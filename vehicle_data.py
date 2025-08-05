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
    return 1 # Default to 1 if no other data is available

def get_catalytic_converter_count_from_api(year: int, make: str, model: str):
    """
    Estimates the number of catalytic converters for a vehicle using Gemini API.
    """
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        print("Please set your actual GEMINI_API_KEY in vehicle_data.py.")
        return None

    if SHARED_GEMINI_MODEL is None:
        print("Gemini model not initialized. Please check your API key.")
        return None

    query_templates = {
        "walker":  f'{year} {make} {model} catalytic converter site:walkerexhaust.com "Bank"',
        "magna":   f'{year} {make} {model} catalytic converter site:magnaflow.com "Bank"',
        "ap":      f'{year} {make} {model} catalytic converter site:apemissions.com "Bank"',
    }

    schema = {
      "type":"function",
      "function":{
          "name":"set_result",
          "parameters":{
              "converter_count":{"type":"integer"}
          },
          "required":["converter_count"]
      }
    }

    for catalog, query in query_templates.items():
        try:
            prompt = f"""
            Return ONLY set_result() with converter_count.
            Rule: Count unique ‘Bank’, ‘Manifold’, or ‘Rear’ positions you see in the
            search snippets for **{year} {make} {model}** on {catalog}.
            If nothing matches, return -1.
            """
            response = SHARED_GEMINI_MODEL.generate_content(
                prompt,
                tools=[schema],
                tool_config={'function_calling_config': 'ANY'},
                generation_config={"temperature": 0}
            )

            # Extract the function call response
            function_call = response.candidates[0].content.parts[0].function_call
            if function_call.name == "set_result":
                count = function_call.args["converter_count"]
                if count > 0:
                    return count

        except Exception as e:
            print(f"An error occurred during the {catalog} API call: {e}")
            continue

    return heuristic_rule(year, make, model)




def process_vehicle(year, make, model):
    """
    Main logic to get vehicle data (curb weight, aluminum engine, aluminum rims, and catalytic converters).
    It first checks the local database, and if not found, queries the Gemini API.
    """
    print(f"Processing: {year} {make} {model}")
    
    # Check database first
    vehicle_data = get_vehicle_data_from_db(year, make, model)
    
    if vehicle_data and vehicle_data['curb_weight_lbs'] is not None:
        print(f"  -> Found in DB: {vehicle_data['curb_weight_lbs']} lbs, Cats: {vehicle_data['catalytic_converters']}")
        return vehicle_data
    else:
        print("  -> Not in DB or missing data. Querying APIs...")
        
        # Get curb weight
        weight = get_curb_weight_from_api(year, make, model)
        if weight:
            print(f"  -> Found curb weight via API: {weight} lbs")
        
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

    print("\nDone.")
