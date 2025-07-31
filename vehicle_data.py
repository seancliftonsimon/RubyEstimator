import sqlite3
import os
import google.generativeai as genai
import re

# --- Configuration ---
# IMPORTANT: Replace with your actual Gemini API Key.
# You can get a key from Google AI Studio: https://aistudio.google.com/app/apikey
GEMINI_API_KEY = "AIzaSyDhOpIAllne17hVDZI2ADXuUcSeE0cPYvY"
DB_FILE = "vehicle_weights.db"


def create_database():
    """Creates the SQLite database and table if they don't exist."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY,
            year INTEGER NOT NULL,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            curb_weight_lbs INTEGER,
            aluminum_engine BOOLEAN,
            aluminum_rims BOOLEAN,
            UNIQUE(year, make, model)
        )
    """)
    
    # Check if new columns exist, if not add them
    c.execute("PRAGMA table_info(vehicles)")
    columns = [row[1] for row in c.fetchall()]
    
    if 'aluminum_engine' not in columns:
        c.execute("ALTER TABLE vehicles ADD COLUMN aluminum_engine BOOLEAN")
        print("Added aluminum_engine column to existing table")
    
    if 'aluminum_rims' not in columns:
        c.execute("ALTER TABLE vehicles ADD COLUMN aluminum_rims BOOLEAN")
        print("Added aluminum_rims column to existing table")
    
    conn.commit()
    conn.close()


def get_curb_weight_from_db(year, make, model):
    """Checks the database for the curb weight of a specific vehicle."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT curb_weight_lbs FROM vehicles WHERE year = ? AND make = ? AND model = ?", (year, make, model))
    result = c.fetchone()
    conn.close()
    if result and result[0] is not None:
        return result[0]
    return None


def get_vehicle_data_from_db(year, make, model):
    """Checks the database for all vehicle data."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT curb_weight_lbs, aluminum_engine, aluminum_rims FROM vehicles WHERE year = ? AND make = ? AND model = ?", (year, make, model))
    result = c.fetchone()
    conn.close()
    if result:
        return {
            'curb_weight_lbs': result[0],
            'aluminum_engine': result[1],
            'aluminum_rims': result[2]
        }
    return None


def update_vehicle_data_in_db(year, make, model, weight, aluminum_engine=None, aluminum_rims=None):
    """Inserts or updates the vehicle data in the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO vehicles (year, make, model, curb_weight_lbs, aluminum_engine, aluminum_rims)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(year, make, model) DO UPDATE SET 
            curb_weight_lbs = excluded.curb_weight_lbs,
            aluminum_engine = excluded.aluminum_engine,
            aluminum_rims = excluded.aluminum_rims;
    """, (year, make, model, weight, aluminum_engine, aluminum_rims))
    conn.commit()
    conn.close()


def get_aluminum_engine_from_api(year: int, make: str, model: str):
    """
    Returns whether the vehicle has an aluminum engine using Gemini API grounded with Google Search.
    Returns True for aluminum engine, False for iron engine, or None for inconclusive.
    """
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        print("Please set your actual GEMINI_API_KEY in vehicle_data.py.")
        return None

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model_instance = genai.GenerativeModel(model_name='gemini-1.5-flash-latest')

        prompt = (
            f"Search the web to determine if the {year} {make} {model} has an aluminum engine block or iron engine block. "
            "Search for engine specifications, materials, and construction details. "
            "Return ONLY one of these exact values: 'aluminum', 'iron', or 'inconclusive'. "
            "Do not include any other text or explanation."
        )
        
        response = model_instance.generate_content(
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

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model_instance = genai.GenerativeModel(model_name='gemini-1.5-flash-latest')

        prompt = (
            f"Search the web to determine if the {year} {make} {model} has aluminum wheels/rims or steel wheels/rims. "
            "Search for wheel specifications, materials, and construction details. "
            "Return ONLY one of these exact values: 'aluminum', 'steel', or 'inconclusive'. "
            "Do not include any other text or explanation."
        )
        
        response = model_instance.generate_content(
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

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model_instance = genai.GenerativeModel(model_name='gemini-1.5-flash-latest')

        # Step 1: Gather candidate weights with preferred sources
        gather_prompt = (
            f"Search the web and list every curb-weight figure (in pounds) you find for a {year} {make} {model}. "
            "Prioritise results from Kelley Blue Book (kbb.com), Edmunds (edmunds.com) or the manufacturer's official site. "
            "Return one line per finding in the exact format '<WEIGHT> <source>'. Only include numbers; omit commentary."
        )

        gather_resp = model_instance.generate_content(
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
                "Consider typical weight ranges for this vehicle type and year. "
                "Return ONLY the weight number, no other text."
            )

            interpret_resp = model_instance.generate_content(
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


def process_vehicle(year, make, model):
    """
    Main logic to get vehicle data (curb weight, aluminum engine, aluminum rims).
    It first checks the local database, and if not found, queries the Gemini API.
    """
    print(f"Processing: {year} {make} {model}")
    
    # Check database first
    vehicle_data = get_vehicle_data_from_db(year, make, model)
    
    if vehicle_data and vehicle_data['curb_weight_lbs'] is not None:
        print(f"  -> Found in DB: {vehicle_data['curb_weight_lbs']} lbs")
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
        
        # Update database with all data
        update_vehicle_data_in_db(year, make, model, weight, aluminum_engine, aluminum_rims)
        
        return {
            'curb_weight_lbs': weight,
            'aluminum_engine': aluminum_engine,
            'aluminum_rims': aluminum_rims
        }


if __name__ == "__main__":
    create_database()

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
    update_vehicle_data_in_db(2021, "Tesla", "Model 3", 3582, True, True)
    result = process_vehicle(2021, "Tesla", "Model 3")

    print("\nDone.")
