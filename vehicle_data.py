import os
from google import genai
import re
import streamlit as st
import pandas as pd
from database_config import create_database_engine, get_database_connection, create_tables, test_database_connection, get_database_info, get_app_config
from sqlalchemy import text
from resolver import GroundedSearchClient, ConsensusResolver, ProvenanceTracker, ResolutionResult
from single_call_resolver import SingleCallVehicleResolver, VehicleSpecificationBundle
import time
import random
import logging

# --- Configuration ---
# Get API key from environment variables (works with Railway, Streamlit Cloud, and local development)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    try:
        # Fallback for Streamlit Cloud or local development
        GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
    except:
        # If secrets are not available, use placeholder
        GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"

if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
    print("⚠️ Warning: GEMINI_API_KEY not set. Please set it in Railway environment variables.")

# Initialize Gemini model once at module level
def initialize_gemini_client():
    """Initialize and return a shared Gemini client instance."""
    if GEMINI_API_KEY != "YOUR_GEMINI_API_KEY":
        return genai.Client(api_key=GEMINI_API_KEY)
    return None

# Create shared client instance
SHARED_GEMINI_CLIENT = initialize_gemini_client()

# Initialize resolver components
def get_resolver_config():
    """Get resolver configuration from database or use defaults."""
    try:
        config = get_app_config() or {}
        grounding_settings = config.get("grounding_settings", {})
        consensus_settings = config.get("consensus_settings", {})
        
        return {
            "clustering_tolerance": grounding_settings.get("clustering_tolerance", 0.15),
            "confidence_threshold": grounding_settings.get("confidence_threshold", 0.7),
            "outlier_threshold": grounding_settings.get("outlier_threshold", 2.0),
            "target_candidates": grounding_settings.get("target_candidates", 3),
            "min_agreement_ratio": consensus_settings.get("min_agreement_ratio", 0.6)
        }
    except Exception as e:
        print(f"Error loading resolver config: {e}")
        return {
            "clustering_tolerance": 0.15,
            "confidence_threshold": 0.7,
            "outlier_threshold": 2.0,
            "target_candidates": 3,
            "min_agreement_ratio": 0.6
        }

# Initialize resolver components
resolver_config = get_resolver_config()
grounded_search_client = GroundedSearchClient()
consensus_resolver = ConsensusResolver(
    clustering_tolerance=resolver_config["clustering_tolerance"],
    confidence_threshold=resolver_config["confidence_threshold"],
    outlier_threshold=resolver_config["outlier_threshold"]
)
provenance_tracker = ProvenanceTracker()

# Initialize single call resolver
single_call_resolver = SingleCallVehicleResolver(
    api_key=GEMINI_API_KEY,
    confidence_threshold=resolver_config["confidence_threshold"]
)

# Define required fields for a complete AI resolution
REQUIRED_FIELDS_FOR_COMPLETE_SEARCH = [
    'curb_weight',
    'aluminum_engine',
    'aluminum_rims',
    'catalytic_converters'
]

def has_complete_resolution(resolution_data):
    """
    Check if resolution data contains all required fields for a complete search.
    
    This function determines completeness by checking the resolutions table for the presence
    of all required fields. This is the correct approach because:
    - The resolutions table stores one row per field (not per search)
    - Completeness is derived by checking if all required fields exist
    - No separate 'is_complete_search' column is needed
    
    Args:
        resolution_data: Dictionary of resolved fields from get_resolution_data_from_db()
                        Format: {field_name: {'value': ..., 'confidence': ..., 'created_at': ...}}
    
    Returns:
        bool: True if all required fields are present with non-None values, False otherwise
    """
    if not resolution_data:
        return False
    
    for field_name in REQUIRED_FIELDS_FOR_COMPLETE_SEARCH:
        if field_name not in resolution_data:
            return False
        
        field_data = resolution_data[field_name]
        if not isinstance(field_data, dict):
            return False
        
        value = field_data.get('value')
        if value is None:
            return False
    
    return True


def retry_with_exponential_backoff(func, max_retries=3, base_delay=1.0, max_delay=10.0, timeout_seconds=30):
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        timeout_seconds: Timeout in seconds (currently not enforced on Windows)
        
    Returns:
        Function result or None if all retries failed
    """
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries:
                print(f"  -> All {max_retries + 1} attempts failed. Last error: {e}")
                return None
            
            # Calculate delay with exponential backoff and jitter
            delay = min(base_delay * (2 ** attempt), max_delay)
            jitter = random.uniform(0, 0.1 * delay)  # Add up to 10% jitter
            total_delay = delay + jitter
            
            print(f"  -> Attempt {attempt + 1} failed: {e}. Retrying in {total_delay:.1f}s...")
            time.sleep(total_delay)
    
    return None

def handle_resolver_error(error, operation, vehicle_key, field_name):
    """
    Handle resolver errors with appropriate logging and fallback strategies.
    
    Args:
        error: The exception that occurred
        operation: Description of the operation that failed
        vehicle_key: Vehicle identifier
        field_name: Field being resolved
        
    Returns:
        None (indicates failure)
    """
    error_msg = f"Resolver error in {operation} for {vehicle_key}.{field_name}: {error}"
    print(f"  -> {error_msg}")
    
    # Log error details for monitoring
    try:
        # In a production system, this would go to a proper logging system
        with open("resolver_errors.log", "a") as log_file:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_file.write(f"[{timestamp}] {error_msg}\n")
    except Exception as log_error:
        print(f"  -> Failed to log error: {log_error}")
    
    return None

def graceful_resolver_fallback(resolver_func, fallback_func, operation, vehicle_key, field_name):
    """
    Attempt resolver-based resolution with graceful fallback to legacy method.
    Implements graceful degradation by trying cached data first, then resolver, then fallback.
    
    Args:
        resolver_func: Primary resolver function to try
        fallback_func: Fallback function if resolver fails
        operation: Description of the operation
        vehicle_key: Vehicle identifier
        field_name: Field being resolved
        
    Returns:
        Resolved value or None
    """
    import logging
    
    try:
        # First, try to get cached resolution data (already checked in resolver_func, but log it)
        logging.debug(f"Attempting {operation} for {vehicle_key}.{field_name}")
        
        # Try resolver approach with retry logic
        result = retry_with_exponential_backoff(resolver_func, max_retries=2)
        if result is not None:
            logging.info(f"Resolver approach succeeded for {operation}")
            return result
        
        logging.warning(f"Resolver approach failed for {operation}, attempting fallback...")
        print(f"  -> Resolver approach failed for {operation}, attempting fallback...")
        
        # Try fallback approach with fewer retries
        fallback_result = retry_with_exponential_backoff(fallback_func, max_retries=1)
        if fallback_result is not None:
            logging.info(f"Fallback approach succeeded for {operation}")
            print(f"  -> Fallback successful for {operation}")
            return fallback_result
        
        # Both approaches failed - try intelligent defaults based on field type
        logging.warning(f"Both resolver and fallback failed for {operation}")
        print(f"  -> Both resolver and fallback failed for {operation}")
        
        # Provide intelligent defaults for critical fields
        if field_name == "aluminum_rims":
            # Default to steel rims for older vehicles, aluminum for newer
            year = int(vehicle_key.split('_')[0]) if '_' in vehicle_key else 2000
            default_value = year >= 2010  # Aluminum rims more common after 2010
            print(f"  -> Using intelligent default: {default_value} (based on vehicle year)")
            return default_value
        elif field_name == "aluminum_engine":
            # Default based on vehicle make/year patterns
            year = int(vehicle_key.split('_')[0]) if '_' in vehicle_key else 2000
            make = vehicle_key.split('_')[1].lower() if '_' in vehicle_key else ""
            # Luxury brands and newer vehicles more likely to have aluminum engines
            luxury_brands = ["bmw", "mercedes", "audi", "lexus", "acura", "infiniti"]
            default_value = year >= 2015 or make in luxury_brands
            print(f"  -> Using intelligent default: {default_value} (based on make/year)")
            return default_value
        
        return None
        
    except Exception as e:
        logging.error(f"Exception in graceful_resolver_fallback for {operation}: {e}")
        return handle_resolver_error(e, operation, vehicle_key, field_name)

# Database setup
print("=== DATABASE SETUP ===")
db_info = get_database_info()
for key, value in db_info.items():
    print(f"{key}: {value}")

# Test database connection
success, message = test_database_connection()
print(f"Database connection: {message}")

if success:
    create_tables()
else:
    print("❌ Database connection failed - check your Railway database configuration")


def backup_database():
    """Creates a backup of the database."""
    # This function will need to be updated to use PostgreSQL
    # For now, it will just print a placeholder message
    print("Backup functionality is not yet implemented for PostgreSQL.")
    return None


def restore_database():
    """Restores the database from backup if it doesn't exist."""
    # This function will need to be updated to use PostgreSQL
    # For now, it will just print a placeholder message
    print("Restore functionality is not yet implemented for PostgreSQL.")
    return False


def export_database_to_json():
    """Exports all vehicle data to JSON for backup purposes."""
    # This function will need to be updated to use PostgreSQL
    # For now, it will just print a placeholder message
    print("Export functionality is not yet implemented for PostgreSQL.")
    return None


def import_database_from_json(json_file):
    """Imports vehicle data from JSON backup."""
    # This function will need to be updated to use PostgreSQL
    # For now, it will just print a placeholder message
    print("Import functionality is not yet implemented for PostgreSQL.")
    return False


def get_curb_weight_from_db(year, make, model):
    """Checks the database for the curb weight of a specific vehicle."""
    import logging
    from database_config import is_sqlite
    
    try:
        engine = create_database_engine()
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT curb_weight_lbs FROM vehicles WHERE year = :year AND make = :make AND model = :model"
            ), {"year": year, "make": make, "model": model})
            row = result.fetchone()
            if row and row[0] is not None:
                return row[0]
    except Exception as e:
        # Enhanced error logging with context
        db_type = "SQLite" if is_sqlite() else "PostgreSQL"
        vehicle_key = f"{year}_{make}_{model}"
        logging.error(f"Database query failed in get_curb_weight_from_db for vehicle_key: {vehicle_key}")
        logging.error(f"Database type: {db_type}")
        logging.error(f"Vehicle: {year} {make} {model}")
        logging.error(f"Field: curb_weight")
        logging.error(f"Error details: {e}")
        print(f"Error getting curb weight from database: {e}")
    return None

def get_vehicle_data_from_db(year, make, model):
    """Checks the database for all vehicle data."""
    import logging
    from database_config import is_sqlite
    
    try:
        engine = create_database_engine()
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT curb_weight_lbs, aluminum_engine, aluminum_rims, catalytic_converters FROM vehicles WHERE year = :year AND make = :make AND model = :model"
            ), {"year": year, "make": make, "model": model})
            row = result.fetchone()
            if row:
                return {
                    'curb_weight_lbs': row[0],
                    'aluminum_engine': row[1],
                    'aluminum_rims': row[2],
                    'catalytic_converters': row[3]
                }
    except Exception as e:
        # Enhanced error logging with context
        db_type = "SQLite" if is_sqlite() else "PostgreSQL"
        vehicle_key = f"{year}_{make}_{model}"
        logging.error(f"Database query failed in get_vehicle_data_from_db for vehicle_key: {vehicle_key}")
        logging.error(f"Database type: {db_type}")
        logging.error(f"Vehicle: {year} {make} {model}")
        logging.error(f"Error details: {e}")
        print(f"Error getting vehicle data from database: {e}")
    return None

def get_resolution_data_from_db(year, make, model):
    """
    Checks the resolutions table for cached resolver data (permanent cache).
    
    Returns all fields for the vehicle regardless of age, using only the most recent
    record for each field. Only returns high-confidence resolutions.
    """
    import logging
    from database_config import is_sqlite
    
    vehicle_key = f"{year}_{make}_{model}"
    
    try:
        engine = create_database_engine()
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT field_name, final_value, confidence_score, created_at 
                FROM resolutions 
                WHERE vehicle_key = :vehicle_key 
                ORDER BY created_at DESC
            """), {"vehicle_key": vehicle_key})
            
            resolution_data = {}
            for row in result.fetchall():
                field_name = row[0]
                final_value = row[1]
                confidence_score = row[2]
                created_at = row[3]
                
                # Only use high-confidence resolutions
                if confidence_score >= resolver_config["confidence_threshold"]:
                    # Only store the first (most recent) record for each field
                    if field_name not in resolution_data:
                        resolution_data[field_name] = {
                            'value': final_value,
                            'confidence': confidence_score,
                            'created_at': created_at
                        }
            
            return resolution_data if resolution_data else None
            
    except Exception as e:
        # Enhanced error logging with context
        db_type = "SQLite" if is_sqlite() else "PostgreSQL"
        logging.error(f"Database query failed in get_resolution_data_from_db for vehicle_key: {vehicle_key}")
        logging.error(f"Database type: {db_type}")
        logging.error(f"Vehicle: {year} {make} {model}")
        logging.error(f"Error details: {e}")
        print(f"Error getting resolution data from database: {e}")
        return None

def update_vehicle_data_in_db(year, make, model, weight, aluminum_engine=None, aluminum_rims=None, catalytic_converters=None, progress_callback=None):
    """Inserts or updates the vehicle data in the database.
    
    Args:
        year: Vehicle year
        make: Vehicle make
        model: Vehicle model
        weight: Curb weight in pounds
        aluminum_engine: Whether engine is aluminum (True/False/None)
        aluminum_rims: Whether rims are aluminum (True/False/None)
        catalytic_converters: Number of catalytic converters (int/None)
        progress_callback: Optional callback function for progress updates
    """
    import logging
    from database_config import is_sqlite
    
    try:
        engine = create_database_engine()
        with engine.connect() as conn:
            if is_sqlite():
                # SQLite syntax - use INSERT OR REPLACE
                conn.execute(text("""
                    INSERT OR REPLACE INTO vehicles (year, make, model, curb_weight_lbs, aluminum_engine, aluminum_rims, catalytic_converters)
                    VALUES (:year, :make, :model, :weight, :aluminum_engine, :aluminum_rims, :catalytic_converters)
                """), {
                    "year": year, 
                    "make": make, 
                    "model": model, 
                    "weight": weight, 
                    "aluminum_engine": aluminum_engine, 
                    "aluminum_rims": aluminum_rims,
                    "catalytic_converters": catalytic_converters
                })
            else:
                # PostgreSQL syntax
                conn.execute(text("""
                    INSERT INTO vehicles (year, make, model, curb_weight_lbs, aluminum_engine, aluminum_rims, catalytic_converters)
                    VALUES (:year, :make, :model, :weight, :aluminum_engine, :aluminum_rims, :catalytic_converters)
                    ON CONFLICT (year, make, model) DO UPDATE SET 
                        curb_weight_lbs = EXCLUDED.curb_weight_lbs,
                        aluminum_engine = EXCLUDED.aluminum_engine,
                        aluminum_rims = EXCLUDED.aluminum_rims,
                        catalytic_converters = EXCLUDED.catalytic_converters
                """), {
                    "year": year, 
                    "make": make, 
                    "model": model, 
                    "weight": weight, 
                    "aluminum_engine": aluminum_engine, 
                    "aluminum_rims": aluminum_rims,
                    "catalytic_converters": catalytic_converters
                })
            conn.commit()
            db_type = "SQLite" if is_sqlite() else "PostgreSQL"
            print(f"✅ Vehicle data updated in {db_type} database: {year} {make} {model}")
    except Exception as e:
        # Enhanced error logging with context
        db_type = "SQLite" if is_sqlite() else "PostgreSQL"
        vehicle_key = f"{year}_{make}_{model}"
        logging.error(f"Database update failed in update_vehicle_data_in_db for vehicle_key: {vehicle_key}")
        logging.error(f"Database type: {db_type}")
        logging.error(f"Vehicle: {year} {make} {model}")
        logging.error(f"Data: weight={weight}, aluminum_engine={aluminum_engine}, aluminum_rims={aluminum_rims}, catalytic_converters={catalytic_converters}")
        logging.error(f"Error details: {e}")
        print(f"Error updating vehicle data in database: {e}")

def mark_vehicle_as_not_found(year, make, model):
    """Stores fake/not found vehicles in session state to prevent repeated validation attempts during the session."""
    # Instead of storing in database, we'll use session state or in-memory cache
    if 'fake_vehicles' not in st.session_state:
        st.session_state['fake_vehicles'] = set()
    
    vehicle_key = f"{year}_{make}_{model}"
    st.session_state['fake_vehicles'].add(vehicle_key)
    print(f"✅ Marked vehicle as not found in session: {year} {make} {model}")

def is_vehicle_marked_as_fake(year, make, model):
    """Checks if a vehicle was previously marked as fake in this session."""
    if 'fake_vehicles' not in st.session_state:
        return False
    
    vehicle_key = f"{year}_{make}_{model}"
    return vehicle_key in st.session_state['fake_vehicles']

def get_last_ten_entries():
    """Fetches the last 10 vehicle entries from the database."""
    try:
        engine = create_database_engine()
        query = text("SELECT year, make, model, curb_weight_lbs, aluminum_engine, aluminum_rims, catalytic_converters FROM vehicles ORDER BY id DESC LIMIT 10")
        df = pd.read_sql_query(query, engine)
        return df
    except Exception as e:
        print(f"Database error: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error


def validate_vehicle_existence(year: int, make: str, model: str):
    """
    Validates if a vehicle actually exists using Gemini API grounded with Google Search.
    Returns True if vehicle exists, False if fake/non-existent, or None for inconclusive.
    """
    import logging
    
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        logging.warning("Google AI API key not configured for vehicle validation")
        logging.warning("Please set GEMINI_API_KEY environment variable")
        print("Please set your actual GEMINI_API_KEY in vehicle_data.py.")
        return None

    if SHARED_GEMINI_CLIENT is None:
        logging.error("Gemini client not initialized for vehicle validation")
        logging.error("Client initialization may have failed - check API key and SDK installation")
        print("Gemini client not initialized. Please check your API key.")
        return None

    try:
        vehicle_string = f"{year} {make} {model}"
        logging.info(f"Validating vehicle existence via Google AI: {vehicle_string}")
        
        prompt = (
            f"Search the web to verify if the {year} {make} {model} is a real vehicle that was actually manufactured. "
            "Look for official manufacturer information, automotive databases like Edmunds, KBB, or manufacturer websites, reviews, or dealership listings. "
            f"Specifically check if '{make}' is a legitimate automotive manufacturer and if the model '{model}' was actually produced in {year}. "
            "Be strict - if the manufacturer doesn't exist (like 'FakeMake') or if the model was never made in that year, return 'fake'. "
            "Return ONLY one of these exact values: 'exists', 'fake', or 'inconclusive'. "
            "Do not include any other text or explanation."
        )
        
        response = SHARED_GEMINI_CLIENT.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={
                "tools": [{"google_search": {}}]
            }
        )
        
        text_response = response.text.strip().lower()
        
        if text_response == 'exists':
            logging.info(f"Vehicle validation successful: {vehicle_string} exists")
            return True
        elif text_response == 'fake':
            logging.info(f"Vehicle validation result: {vehicle_string} is fake/non-existent")
            return False
        elif text_response == 'inconclusive':
            logging.warning(f"Vehicle validation inconclusive for: {vehicle_string}")
            return None
        else:
            logging.warning(f"Unexpected validation response for {vehicle_string}: {text_response}")
            return None

    except Exception as e:
        # Enhanced error logging with context
        vehicle_string = f"{year} {make} {model}"
        logging.error(f"Google AI API call failed during vehicle validation")
        logging.error(f"Vehicle: {vehicle_string}")
        logging.error(f"Error type: {type(e).__name__}")
        logging.error(f"Error details: {e}")
        
        # Provide user-friendly error messages for common failures
        error_str = str(e)
        if "404" in error_str and "not found" in error_str:
            logging.error("Model not found error - the specified model may be deprecated or unavailable")
            print(f"Error: Google AI model not found. Please check model configuration.")
        elif "401" in error_str or "403" in error_str:
            logging.error("Authentication error - API key may be invalid or expired")
            print(f"Error: Google AI authentication failed. Please check your API key.")
        elif "429" in error_str:
            logging.error("Rate limit exceeded - too many API requests")
            print(f"Error: Google AI rate limit exceeded. Please try again later.")
        else:
            print(f"An error occurred during the vehicle validation API call: {e}")
        
        return None


def get_aluminum_engine_from_resolver(year: int, make: str, model: str):
    """
    Returns whether the vehicle has an aluminum engine using the resolver system.
    Returns True for aluminum engine, False for iron engine, or None for inconclusive.
    """
    vehicle_key = f"{year}_{make}_{model}"
    
    # Check for cached resolution first
    try:
        cached_result = provenance_tracker.get_cached_resolution(vehicle_key, "aluminum_engine")
        if cached_result and cached_result.confidence_score >= resolver_config["confidence_threshold"]:
            print(f"  -> Using cached aluminum engine resolution: {bool(cached_result.final_value)} (confidence: {cached_result.confidence_score:.2f})")
            return bool(cached_result.final_value) if cached_result.final_value is not None else None
    except Exception as e:
        print(f"  -> Cache lookup failed: {e}")
    
    def resolver_operation():
        # Use grounded search to get multiple candidates
        candidates = grounded_search_client.search_vehicle_specs(year, make, model, "aluminum_engine")
        
        if not candidates:
            print(f"  -> No candidates found for aluminum engine via grounded search")
            return None
        
        print(f"  -> Found {len(candidates)} aluminum engine candidates via grounded search")
        
        # Use consensus resolver to get final value
        resolution_result = consensus_resolver.resolve_field(candidates)
        
        # Store resolution with provenance (with error handling)
        try:
            record_id = provenance_tracker.create_resolution_record(vehicle_key, "aluminum_engine", resolution_result)
        except Exception as e:
            print(f"  -> Failed to store resolution record: {e}")
        
        # Convert numeric result to boolean
        final_value = None
        if resolution_result.final_value is not None:
            final_value = bool(resolution_result.final_value)
        
        # Log resolution details
        print(f"  -> Resolved aluminum engine: {final_value}")
        print(f"  -> Confidence score: {resolution_result.confidence_score:.2f}")
        print(f"  -> Method: {resolution_result.method}")
        
        if resolution_result.warnings:
            for warning in resolution_result.warnings:
                print(f"  -> Warning: {warning}")
        
        return final_value
    
    try:
        return retry_with_exponential_backoff(resolver_operation, max_retries=2)
    except Exception as e:
        return handle_resolver_error(e, "aluminum engine resolution", vehicle_key, "aluminum_engine")

def get_aluminum_engine_from_api(year: int, make: str, model: str, progress_callback=None):
    """
    Enhanced function - uses SingleCallVehicleResolver as primary method with graceful fallback to multi-call resolver.
    
    Args:
        year: Vehicle year
        make: Vehicle make
        model: Vehicle model
        progress_callback: Optional callback function for progress updates
    """
    vehicle_key = f"{year}_{make}_{model}"
    
    def single_call_approach():
        """Try single-call resolution first."""
        single_call_result = single_call_resolver.resolve_all_specifications(year, make, model)
        if (single_call_result and 
            single_call_result.aluminum_engine is not None and
            single_call_result.confidence_scores.get('engine_material', 0.0) >= resolver_config["confidence_threshold"]):
            return single_call_result.aluminum_engine
        return None
    
    def resolver_approach():
        return get_aluminum_engine_from_resolver(year, make, model)
    
    def fallback_approach():
        if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
            print("Please set your actual GEMINI_API_KEY in vehicle_data.py.")
            return None

        if SHARED_GEMINI_CLIENT is None:
            print("Gemini client not initialized. Please check your API key.")
            return None

        prompt = (
            f"Search the web to determine if the {year} {make} {model} has an aluminum engine block or iron engine block. "
            "Search for engine specifications, materials, and construction details. "
            "Return ONLY one of these exact values: 'aluminum', 'iron', or 'inconclusive'. "
            "Do not include any other text or explanation."
        )
        
        response = SHARED_GEMINI_CLIENT.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={
                "tools": [{"google_search": {}}]
            }
        )
        
        text_response = response.text.strip().lower()
        
        if text_response == 'aluminum':
            return True
        elif text_response == 'iron':
            return False
        elif text_response == 'inconclusive':
            return None
        else:
            return None
    
    # Try single-call approach first
    try:
        result = single_call_approach()
        if result is not None:
            print(f"  -> Single-call aluminum engine resolution successful: {result}")
            return result
    except Exception as e:
        print(f"  -> Single-call approach failed: {e}")
    
    # Fallback to existing multi-call resolver approach
    return graceful_resolver_fallback(
        resolver_approach, 
        fallback_approach, 
        "aluminum engine resolution", 
        vehicle_key, 
        "aluminum_engine"
    )


def get_aluminum_rims_from_resolver(year: int, make: str, model: str):
    """
    Returns whether the vehicle has aluminum rims using the resolver system.
    Returns True for aluminum rims, False for steel rims, or None for inconclusive.
    """
    vehicle_key = f"{year}_{make}_{model}"
    
    # Check for cached resolution first
    try:
        cached_result = provenance_tracker.get_cached_resolution(vehicle_key, "aluminum_rims")
        if cached_result and cached_result.confidence_score >= resolver_config["confidence_threshold"]:
            print(f"  -> Using cached aluminum rims resolution: {bool(cached_result.final_value)} (confidence: {cached_result.confidence_score:.2f})")
            return bool(cached_result.final_value) if cached_result.final_value is not None else None
    except Exception as e:
        print(f"  -> Cache lookup failed: {e}")
    
    def resolver_operation():
        # Use grounded search to get multiple candidates
        candidates = grounded_search_client.search_vehicle_specs(year, make, model, "aluminum_rims")
        
        if not candidates:
            print(f"  -> No candidates found for aluminum rims via grounded search")
            return None
        
        print(f"  -> Found {len(candidates)} aluminum rims candidates via grounded search")
        
        # Use consensus resolver to get final value
        resolution_result = consensus_resolver.resolve_field(candidates)
        
        # Store resolution with provenance (with error handling)
        try:
            record_id = provenance_tracker.create_resolution_record(vehicle_key, "aluminum_rims", resolution_result)
        except Exception as e:
            print(f"  -> Failed to store resolution record: {e}")
        
        # Convert numeric result to boolean
        final_value = None
        if resolution_result.final_value is not None:
            final_value = bool(resolution_result.final_value)
        
        # Log resolution details
        print(f"  -> Resolved aluminum rims: {final_value}")
        print(f"  -> Confidence score: {resolution_result.confidence_score:.2f}")
        print(f"  -> Method: {resolution_result.method}")
        
        if resolution_result.warnings:
            for warning in resolution_result.warnings:
                print(f"  -> Warning: {warning}")
        
        return final_value
    
    try:
        return retry_with_exponential_backoff(resolver_operation, max_retries=2)
    except Exception as e:
        return handle_resolver_error(e, "aluminum rims resolution", vehicle_key, "aluminum_rims")

def get_aluminum_rims_from_api(year: int, make: str, model: str, progress_callback=None):
    """
    Enhanced function - uses SingleCallVehicleResolver as primary method with graceful fallback to multi-call resolver.
    
    Args:
        year: Vehicle year
        make: Vehicle make
        model: Vehicle model
        progress_callback: Optional callback function for progress updates
    """
    vehicle_key = f"{year}_{make}_{model}"
    
    def single_call_approach():
        """Try single-call resolution first."""
        single_call_result = single_call_resolver.resolve_all_specifications(year, make, model)
        if (single_call_result and 
            single_call_result.aluminum_rims is not None and
            single_call_result.confidence_scores.get('rim_material', 0.0) >= resolver_config["confidence_threshold"]):
            return single_call_result.aluminum_rims
        return None
    
    def resolver_approach():
        return get_aluminum_rims_from_resolver(year, make, model)
    
    def fallback_approach():
        if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
            print("Please set your actual GEMINI_API_KEY in vehicle_data.py.")
            return None

        if SHARED_GEMINI_CLIENT is None:
            print("Gemini client not initialized. Please check your API key.")
            return None

        prompt = (
            f"Search the web to determine if the {year} {make} {model} has aluminum wheels/rims or steel wheels/rims. "
            "Search for wheel specifications, materials, and construction details. "
            "Return ONLY one of these exact values: 'aluminum', 'steel', or 'inconclusive'. "
            "Do not include any other text or explanation."
        )
        
        response = SHARED_GEMINI_CLIENT.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={
                "tools": [{"google_search": {}}]
            }
        )
        
        text_response = response.text.strip().lower()
        
        if text_response == 'aluminum':
            return True
        elif text_response == 'steel':
            return False
        elif text_response == 'inconclusive':
            return None
        else:
            return None
    
    # Try single-call approach first
    try:
        result = single_call_approach()
        if result is not None:
            print(f"  -> Single-call aluminum rims resolution successful: {result}")
            return result
    except Exception as e:
        print(f"  -> Single-call approach failed: {e}")
    
    # Fallback to existing multi-call resolver approach
    return graceful_resolver_fallback(
        resolver_approach, 
        fallback_approach, 
        "aluminum rims resolution", 
        vehicle_key, 
        "aluminum_rims"
    )


def get_curb_weight_from_resolver(year: int, make: str, model: str):
    """
    Returns curb weight in pounds using the resolver system with consensus-based resolution.
    Includes caching, provenance tracking, and enhanced error handling.
    """
    vehicle_key = f"{year}_{make}_{model}"
    
    # Check for cached resolution first
    try:
        cached_result = provenance_tracker.get_cached_resolution(vehicle_key, "curb_weight")
        if cached_result and cached_result.confidence_score >= resolver_config["confidence_threshold"]:
            print(f"  -> Using cached curb weight resolution: {cached_result.final_value} lbs (confidence: {cached_result.confidence_score:.2f})")
            return cached_result.final_value
    except Exception as e:
        print(f"  -> Cache lookup failed: {e}")
    
    def resolver_operation():
        # Use grounded search to get multiple candidates
        candidates = grounded_search_client.search_vehicle_specs(year, make, model, "curb_weight")
        
        if not candidates:
            print(f"  -> No candidates found for curb weight via grounded search")
            return None
        
        print(f"  -> Found {len(candidates)} curb weight candidates via grounded search")
        
        # Use consensus resolver to get final value
        resolution_result = consensus_resolver.resolve_field(candidates)
        
        # Store resolution with provenance (with error handling)
        try:
            record_id = provenance_tracker.create_resolution_record(vehicle_key, "curb_weight", resolution_result)
        except Exception as e:
            print(f"  -> Failed to store resolution record: {e}")
        
        # Log resolution details
        print(f"  -> Resolved curb weight: {resolution_result.final_value} lbs")
        print(f"  -> Confidence score: {resolution_result.confidence_score:.2f}")
        print(f"  -> Method: {resolution_result.method}")
        
        if resolution_result.warnings:
            for warning in resolution_result.warnings:
                print(f"  -> Warning: {warning}")
        
        # Return the resolved value
        return resolution_result.final_value
    
    try:
        return retry_with_exponential_backoff(resolver_operation, max_retries=2)
    except Exception as e:
        return handle_resolver_error(e, "curb weight resolution", vehicle_key, "curb_weight")

def get_curb_weight_from_api(year: int, make: str, model: str, progress_callback=None):
    """
    Enhanced function - uses SingleCallVehicleResolver as primary method with graceful fallback to multi-call resolver.
    
    Args:
        year: Vehicle year
        make: Vehicle make
        model: Vehicle model
        progress_callback: Optional callback function for progress updates
    """
    vehicle_key = f"{year}_{make}_{model}"
    
    def single_call_approach():
        """Try single-call resolution first."""
        single_call_result = single_call_resolver.resolve_all_specifications(year, make, model)
        if (single_call_result and 
            single_call_result.curb_weight_lbs is not None and
            single_call_result.confidence_scores.get('curb_weight', 0.0) >= resolver_config["confidence_threshold"]):
            return single_call_result.curb_weight_lbs
        return None
    
    def resolver_approach():
        return get_curb_weight_from_resolver(year, make, model)
    
    def fallback_approach():
        if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
            print("Please set your actual GEMINI_API_KEY in vehicle_data.py.")
            return None

        if SHARED_GEMINI_CLIENT is None:
            print("Gemini client not initialized. Please check your API key.")
            return None

        # Step 1: Gather candidate weights with preferred sources
        gather_prompt = (
            f"Search the web and list every curb-weight figure (in pounds) you find for a {year} {make} {model}. "
            "Prioritise results from Kelley Blue Book (kbb.com), Edmunds (edmunds.com) or the manufacturer's official site. "
            "Return one line per finding in the exact format '<WEIGHT> <source>'. Only include numbers; omit commentary."
        )

        gather_resp = SHARED_GEMINI_CLIENT.models.generate_content(
            model='gemini-2.5-flash',
            contents=gather_prompt,
            config={
                "tools": [{"google_search": {}}]
            }
        )

        candidate_numbers = [int(m) for m in re.findall(r"(?m)^(\d{3,5})", gather_resp.text)]
        
        if not candidate_numbers:
            return None

        # If only one weight found, use it
        if len(candidate_numbers) == 1:
            return candidate_numbers[0]

        # If multiple weights found, use a second API call to interpret
        if len(candidate_numbers) > 1:
            # Step 2: Use AI to interpret the best weight from candidates
            interpret_prompt = (
                f"Based on the curb weight candidates for a {year} {make} {model}: {candidate_numbers}, "
                "determine the most likely accurate curb weight in pounds. "
                "Consider typical weight ranges for this vehicle type and year, and in cases with several viable figures for curb weight, choose the lower number. "
                "Return ONLY the weight number, no other text."
            )

            interpret_resp = SHARED_GEMINI_CLIENT.models.generate_content(
                model='gemini-2.5-flash',
                contents=interpret_prompt,
                config={
                    "tools": [{"google_search": {}}]
                }
            )

            # Extract the interpreted weight
            interpreted_weight_match = re.search(r'(\d{3,5})', interpret_resp.text)
            if interpreted_weight_match:
                interpreted_weight = int(interpreted_weight_match.group(1))
                return interpreted_weight
            else:
                # Fallback to most common weight
                from collections import Counter
                counts = Counter(candidate_numbers)
                most_common_weight, freq = counts.most_common(1)[0]
                return most_common_weight

        return None
    
    # Try single-call approach first
    try:
        result = single_call_approach()
        if result is not None:
            print(f"  -> Single-call curb weight resolution successful: {result} lbs")
            return result
    except Exception as e:
        print(f"  -> Single-call approach failed: {e}")
    
    # Fallback to existing multi-call resolver approach
    return graceful_resolver_fallback(
        resolver_approach, 
        fallback_approach, 
        "curb weight resolution", 
        vehicle_key, 
        "curb_weight"
    )

def heuristic_rule(year, make, model):
    """Fallback heuristic for catalytic converter count."""
    # Performance vehicle heuristics
    model = model.lower()
    make = make.lower()
    
    # Performance trims that typically have dual exhaust (4 cats)
    performance_indicators = ['gt', 'rs', 'ss', 'amg', 'type r', 'm3', 'm4', 'm5', 'v8']
    if any(indicator in model.lower() for indicator in performance_indicators):
        print(f"  -> Heuristic: Performance model detected ({model}), assuming 4 catalytic converters")
        return 4
        
    # V8 models typically have 4 cats (2 per bank)
    if 'v8' in model.lower() or '5.0' in model.lower() or '6.2' in model.lower():
        print(f"  -> Heuristic: V8 engine detected, assuming 4 catalytic converters")
        return 4
        
    # Default fallback
    print(f"  -> Heuristic: No special cases detected, defaulting to 1 catalytic converter")
    return 1

def get_catalytic_converter_count_from_api(year: int, make: str, model: str):
    """
    Enhanced function - uses SingleCallVehicleResolver as primary method with graceful fallback to existing API approach.
    """
    print(f"\n  -> Searching for catalytic converter count for {year} {make} {model}...")
    
    # Try single-call approach first
    try:
        single_call_result = single_call_resolver.resolve_all_specifications(year, make, model)
        if (single_call_result and 
            single_call_result.catalytic_converters is not None and
            single_call_result.confidence_scores.get('catalytic_converters', 0.0) >= resolver_config["confidence_threshold"]):
            print(f"  -> Single-call catalytic converter resolution successful: {single_call_result.catalytic_converters}")
            return single_call_result.catalytic_converters
    except Exception as e:
        print(f"  -> Single-call approach failed: {e}")
    
    # Fallback to existing API approach
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        print("Please set your actual GEMINI_API_KEY in vehicle_data.py.")
        return None

    if SHARED_GEMINI_CLIENT is None:
        print("Gemini client not initialized. Please check your API key.")
        return None

    # Single consolidated search approach
    try:
        prompt = f"""
        Search the web for information about {year} {make} {model} catalytic converter count and configuration.
        Look for parts catalog information, exhaust system diagrams, and technical specifications.
        
        Count UNIQUE catalytic converter positions and return ONLY a number:
        1. Look for terms like: Bank 1, Bank 2, Left Bank, Right Bank, Front, Rear, Manifold
        2. For dual exhaust systems, typically there are 2 cats per bank (pre-cat near engine, main cat further down)
        3. V6/V8 engines often have 2 banks (left/right) with 2 cats each
        4. Performance/sports models often have dual exhaust with 4 total cats
        
        Return ONLY a number (1, 2, 3, 4, etc.) representing the total count of catalytic converters.
        If nothing definitive is found, return -1.
        
        Return ONLY the number, no other text.
        """
        print(f"\n  -> Searching for catalytic converter count...")
        
        response = SHARED_GEMINI_CLIENT.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={
                "tools": [{"google_search": {}}]
            }
        )
        
        # Extract the count from the response
        response_text = response.text.strip()
        print(f"     API response: '{response_text}'")
        
        # Parse the numeric response
        count_match = re.search(r'^(-?\d+)', response_text)
        if count_match:
            count = int(count_match.group(1))
            if count > 0:
                print(f"     Found {count} catalytic converters via API")
                return count
            else:
                print(f"     No definitive converter count found via API")
        else:
            print(f"     Could not parse count from response: {response_text}")

    except Exception as e:
        print(f"An error occurred during the API call: {e}")
        print(f"Exception type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

    print("  -> All API calls failed, falling back to heuristic")
    return heuristic_rule(year, make, model)




def process_vehicle(year, make, model, progress_callback=None):
    """
    Main logic to get vehicle data using the resolver system with fallback to database and API.
    Integrates consensus-based resolution with caching and provenance tracking.
    
    Args:
        year: Vehicle year
        make: Vehicle make
        model: Vehicle model
        progress_callback: Optional callback function for progress updates
                          Should accept (phase: str, spec_name: str, status: str) parameters
    
    Graceful degradation strategy:
    1. Try cached high-confidence resolver data first
    2. Fall back to database vehicle data
    3. Validate vehicle existence before expensive API calls
    4. Try resolver-based queries with retry logic
    5. Only mark as fake if validation explicitly fails (not inconclusive)
    """
    import logging
    
    print(f"Processing: {year} {make} {model}")
    logging.info(f"Starting vehicle processing for {year} {make} {model}")
    
    # Helper function to safely call progress callback
    def update_progress(phase, spec_name=None, status=None, confidence=None, error_message=None):
        if progress_callback:
            try:
                progress_callback(phase, spec_name, status, confidence, error_message)
            except Exception as e:
                print(f"  -> Progress callback error: {e}")
    
    # Initial progress update
    update_progress("Initializing search...", None, None)
    
    # Check if this vehicle was previously marked as fake in this session
    if is_vehicle_marked_as_fake(year, make, model):
        print(f"  -> Vehicle previously marked as fake in session: {year} {make} {model}")
        logging.info(f"Vehicle {year} {make} {model} previously marked as fake - skipping")
        update_progress("Search complete", None, None)
        return None
    
    # Check for COMPLETE high-confidence resolver data (cached data first)
    update_progress("Checking cached data...", None, None)
    resolution_data = get_resolution_data_from_db(year, make, model)
    
    # Only use cache if we have ALL required fields (complete resolution)
    if resolution_data and has_complete_resolution(resolution_data):
        print(f"  -> Found complete cached AI resolution for all fields")
        logging.info(f"Using complete cached resolver data for {year} {make} {model}")
        
        # Extract resolved values
        curb_weight = resolution_data.get('curb_weight', {}).get('value')
        aluminum_engine = resolution_data.get('aluminum_engine', {}).get('value')
        aluminum_rims = resolution_data.get('aluminum_rims', {}).get('value')
        catalytic_converters = resolution_data.get('catalytic_converters', {}).get('value')
        
        # Update progress for cached complete data
        update_progress("Using cached AI search...", "curb_weight", "found")
        update_progress("Using cached AI search...", "engine_material", "found")
        update_progress("Using cached AI search...", "rim_material", "found")
        update_progress("Using cached AI search...", "catalytic_converters", "found")
        
        # Convert boolean values from numeric storage
        if aluminum_engine is not None:
            aluminum_engine = bool(aluminum_engine)
        if aluminum_rims is not None:
            aluminum_rims = bool(aluminum_rims)
        
        print(f"  -> Using complete cached AI data: {curb_weight} lbs, Al Engine: {aluminum_engine}, Al Rims: {aluminum_rims}, Cats: {catalytic_converters}")
        logging.info(f"Successfully returned complete cached data for {year} {make} {model}")
        update_progress("Search complete", None, None)
        return {
            'curb_weight_lbs': curb_weight,
            'aluminum_engine': aluminum_engine,
            'aluminum_rims': aluminum_rims,
            'catalytic_converters': catalytic_converters
        }
    elif resolution_data:
        # Partial data exists but not complete - log and proceed with new AI search
        missing_fields = [f for f in REQUIRED_FIELDS_FOR_COMPLETE_SEARCH if f not in resolution_data or resolution_data[f].get('value') is None]
        print(f"  -> Found partial cached data but missing fields: {missing_fields}")
        print(f"  -> Will run new AI search for complete resolution")
        logging.info(f"Incomplete cached data for {year} {make} {model}, missing: {missing_fields}")
    
    # No complete cached data - proceed with AI search
    # (vehicles table is NOT used as cache - only resolutions table with complete data)
    print("  -> No complete cached AI data. Validating vehicle existence first...")
    
    # Validate vehicle existence before making expensive resolver calls
    update_progress("Validating vehicle...", None, None)
    vehicle_exists = validate_vehicle_existence(year, make, model)
    
    if vehicle_exists is False:
        # Only mark as not found if validation explicitly returned False
        print(f"  -> Vehicle validation failed: {year} {make} {model} does not exist")
        mark_vehicle_as_not_found(year, make, model)
        update_progress("Search complete", None, None)
        return None  # Return None to indicate vehicle not found
    elif vehicle_exists is None:
        print(f"  -> Vehicle validation inconclusive for: {year} {make} {model}")
        print(f"  -> Will attempt resolution but won't mark as fake if unsuccessful")
        # Continue with processing - inconclusive doesn't mean fake
    else:
        print(f"  -> Vehicle validation passed: {year} {make} {model} exists")
    
    print("  -> Proceeding with single-call resolution...")
    
    # Try single-call resolution first - always run for new searches
    update_progress("Running new AI search...", None, "searching")
    single_call_result = single_call_resolver.resolve_all_specifications(year, make, model)
    
    # Check if single-call resolution was successful
    if (single_call_result and 
        single_call_result.curb_weight_lbs is not None and 
        single_call_resolver.has_sufficient_confidence(single_call_result)):
        
        print(f"  -> Single-call resolution successful!")
        print(f"  -> Weight: {single_call_result.curb_weight_lbs} lbs")
        print(f"  -> Aluminum Engine: {single_call_result.aluminum_engine}")
        print(f"  -> Aluminum Rims: {single_call_result.aluminum_rims}")
        print(f"  -> Catalytic Converters: {single_call_result.catalytic_converters}")
        
        # Update progress for all found specifications
        if single_call_result.curb_weight_lbs is not None:
            confidence = single_call_result.confidence_scores.get('curb_weight', 0.8)
            update_progress("Searching specifications...", "curb_weight", "found", confidence)
        
        if single_call_result.aluminum_engine is not None:
            confidence = single_call_result.confidence_scores.get('engine_material', 0.7)
            update_progress("Searching specifications...", "engine_material", "found", confidence)
        
        if single_call_result.aluminum_rims is not None:
            confidence = single_call_result.confidence_scores.get('rim_material', 0.7)
            update_progress("Searching specifications...", "rim_material", "found", confidence)
        
        if single_call_result.catalytic_converters is not None:
            confidence = single_call_result.confidence_scores.get('catalytic_converters', 0.6)
            update_progress("Searching specifications...", "catalytic_converters", "found", confidence)
        
        # Store single-call resolution results in provenance tracker
        try:
            vehicle_key = f"{year}_{make}_{model}"
            
            # Create resolution records for each field
            if single_call_result.curb_weight_lbs is not None:
                from resolver import ResolutionResult
                weight_resolution = ResolutionResult(
                    final_value=single_call_result.curb_weight_lbs,
                    confidence_score=single_call_result.confidence_scores.get('curb_weight', 0.8),
                    method="single_call_resolution",
                    candidates=[],  # Single call doesn't use candidates
                    outliers=[],    # Single call doesn't use outliers
                    warnings=single_call_result.warnings
                )
                provenance_tracker.create_resolution_record(vehicle_key, "curb_weight", weight_resolution)
            
            if single_call_result.aluminum_engine is not None:
                engine_resolution = ResolutionResult(
                    final_value=int(single_call_result.aluminum_engine),
                    confidence_score=single_call_result.confidence_scores.get('engine_material', 0.7),
                    method="single_call_resolution",
                    candidates=[],  # Single call doesn't use candidates
                    outliers=[],    # Single call doesn't use outliers
                    warnings=single_call_result.warnings
                )
                provenance_tracker.create_resolution_record(vehicle_key, "aluminum_engine", engine_resolution)
            
            if single_call_result.aluminum_rims is not None:
                rims_resolution = ResolutionResult(
                    final_value=int(single_call_result.aluminum_rims),
                    confidence_score=single_call_result.confidence_scores.get('rim_material', 0.7),
                    method="single_call_resolution",
                    candidates=[],  # Single call doesn't use candidates
                    outliers=[],    # Single call doesn't use outliers
                    warnings=single_call_result.warnings
                )
                provenance_tracker.create_resolution_record(vehicle_key, "aluminum_rims", rims_resolution)
            
            if single_call_result.catalytic_converters is not None:
                cat_resolution = ResolutionResult(
                    final_value=single_call_result.catalytic_converters,
                    confidence_score=single_call_result.confidence_scores.get('catalytic_converters', 0.6),
                    method="single_call_resolution",
                    candidates=[],  # Single call doesn't use candidates
                    outliers=[],    # Single call doesn't use outliers
                    warnings=single_call_result.warnings
                )
                provenance_tracker.create_resolution_record(vehicle_key, "catalytic_converters", cat_resolution)
            
            # Check completeness of resolution and log if incomplete
            resolved_fields = []
            missing_fields = []
            
            for field_name in REQUIRED_FIELDS_FOR_COMPLETE_SEARCH:
                if field_name == 'curb_weight' and single_call_result.curb_weight_lbs is not None:
                    resolved_fields.append(field_name)
                elif field_name == 'aluminum_engine' and single_call_result.aluminum_engine is not None:
                    resolved_fields.append(field_name)
                elif field_name == 'aluminum_rims' and single_call_result.aluminum_rims is not None:
                    resolved_fields.append(field_name)
                elif field_name == 'catalytic_converters' and single_call_result.catalytic_converters is not None:
                    resolved_fields.append(field_name)
                else:
                    missing_fields.append(field_name)
            
            if missing_fields:
                print(f"  -> WARNING: Incomplete resolution - missing fields: {missing_fields}")
                logging.warning(f"Incomplete AI resolution for {vehicle_key}: resolved {resolved_fields}, missing {missing_fields}")
            else:
                print(f"  -> Complete resolution achieved - all required fields resolved")
                logging.info(f"Complete AI resolution for {vehicle_key}: all fields resolved")
                
        except Exception as e:
            print(f"  -> Warning: Failed to store single-call resolution records: {e}")
        
        # Update database with single-call results
        update_progress("Saving to database...", None, None)
        update_vehicle_data_in_db(
            year, make, model, 
            single_call_result.curb_weight_lbs,
            single_call_result.aluminum_engine,
            single_call_result.aluminum_rims,
            single_call_result.catalytic_converters,
            progress_callback
        )
        
        update_progress("Search complete", None, None)
        return {
            'curb_weight_lbs': single_call_result.curb_weight_lbs,
            'aluminum_engine': single_call_result.aluminum_engine,
            'aluminum_rims': single_call_result.aluminum_rims,
            'catalytic_converters': single_call_result.catalytic_converters
        }
    
    else:
        # Single-call resolution failed or insufficient confidence, fallback to multi-call system
        print("  -> Single-call resolution failed or insufficient confidence, falling back to multi-call system...")
        if single_call_result and single_call_result.warnings:
            for warning in single_call_result.warnings:
                print(f"  -> Single-call warning: {warning}")
        
        # Use existing multi-call resolver system for curb weight
        update_progress("Searching specifications...", "curb_weight", "searching")
        weight = get_curb_weight_from_api(year, make, model, progress_callback)  # This uses existing resolver internally
        if weight:
            print(f"  -> Resolved curb weight: {weight} lbs")
            # Try to get confidence score from resolver data if available
            confidence = 0.8  # Default confidence for successful resolution
            if resolution_data and 'curb_weight' in resolution_data:
                confidence = resolution_data['curb_weight'].get('confidence', 0.8)
            update_progress("Searching specifications...", "curb_weight", "found", confidence)
        else:
            error_msg = "Unable to find reliable curb weight data"
            update_progress("Searching specifications...", "curb_weight", "failed", None, error_msg)
        
        # Graceful degradation: Only mark as fake if validation explicitly failed
        # Don't mark as fake just because we couldn't resolve data
        if not weight:
            if vehicle_exists is False:
                # Already handled above, but double-check
                print(f"  -> No weight found and vehicle explicitly validated as fake")
                mark_vehicle_as_not_found(year, make, model)
                update_progress("Search complete", None, None)
                return None
            else:
                # Validation was inconclusive or passed - don't mark as fake
                print(f"  -> Could not resolve weight, but validation was not conclusive")
                print(f"  -> Not marking vehicle as fake - may need manual review or retry later")
                # Provide specific error message for weight resolution failure
                error_msg = "Weight data not available from reliable sources"
                update_progress("Search complete", "curb_weight", "failed", None, error_msg)
                return None
        
        # Use existing multi-call resolver system for aluminum engine info
        update_progress("Searching specifications...", "engine_material", "searching")
        aluminum_engine = get_aluminum_engine_from_api(year, make, model, progress_callback)  # This uses existing resolver internally
        if aluminum_engine is not None:
            print(f"  -> Resolved aluminum engine: {aluminum_engine}")
            # Try to get confidence score from resolver data if available
            confidence = 0.7  # Default confidence for successful resolution
            if resolution_data and 'aluminum_engine' in resolution_data:
                confidence = resolution_data['aluminum_engine'].get('confidence', 0.7)
            update_progress("Searching specifications...", "engine_material", "found", confidence)
        else:
            update_progress("Searching specifications...", "engine_material", "partial", 0.5, "Engine material could not be determined")
        
        # Use existing multi-call resolver system for aluminum rims info
        update_progress("Searching specifications...", "rim_material", "searching")
        aluminum_rims = get_aluminum_rims_from_api(year, make, model, progress_callback)  # This uses existing resolver internally
        if aluminum_rims is not None:
            print(f"  -> Resolved aluminum rims: {aluminum_rims}")
            # Try to get confidence score from resolver data if available
            confidence = 0.7  # Default confidence for successful resolution
            if resolution_data and 'aluminum_rims' in resolution_data:
                confidence = resolution_data['aluminum_rims'].get('confidence', 0.7)
            update_progress("Searching specifications...", "rim_material", "found", confidence)
        else:
            update_progress("Searching specifications...", "rim_material", "partial", 0.5, "Rim material could not be determined")

        # Use existing multi-call resolver system for catalytic converters if single-call didn't provide it
        catalytic_converters = None
        if single_call_result and single_call_result.catalytic_converters is not None:
            catalytic_converters = single_call_result.catalytic_converters
            print(f"  -> Using catalytic converter count from single-call: {catalytic_converters}")
            confidence = single_call_result.confidence_scores.get('catalytic_converters', 0.6)
            update_progress("Searching specifications...", "catalytic_converters", "found", confidence)
        else:
            # NOTE: Catalytic converter count estimation is temporarily disabled in multi-call system.
            # TODO: Revisit approach for more accuracy (e.g., OEM diagrams, VIN decoding, engine/bank heuristics).
            # Use default average in calculations for now.
            update_progress("Searching specifications...", "catalytic_converters", "partial", 0.4, "Using default average - specific count not available")
            catalytic_converters = None

        # Check completeness of multi-call resolution and log if incomplete
        vehicle_key = f"{year}_{make}_{model}"
        resolved_fields = []
        missing_fields = []
        
        if weight is not None:
            resolved_fields.append('curb_weight')
        else:
            missing_fields.append('curb_weight')
        
        if aluminum_engine is not None:
            resolved_fields.append('aluminum_engine')
        else:
            missing_fields.append('aluminum_engine')
        
        if aluminum_rims is not None:
            resolved_fields.append('aluminum_rims')
        else:
            missing_fields.append('aluminum_rims')
        
        if catalytic_converters is not None:
            resolved_fields.append('catalytic_converters')
        else:
            missing_fields.append('catalytic_converters')
        
        if missing_fields:
            print(f"  -> WARNING: Incomplete multi-call resolution - missing fields: {missing_fields}")
            logging.warning(f"Incomplete multi-call AI resolution for {vehicle_key}: resolved {resolved_fields}, missing {missing_fields}")
        else:
            print(f"  -> Complete multi-call resolution achieved - all required fields resolved")
            logging.info(f"Complete multi-call AI resolution for {vehicle_key}: all fields resolved")

        # Update database with all resolved data
        update_progress("Saving to database...", None, None)
        update_vehicle_data_in_db(year, make, model, weight, aluminum_engine, aluminum_rims, catalytic_converters, progress_callback)

        update_progress("Search complete", None, None)
        return {
            'curb_weight_lbs': weight,
            'aluminum_engine': aluminum_engine,
            'aluminum_rims': aluminum_rims,
            'catalytic_converters': catalytic_converters
        }


def check_database_status():
    """Check and report database status for debugging persistent volume issues."""
    # This function will need to be updated to use PostgreSQL
    # For now, it will just print a placeholder message
    print("check_database_status is not yet implemented for PostgreSQL.")
    return {}


def test_persistent_volume():
    """Test if persistent volume is working by writing and reading a test file."""
    # This function will need to be updated to use PostgreSQL
    # For now, it will just print a placeholder message
    print("test_persistent_volume is not yet implemented for PostgreSQL.")
    return False


if __name__ == "__main__":
    # create_database() # This line is no longer needed as create_tables is called in database_config

    vehicles_to_process = [
        (2019, "Kia", "Sportage"),
        (2023, "Ford", "F-150"),
        (2022, "Toyota", "Camry"),
        (1999, "Honda", "Civic"),
    ]

    for year, make, model in vehicles_to_process:
        result = process_vehicle(year, make, model)
        print("-" * 20)

    print("\nAdding a vehicle with known data directly to the DB:")
    update_vehicle_data_in_db(2021, "Tesla", "Model 3", 3582, True, True, 1)
    result = process_vehicle(2021, "Tesla", "Model 3")

    print("\nTesting fake vehicle validation:")
    fake_result = process_vehicle(2006, "FakeMake", "WrongModel")
    print(f"Fake vehicle result: {fake_result}")

    print("\nDone.")
