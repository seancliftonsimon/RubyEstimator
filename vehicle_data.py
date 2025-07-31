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
            UNIQUE(year, make, model)
        )
    """)
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


def update_curb_weight_in_db(year, make, model, weight):
    """Inserts or updates the curb weight for a vehicle in the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO vehicles (year, make, model, curb_weight_lbs)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(year, make, model) DO UPDATE SET curb_weight_lbs = excluded.curb_weight_lbs;
    """, (year, make, model, weight))
    conn.commit()
    conn.close()


def get_curb_weight_from_api(year: int, make: str, model: str):
    """
    Returns curb weight in pounds using Gemini API grounded with Google Search.
    Always forces a search and returns an integer (lbs) or None (for Inconclusive).
    """
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        print("Please set your actual GEMINI_API_KEY in vehicle_data.py.")
        return None

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        model_instance = genai.GenerativeModel(model_name='gemini-1.5-flash-latest')

        # First call: gather candidate weights with preferred sources
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
            return None  # Inconclusive

        # Choose the most common weight; if tie, pick the first encountered
        from collections import Counter
        counts = Counter(candidate_numbers)
        most_common_weight, freq = counts.most_common(1)[0]
        # Simple majority check: must appear at least twice or be the only value
        if freq == 1 and len(candidate_numbers) > 1:
            return None
        return most_common_weight

        response = model_instance.generate_content(
            prompt,
            tools=[{"google_search_retrieval": {}}]
        )
        
        # --- Enhanced Debugging ---
        print("\n--- Full API Response ---")
        print(response)
        print("--- End Full API Response ---\n")
        
        text_response = response.text.strip()

        if text_response.lower() == 'inconclusive':
            print("  -> API returned 'Inconclusive'.")
            return None

        # Use regex to find any number in the response, in case of extra text.
        numeric_match = re.search(r'\d+', text_response.replace(',', ''))
        if numeric_match:
            try:
                weight = int(numeric_match.group(0))
                return weight
            except (ValueError, IndexError):
                 print(f"  -> Could not extract a valid number from API response: '{text_response}'")
                 return None
        else:
            print(f"  -> API returned a non-numeric or unexpected value: '{text_response}'")
            return None

    except Exception as e:
        print(f"An error occurred during the Gemini API call: {e}")
        return None


def process_vehicle(year, make, model):
    """
    Main logic to get curb weight for a vehicle.
    It first checks the local database, and if not found, queries the Gemini API.
    """
    print(f"Processing: {year} {make} {model}")
    weight = get_curb_weight_from_db(year, make, model)

    if weight:
        print(f"  -> Found in DB: {weight} lbs")
        return weight
    else:
        print("  -> Not in DB. Querying API...")
        weight = get_curb_weight_from_api(year, make, model)
        if weight:
            print(f"  -> Found via API: {weight} lbs")
            update_curb_weight_in_db(year, make, model, weight)
            return weight
        else:
            print("  -> Could not find curb weight.")
            update_curb_weight_in_db(year, make, model, None)
            return None


if __name__ == "__main__":
    create_database()

    vehicles_to_process = [
        (2019, "Kia", "Sportage"),
        (2023, "Ford", "F-150"),
        (2022, "Toyota", "Camry"),
        (1999, "Honda", "Civic"),
    ]

    for year, make, model in vehicles_to_process:
        process_vehicle(year, make, model)
        print("-" * 20)

    print("\nAdding a vehicle with a known weight directly to the DB:")
    update_curb_weight_in_db(2021, "Tesla", "Model 3", 3582)
    process_vehicle(2021, "Tesla", "Model 3")

    print("\nDone.")
