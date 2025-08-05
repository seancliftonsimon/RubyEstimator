import os
import google.generativeai as genai
import re
import streamlit as st
import pandas as pd
from database_config import create_database_engine, get_database_connection, create_tables, test_database_connection, get_database_info
from sqlalchemy import text

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
def initialize_gemini_model():
    """Initialize and return a shared Gemini model instance."""
    if GEMINI_API_KEY != "YOUR_GEMINI_API_KEY":
        genai.configure(api_key=GEMINI_API_KEY)
        return genai.GenerativeModel(model_name='gemini-1.5-flash-latest')
    return None

# Create shared model instance
SHARED_GEMINI_MODEL = initialize_gemini_model()

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
        print(f"Error getting curb weight from database: {e}")
    return None

def get_vehicle_data_from_db(year, make, model):
    """Checks the database for all vehicle data."""
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
        print(f"Error getting vehicle data from database: {e}")
    return None

def update_vehicle_data_in_db(year, make, model, weight, aluminum_engine=None, aluminum_rims=None, catalytic_converters=None):
    """Inserts or updates the vehicle data in the database."""
    try:
        engine = create_database_engine()
        with engine.connect() as conn:
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
            print(f"✅ Vehicle data updated in PostgreSQL database: {year} {make} {model}")
    except Exception as e:
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
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        print("Please set your actual GEMINI_API_KEY in vehicle_data.py.")
        return None

    if SHARED_GEMINI_MODEL is None:
        print("Gemini model not initialized. Please check your API key.")
        return None

    try:
        prompt = (
            f"Search the web to verify if the {year} {make} {model} is a real vehicle that was actually manufactured. "
            "Look for official manufacturer information, automotive databases like Edmunds, KBB, or manufacturer websites, reviews, or dealership listings. "
            f"Specifically check if '{make}' is a legitimate automotive manufacturer and if the model '{model}' was actually produced in {year}. "
            "Be strict - if the manufacturer doesn't exist (like 'FakeMake') or if the model was never made in that year, return 'fake'. "
            "Return ONLY one of these exact values: 'exists', 'fake', or 'inconclusive'. "
            "Do not include any other text or explanation."
        )
        
        response = SHARED_GEMINI_MODEL.generate_content(
            prompt,
            tools=[{"google_search_retrieval": {}}],
            generation_config={"temperature": 0, "max_output_tokens": 16}
        )
        
        text_response = response.text.strip().lower()
        
        if text_response == 'exists':
            return True
        elif text_response == 'fake':
            return False
        elif text_response == 'inconclusive':
            return None
        else:
            return None

    except Exception as e:
        print(f"An error occurred during the vehicle validation API call: {e}")
        return None


def get_aluminum_engine_from_api(year: int, make: str, model: str):
    """
    Returns whether the vehicle has an aluminum engine using Gemini API grounded with Google Search.
    Returns True for aluminum engine, False for iron engine, or None for inconclusive.
    """
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        print("Please set your actual GEMINI_API_KEY in vehicle_data.py.")
        return None

    if SHARED_GEMINI_MODEL is None:
        print("Gemini model not initialized. Please check your API key.")
        return None

    try:
        prompt = (
            f"Search the web to determine if the {year} {make} {model} has an aluminum engine block or iron engine block. "
            "Search for engine specifications, materials, and construction details. "
            "Return ONLY one of these exact values: 'aluminum', 'iron', or 'inconclusive'. "
            "Do not include any other text or explanation."
        )
        
        response = SHARED_GEMINI_MODEL.generate_content(
            prompt,
            tools=[{"google_search_retrieval": {}}],
            generation_config={"temperature": 0, "max_output_tokens": 16}
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

    except Exception as e:
        print(f"An error occurred during the aluminum engine API call: {e}")
        return None


def get_aluminum_rims_from_api(year: int, make: str, model: str):
    """
    Returns whether the vehicle has aluminum rims using Gemini API grounded with Google Search.
    Returns True for aluminum rims, False for steel rims, or None for inconclusive.
    """
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        print("Please set your actual GEMINI_API_KEY in vehicle_data.py.")
        return None

    if SHARED_GEMINI_MODEL is None:
        print("Gemini model not initialized. Please check your API key.")
        return None

    try:
        prompt = (
            f"Search the web to determine if the {year} {make} {model} has aluminum wheels/rims or steel wheels/rims. "
            "Search for wheel specifications, materials, and construction details. "
            "Return ONLY one of these exact values: 'aluminum', 'steel', or 'inconclusive'. "
            "Do not include any other text or explanation."
        )
        
        response = SHARED_GEMINI_MODEL.generate_content(
            prompt,
            tools=[{"google_search_retrieval": {}}],
            generation_config={"temperature": 0, "max_output_tokens": 16}
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

    except Exception as e:
        print(f"An error occurred during the aluminum rims API call: {e}")
        return None


def get_curb_weight_from_api(year: int, make: str, model: str):
    """
    Returns curb weight in pounds using Gemini API grounded with Google Search.
    Uses a two-step process: gather candidates, then interpret the best weight.
    """
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        print("Please set your actual GEMINI_API_KEY in vehicle_data.py.")
        return None

    if SHARED_GEMINI_MODEL is None:
        print("Gemini model not initialized. Please check your API key.")
        return None

    try:
        # Step 1: Gather candidate weights with preferred sources
        gather_prompt = (
            f"Search the web and list every curb-weight figure (in pounds) you find for a {year} {make} {model}. "
            "Prioritise results from Kelley Blue Book (kbb.com), Edmunds (edmunds.com) or the manufacturer's official site. "
            "Return one line per finding in the exact format '<WEIGHT> <source>'. Only include numbers; omit commentary."
        )

        gather_resp = SHARED_GEMINI_MODEL.generate_content(
            gather_prompt,
            tools=[{"google_search_retrieval": {}}],
            generation_config={"temperature": 0, "max_output_tokens": 64},
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

            interpret_resp = SHARED_GEMINI_MODEL.generate_content(
                interpret_prompt,
                tools=[{"google_search_retrieval": {}}],
                generation_config={"temperature": 0, "max_output_tokens": 8},
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

    except Exception as e:
        print(f"An error occurred during the Gemini API call: {e}")
        return None

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
    Estimates the number of catalytic converters for a vehicle using Gemini API.
    Searches multiple parts catalogs and counts unique catalytic converter positions.
    """
    print(f"\n  -> Searching for catalytic converter count for {year} {make} {model}...")
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        print("Please set your actual GEMINI_API_KEY in vehicle_data.py.")
        return None

    if SHARED_GEMINI_MODEL is None:
        print("Gemini model not initialized. Please check your API key.")
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
        
        response = SHARED_GEMINI_MODEL.generate_content(
            prompt,
            tools=[{"google_search_retrieval": {}}],
            generation_config={"temperature": 0, "max_output_tokens": 8}
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




def process_vehicle(year, make, model):
    """
    Main logic to get vehicle data (curb weight, aluminum engine, aluminum rims, and catalytic converters).
    It first validates the vehicle exists, then checks the local database, and if not found, queries the Gemini API.
    """
    print(f"Processing: {year} {make} {model}")
    
    # Check if this vehicle was previously marked as fake in this session
    if is_vehicle_marked_as_fake(year, make, model):
        print(f"  -> Vehicle previously marked as fake in session: {year} {make} {model}")
        return None
    
    # Check database for legitimate vehicle data
    vehicle_data = get_vehicle_data_from_db(year, make, model)
    
    if vehicle_data and vehicle_data['curb_weight_lbs'] is not None and vehicle_data['curb_weight_lbs'] > 0:
        print(f"  -> Found in DB: {vehicle_data['curb_weight_lbs']} lbs, Cats: {vehicle_data['catalytic_converters']}")
        
        # If catalytic converter data is missing, get it and update the record
        if vehicle_data['catalytic_converters'] is None:
            print("  -> Missing catalytic converter data, querying API...")
            catalytic_converters = get_catalytic_converter_count_from_api(year, make, model)
            if catalytic_converters is not None:
                print(f"  -> Found catalytic converter count via API: {catalytic_converters}")
                # Update just the catalytic converter count in the database
                update_vehicle_data_in_db(
                    year, make, model,
                    vehicle_data['curb_weight_lbs'],
                    vehicle_data['aluminum_engine'],
                    vehicle_data['aluminum_rims'],
                    catalytic_converters
                )
                vehicle_data['catalytic_converters'] = catalytic_converters
        
        return vehicle_data
    else:
        print("  -> Not in DB or missing data. Validating vehicle existence first...")
        
        # Validate vehicle existence before making expensive API calls
        vehicle_exists = validate_vehicle_existence(year, make, model)
        
        if vehicle_exists is False:
            print(f"  -> Vehicle validation failed: {year} {make} {model} does not exist")
            mark_vehicle_as_not_found(year, make, model)
            return None  # Return None to indicate vehicle not found
        elif vehicle_exists is None:
            print(f"  -> Vehicle validation inconclusive for: {year} {make} {model}")
            # Continue with processing but be aware it might be invalid
        else:
            print(f"  -> Vehicle validation passed: {year} {make} {model} exists")
        
        print("  -> Proceeding with API queries...")
        
        # Get curb weight
        weight = get_curb_weight_from_api(year, make, model)
        if weight:
            print(f"  -> Found curb weight via API: {weight} lbs")
        
        # Additional validation: if no weight found and vehicle existence was inconclusive, 
        # it's likely a fake vehicle
        if not weight and vehicle_exists is None:
            print(f"  -> No weight found and vehicle existence inconclusive - likely fake vehicle")
            mark_vehicle_as_not_found(year, make, model)
            return None
        
        # Get aluminum engine info
        aluminum_engine = get_aluminum_engine_from_api(year, make, model)
        if aluminum_engine is not None:
            print(f"  -> Found aluminum engine info via API: {aluminum_engine}")
        
        # Get aluminum rims info
        aluminum_rims = get_aluminum_rims_from_api(year, make, model)
        if aluminum_rims is not None:
            print(f"  -> Found aluminum rims info via API: {aluminum_rims}")

        # Get catalytic converter count
        catalytic_converters = get_catalytic_converter_count_from_api(year, make, model)
        if catalytic_converters is not None:
            print(f"  -> Found catalytic converter count via API: {catalytic_converters}")
        
        # Update database with all data
        update_vehicle_data_in_db(year, make, model, weight, aluminum_engine, aluminum_rims, catalytic_converters)
        
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
