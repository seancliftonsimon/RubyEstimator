import streamlit as st
import sqlite3
import pandas as pd
from vehicle_data import process_vehicle, create_database, DB_FILE

# --- Cost Estimator Constants ---
PRICE_PER_LB = {
    "ELV": 0.118,
    "AL_ENGINE": 0.3525,
    "FE_ENGINE": 0.2325,
    "HARNESS": 1.88,
    "FE_RAD": 0.565,
    "BREAKAGE": 0.26,
    "ALT": 0.88,
    "STARTER": 0.73,
    "AC_COMP": 0.55,
    "FUSE_BOX": 0.82,
    "BATTERY": 0.36,
    "AL_RIMS": 1.24,
    "CATS": 92.25,
    "TIRES": 4.5,     # special handling
    "ECM": 1.32,
}

FLAT_COSTS = {
    "PURCHASE": 475,
    "TOW": 90,
    "LEAD_PER_CAR": 107.5,
    "NUT_PER_LB": 0.015,
}

# --- Cost Estimator Functions ---
def compute_commodities(cars, curb_weight):
    """Compute all commodity weights, prices, and sale values."""
    w = lambda lbs: cars * lbs
    list_commodities = [
        {"key": "AL_ENGINE", "label": "AL Engine", "weight": w(275), "unit_price": PRICE_PER_LB["AL_ENGINE"], "sale_value": 0},
        {"key": "FE_ENGINE", "label": "FE Engine", "weight": w(275), "unit_price": PRICE_PER_LB["FE_ENGINE"], "sale_value": 0},
        {"key": "HARNESS", "label": "Harness", "weight": w(23), "unit_price": PRICE_PER_LB["HARNESS"], "sale_value": 0},
        {"key": "FE_RAD", "label": "FE Rad", "weight": w(18), "unit_price": PRICE_PER_LB["FE_RAD"], "sale_value": 0},
        {"key": "BREAKAGE", "label": "Breakage", "weight": w(15), "unit_price": PRICE_PER_LB["BREAKAGE"], "sale_value": 0},
        {"key": "ALT", "label": "Alt", "weight": w(12), "unit_price": PRICE_PER_LB["ALT"], "sale_value": 0},
        {"key": "STARTER", "label": "Starter", "weight": w(8), "unit_price": PRICE_PER_LB["STARTER"], "sale_value": 0},
        {"key": "AC_COMP", "label": "AC Comp", "weight": w(7), "unit_price": PRICE_PER_LB["AC_COMP"], "sale_value": 0},
        {"key": "FUSE_BOX", "label": "Fuse Box", "weight": w(6), "unit_price": PRICE_PER_LB["FUSE_BOX"], "sale_value": 0},
        {"key": "BATTERY", "label": "Battery", "weight": w(5), "unit_price": PRICE_PER_LB["BATTERY"], "sale_value": 0},
        {"key": "AL_RIMS", "label": "AL Rims", "weight": w(4), "unit_price": PRICE_PER_LB["AL_RIMS"], "sale_value": 0},
        {"key": "CATS", "label": "Cats", "weight": w(3), "unit_price": PRICE_PER_LB["CATS"], "sale_value": 0},
        {"key": "ECM", "label": "ECM", "weight": w(2), "unit_price": PRICE_PER_LB["ECM"], "sale_value": 0},
    ]

    # Calculate ELV weight (curb weight minus engine weights)
    al_engine_w = list_commodities[0]["weight"]  # AL_ENGINE weight
    fe_engine_w = list_commodities[1]["weight"]  # FE_ENGINE weight
    elv_weight = curb_weight - al_engine_w - fe_engine_w

    # Add ELV at the beginning
    list_commodities.insert(0, {
        "key": "ELV",
        "label": "ELV",
        "weight": elv_weight,
        "unit_price": PRICE_PER_LB["ELV"],
        "sale_value": 0,
    })

    # Add TIRES at the end (special handling)
    list_commodities.append({
        "key": "TIRES",
        "label": "Tires",
        "weight": cars * 25,
        "unit_price": PRICE_PER_LB["TIRES"],
        "sale_value": cars * PRICE_PER_LB["TIRES"] * 25,  # sale = cars × price × 25
    })

    # Compute sale values for all commodities except TIRES
    for commodity in list_commodities:
        if commodity["key"] != "TIRES":
            commodity["sale_value"] = commodity["weight"] * commodity["unit_price"]

    return list_commodities

def calculate_totals(commodities, cars, curb_weight):
    """Calculate total sale value and all costs."""
    total_sale = sum(c["sale_value"] for c in commodities)
    purchase = FLAT_COSTS["PURCHASE"]
    tow = FLAT_COSTS["TOW"]
    lead = cars * FLAT_COSTS["LEAD_PER_CAR"]
    nut = curb_weight * FLAT_COSTS["NUT_PER_LB"]
    net = total_sale - (purchase + tow + lead + nut)
    
    return {
        "total_sale": total_sale,
        "purchase": purchase,
        "tow": tow,
        "lead": lead,
        "nut": nut,
        "net": net
    }

def format_currency(amount):
    """Format amount as currency."""
    return f"${amount:,.2f}"

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

# Configure page with light mode styling
st.set_page_config(
    page_title="RubyEstimator - Vehicle Weight & Cost Calculator",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for light theme with ruby and teal accents
st.markdown("""
<style>
    /* Global background and text colors */
    .main {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #cbd5e1 100%);
        color: #1e293b;
    }
    
    /* Main title styling */
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1.5rem;
        background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #dc2626;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    }
    
    /* Subsection headers */
    .subsection-header {
        font-size: 1.2rem;
        font-weight: 500;
        color: #475569;
        margin-bottom: 0.75rem;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    }
    
    /* Enhanced card styling for main sections */
    .main-section-card {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        border: 1px solid rgba(220, 38, 38, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    
    /* Success message styling */
    .success-message {
        background: rgba(34, 197, 94, 0.1);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #22c55e;
        margin: 1rem 0;
        color: #166534;
    }
    
    /* Warning message styling */
    .warning-message {
        background: rgba(245, 158, 11, 0.1);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #f59e0b;
        margin: 1rem 0;
        color: #92400e;
    }
    
    /* Error message styling */
    .error-message {
        background: rgba(239, 68, 68, 0.1);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ef4444;
        margin: 1rem 0;
        color: #991b1b;
    }
    
    /* Form styling */
    .stForm {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid rgba(220, 38, 38, 0.2);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
    }
    
    /* Enhanced input field styling */
    .stTextInput > div > div > input, .stNumberInput > div > div > input {
        background: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid rgba(220, 38, 38, 0.3) !important;
        border-radius: 6px;
        padding: 0.75rem;
        transition: all 0.2s ease;
        color: #1e293b !important;
    }
    
    .stTextInput > div > div > input:focus, .stNumberInput > div > div > input:focus {
        border-color: #dc2626 !important;
        box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.2) !important;
        outline: none;
        background: rgba(255, 255, 255, 1) !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: rgba(71, 85, 105, 0.6) !important;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(220, 38, 38, 0.4);
        color: #ffffff !important;
    }
    
    /* Dataframe styling */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        background: rgba(255, 255, 255, 0.9) !important;
        backdrop-filter: blur(10px);
    }
    
    .dataframe th {
        background: rgba(220, 38, 38, 0.1) !important;
        color: #1e293b !important;
        font-weight: 600;
    }
    
    .dataframe td {
        background: rgba(255, 255, 255, 0.8) !important;
        color: #1e293b !important;
        border-color: rgba(220, 38, 38, 0.1) !important;
    }
    
    /* Metric styling */
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1e293b;
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Ensure proper contrast for all text elements */
    .stMarkdown, .stText, .stNumberInput, .stSelectbox, .stTextInput {
        color: #1e293b !important;
    }
    
    /* Ensure form labels are visible */
    .stForm label, .stForm p {
        color: #475569 !important;
        font-weight: 500;
    }
    
    /* Ensure button text is visible */
    .stButton > button {
        color: #ffffff !important;
    }
    
    /* Info icon styling */
    .info-icon-container {
        display: inline-block;
        margin-left: 1rem;
        vertical-align: middle;
    }
    
    .info-icon {
        display: inline-block;
        width: 40px;
        height: 40px;
        background: rgba(20, 184, 166, 0.1);
        border: 1px solid rgba(20, 184, 166, 0.4);
        border-radius: 50%;
        text-align: center;
        line-height: 36px;
        font-size: 18px;
        color: #14b8a6;
        cursor: help;
        transition: all 0.2s ease;
        position: relative;
    }
    
    .info-icon:hover {
        background: rgba(20, 184, 166, 0.2);
        border-color: rgba(20, 184, 166, 0.6);
        transform: scale(1.1);
        box-shadow: 0 2px 8px rgba(20, 184, 166, 0.3);
    }
    
    /* Custom tooltip styling */
    .info-icon:hover::after {
        content: attr(title);
        position: absolute;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(30, 41, 59, 0.95);
        color: #ffffff;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        font-size: 0.875rem;
        font-weight: 400;
        line-height: 1.4;
        white-space: normal;
        z-index: 1000;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.1);
        min-width: 400px;
        max-width: 500px;
        text-align: left;
        word-wrap: break-word;
    }
    
    .info-icon:hover::before {
        content: '';
        position: absolute;
        bottom: 115%;
        left: 50%;
        transform: translateX(-50%);
        border: 5px solid transparent;
        border-top-color: rgba(30, 41, 59, 0.95);
        z-index: 1000;
    }
    
    /* Info box styling (keeping for backward compatibility) */
    .info-box {
        background: rgba(20, 184, 166, 0.1);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #14b8a6;
        margin: 1rem 0;
        color: #0f766e;
    }
    
    /* Remove extra spacing */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    /* Streamlit metric containers */
    .stMetric {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border-radius: 8px;
        padding: 1rem;
        border: 1px solid rgba(220, 38, 38, 0.2);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
    }
    
    /* Remove default Streamlit spacing */
    .stApp > header {
        background-color: transparent;
    }
    
    .stApp > footer {
        background-color: transparent;
    }
    
    /* Ensure all text has proper contrast */
    p, h1, h2, h3, h4, h5, h6, span, div {
        color: #1e293b !important;
    }
    
    /* Style the main container */
    .main .block-container {
        background: transparent;
    }
    
    /* Additional teal accents for variety */
    .teal-accent {
        color: #14b8a6;
        font-weight: 600;
    }
    
    .teal-border {
        border-color: #14b8a6 !important;
    }
    
    .teal-bg {
        background-color: rgba(20, 184, 166, 0.1) !important;
    }
</style>
""", unsafe_allow_html=True)

# Main title with ruby gradient effect
st.markdown('<h1 class="main-title">🚗 RubyEstimator</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #475569; font-size: 1.1rem; margin-bottom: 2rem; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);">Vehicle Weight Estimator & Cost Calculator</p>', unsafe_allow_html=True)

# Create two columns for the main layout
left_col, right_col = st.columns([1, 1])

# --- Left Column: Vehicle Search ---
with left_col:
    st.markdown("""
    <h2 class="section-header">
        Vehicle Weight Search
        <div class="info-icon-container">
            <span class="info-icon" title="Enter vehicle details to find curb weight. The tool checks the local database first, then uses the Gemini API for new searches and saves results for future use.">ⓘ</span>
        </div>
    </h2>
    """, unsafe_allow_html=True)

    # --- Main Form ---
    with st.form(key="vehicle_form"):
        st.markdown('<h3 class="subsection-header">Vehicle Information</h3>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            year_input = st.number_input("Year", min_value=1900, max_value=2050, step=1, value=2023)
        with col2:
            make_input = st.text_input("Make", placeholder="e.g., Ford")
        with col3:
            model_input = st.text_input("Model", placeholder="e.g., F-150")

        submit_button = st.form_submit_button(label="Get Curb Weight", use_container_width=True)

    # --- Processing and Output ---
    if submit_button:
        if not make_input or not model_input:
            st.markdown("""
            <div class="warning-message">
                <strong>Missing Information:</strong> Please enter both a make and a model.
            </div>
            """, unsafe_allow_html=True)
        else:
            with st.spinner(f"Searching for {year_input} {make_input} {model_input}..."):
                weight = process_vehicle(year_input, make_input.strip(), model_input.strip())
                if weight:
                    st.markdown(f"""
                    <div class="success-message">
                        <strong>Weight Found:</strong> <span class="metric-value">{weight} lbs</span>
                    </div>
                    """, unsafe_allow_html=True)
                    # Store the weight in session state for the cost estimator
                    st.session_state['last_curb_weight'] = weight
                else:
                    st.markdown("""
                    <div class="error-message">
                        <strong>Weight Not Found:</strong> Could not determine the curb weight. 
                        The result has been stored as 'Inconclusive' to prevent repeated searches.
                    </div>
                    """, unsafe_allow_html=True)

    # --- Display Last 10 Entries ---
    st.markdown('<h3 class="subsection-header">Recently Searched Vehicles</h3>', unsafe_allow_html=True)
    
    try:
        recent_entries_df = get_last_ten_entries()
        if not recent_entries_df.empty:
            # Style the dataframe
            styled_df = recent_entries_df.style.set_properties(**{
                'background-color': 'rgba(255, 255, 255, 0.05)',
                'color': '#ffffff',
                'border-color': 'rgba(255, 255, 255, 0.1)'
            }).format({'curb_weight_lbs': '{:,.0f} lbs'})
            
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        else:
            st.info("The database is currently empty. Search for a vehicle to populate it.")
    except Exception as e:
        st.error(f"An error occurred while fetching recent entries: {e}")

# --- Right Column: Cost Estimator ---
with right_col:
    st.markdown("""
    <h2 class="section-header">
        Cost Estimator
        <div class="info-icon-container">
            <span class="info-icon" title="Calculate commodity weights, sale values, costs, and net profit based on the number of cars and combined curb weight.">ⓘ</span>
        </div>
    </h2>
    """, unsafe_allow_html=True)
    
    # Cost estimator form
    with st.form(key="cost_estimator_form"):
        st.markdown('<h3 class="subsection-header">Calculation Parameters</h3>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            cars_input = st.number_input("Number of Cars", min_value=1, value=1, step=1)
        with col2:
            # Use last curb weight if available, otherwise default to 3600
            default_weight = st.session_state.get('last_curb_weight', 3600)
            curb_weight_input = st.number_input("Combined Curb Weight (lb)", min_value=1, value=default_weight, step=1)
        
        calculate_button = st.form_submit_button(label="Calculate Costs", use_container_width=True)
    
    # Calculate and display results
    if calculate_button:
        commodities = compute_commodities(cars_input, curb_weight_input)
        totals = calculate_totals(commodities, cars_input, curb_weight_input)
        
        # Display summary metrics
        st.markdown('<h3 class="subsection-header">Summary Metrics</h3>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Sale Value", format_currency(totals["total_sale"]))
        with col2:
            st.metric("Total Costs", format_currency(totals["purchase"] + totals["tow"] + totals["lead"] + totals["nut"]))
        with col3:
            st.metric("Net Profit", format_currency(totals["net"]), 
                     delta="Profit" if totals["net"] > 0 else "Loss")
        
        # Display commodities table
        st.markdown('<h3 class="subsection-header">Commodity Breakdown</h3>', unsafe_allow_html=True)
        
        # Create DataFrame for better display
        commodity_data = []
        for commodity in commodities:
            commodity_data.append({
                "Commodity": commodity["label"],
                "Weight (lb)": f"{commodity['weight']:.1f}",
                "$/lb": f"{commodity['unit_price']:.2f}",
                "Sale Value": format_currency(commodity["sale_value"])
            })
        
        commodity_df = pd.DataFrame(commodity_data)
        
        # Style the commodity dataframe
        styled_commodity_df = commodity_df.style.set_properties(**{
            'background-color': 'rgba(255, 255, 255, 0.05)',
            'color': '#ffffff',
            'border-color': 'rgba(255, 255, 255, 0.1)'
        }).format({
            'Weight (lb)': '{:,.1f}',
            '$/lb': '{:.2f}'
        })
        
        st.dataframe(styled_commodity_df, use_container_width=True, hide_index=True)
        
        # Display detailed cost breakdown
        st.markdown('<h3 class="subsection-header">Cost Breakdown</h3>', unsafe_allow_html=True)
        
        # Create summary DataFrame with better formatting
        summary_data = [
            {"Item": "Total Sale", "Amount": format_currency(totals["total_sale"]), "Type": "Revenue"},
            {"Item": "Purchase Cost", "Amount": f"-{format_currency(totals['purchase'])}", "Type": "Cost"},
            {"Item": "Tow Fee", "Amount": f"-{format_currency(totals['tow'])}", "Type": "Cost"},
            {"Item": "Lead Fee", "Amount": f"-{format_currency(totals['lead'])}", "Type": "Cost"},
            {"Item": "Nut Fee", "Amount": f"-{format_currency(totals['nut'])}", "Type": "Cost"},
        ]
        
        summary_df = pd.DataFrame(summary_data)
        
        # Style the summary dataframe
        styled_summary_df = summary_df.style.set_properties(**{
            'background-color': 'rgba(255, 255, 255, 0.05)',
            'color': '#ffffff',
            'border-color': 'rgba(255, 255, 255, 0.1)'
        })
        
        st.dataframe(styled_summary_df, use_container_width=True, hide_index=True)
        
        # Net profit highlight
        if totals["net"] > 0:
            st.markdown(f"""
            <div style="background: rgba(34, 197, 94, 0.1); padding: 1.5rem; border-radius: 8px; text-align: center; margin-top: 1rem; border: 1px solid #22c55e;">
                <h3 style="margin: 0; color: #166534;">Net Profit</h3>
                <p style="font-size: 2rem; font-weight: 700; margin: 0.5rem 0; color: #166534;">
                    {format_currency(totals["net"])}
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: rgba(239, 68, 68, 0.1); padding: 1.5rem; border-radius: 8px; text-align: center; margin-top: 1rem; border: 1px solid #ef4444;">
                <h3 style="margin: 0; color: #991b1b;">Net Loss</h3>
                <p style="font-size: 2rem; font-weight: 700; margin: 0.5rem 0; color: #991b1b;">
                    {format_currency(totals["net"])}
                </p>
            </div>
            """, unsafe_allow_html=True)

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #475569; padding: 1rem 0;">
    <p style="margin: 0; font-size: 0.9rem; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);">
        Built with Streamlit | RubyEstimator v1.0
    </p>
</div>
""", unsafe_allow_html=True)

# --- Initial Setup ---
if 'db_created' not in st.session_state:
    create_database()
    st.session_state['db_created'] = True
