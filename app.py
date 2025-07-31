import streamlit as st
import sqlite3
import pandas as pd
from vehicle_data import process_vehicle, create_database, DB_FILE

def get_last_ten_entries():
    """Fetches the last 10 vehicle entries from the database."""
    try:
        conn = sqlite3.connect(DB_FILE)
        # Order by id DESC to get the most recent entries
        query = "SELECT year, make, model, curb_weight_lbs FROM vehicles ORDER BY id DESC LIMIT 10"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame() # Return empty DataFrame on error

# --- Streamlit App ---

st.set_page_config(page_title="Vehicle Curb Weight Estimator", layout="centered")

st.title("Vehicle Curb Weight Estimator")
st.write("Enter the details of a vehicle to find its curb weight. The tool will first check the local database. If the vehicle is not found, it will use the Gemini API to search for the weight and save it for future use.")

# --- Main Form ---
with st.form(key="vehicle_form"):
    st.header("Search for a Vehicle")
    col1, col2, col3 = st.columns(3)
    with col1:
        year_input = st.number_input("Year", min_value=1900, max_value=2050, step=1, value=2023)
    with col2:
        make_input = st.text_input("Make", placeholder="e.g., Ford")
    with col3:
        model_input = st.text_input("Model", placeholder="e.g., F-150")

    submit_button = st.form_submit_button(label="Get Curb Weight")

# --- Processing and Output ---
if submit_button:
    if not make_input or not model_input:
        st.warning("Please enter both a make and a model.")
    else:
        with st.spinner(f"Processing {year_input} {make_input} {model_input}..."):
            # The process_vehicle function already handles DB checks, API calls, and DB updates.
            # It also prints to the console, which is fine for this simple app.
            weight = process_vehicle(year_input, make_input.strip(), model_input.strip())
            if weight:
                st.success(f"**Curb Weight:** {weight} lbs")
            else:
                st.error("Could not determine the curb weight. The result has been stored as 'Inconclusive' to prevent repeated searches.")

# --- Display Last 10 Entries ---
st.header("Recently Searched Vehicles")
st.write("This table shows the last 10 vehicles that were looked up.")

try:
    recent_entries_df = get_last_ten_entries()
    if not recent_entries_df.empty:
        st.dataframe(recent_entries_df, use_container_width=True)
    else:
        st.info("The database is currently empty. Search for a vehicle to populate it.")
except Exception as e:
    st.error(f"An error occurred while fetching recent entries: {e}")


# --- Initial Setup ---
if 'db_created' not in st.session_state:
    create_database()
    st.session_state['db_created'] = True
