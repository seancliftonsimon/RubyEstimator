import streamlit as st
import pandas as pd
from vehicle_data import process_vehicle, get_last_ten_entries
from auth import setup_password_protection
from database_config import test_database_connection, get_database_info

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
def compute_commodities(cars, curb_weight, aluminum_engine=None, aluminum_rims=None):
    """Compute all commodity weights, prices, and sale values."""
    w = lambda lbs: cars * lbs
    
    # Calculate engine weight as a percentage of curb weight
    # Engine weight estimate: 13.9% of curb weight
    # Based on typical engine weights: 4-cyl (300-400 lbs), V6 (400-500 lbs), V8 (500-700 lbs)
    engine_weight_percentage = 0.139
    total_engine_weight = curb_weight * engine_weight_percentage
    
    # Determine engine type based on aluminum_engine parameter
    if aluminum_engine is True:
        # All aluminum engines
        engine_commodities = [
            {"key": "AL_ENGINE", "label": "Aluminum Engine Block", "weight": w(total_engine_weight), "unit_price": PRICE_PER_LB["AL_ENGINE"], "sale_value": 0},
            {"key": "FE_ENGINE", "label": "Iron Engine Block", "weight": 0, "unit_price": PRICE_PER_LB["FE_ENGINE"], "sale_value": 0},
        ]
    elif aluminum_engine is False:
        # All iron engines
        engine_commodities = [
            {"key": "AL_ENGINE", "label": "Aluminum Engine Block", "weight": 0, "unit_price": PRICE_PER_LB["AL_ENGINE"], "sale_value": 0},
            {"key": "FE_ENGINE", "label": "Iron Engine Block", "weight": w(total_engine_weight), "unit_price": PRICE_PER_LB["FE_ENGINE"], "sale_value": 0},
        ]
    else:
        # Unknown engine type - use default split (50/50)
        # For unknown engines, use 275 lbs each as the average split
        engine_commodities = [
            {"key": "AL_ENGINE", "label": "Aluminum Engine Block", "weight": w(275), "unit_price": PRICE_PER_LB["AL_ENGINE"], "sale_value": 0},
            {"key": "FE_ENGINE", "label": "Iron Engine Block", "weight": w(275), "unit_price": PRICE_PER_LB["FE_ENGINE"], "sale_value": 0},
        ]
    
    # Determine rims type based on aluminum_rims parameter
    if aluminum_rims is True:
        # All aluminum rims
        rims_weight = w(4)
    elif aluminum_rims is False:
        # Steel rims - no aluminum rims value
        rims_weight = 0
    else:
        # Unknown rims type - use default
        rims_weight = w(2)
    
    list_commodities = engine_commodities + [
        {"key": "HARNESS", "label": "Wiring Harness", "weight": w(23), "unit_price": PRICE_PER_LB["HARNESS"], "sale_value": 0},
        {"key": "FE_RAD", "label": "Iron Radiator", "weight": w(18), "unit_price": PRICE_PER_LB["FE_RAD"], "sale_value": 0},
        {"key": "BREAKAGE", "label": "Breakage", "weight": w(15), "unit_price": PRICE_PER_LB["BREAKAGE"], "sale_value": 0},
        {"key": "ALT", "label": "Alternator", "weight": w(12), "unit_price": PRICE_PER_LB["ALT"], "sale_value": 0},
        {"key": "STARTER", "label": "Starter Motor", "weight": w(8), "unit_price": PRICE_PER_LB["STARTER"], "sale_value": 0},
        {"key": "AC_COMP", "label": "AC Compressor", "weight": w(7), "unit_price": PRICE_PER_LB["AC_COMP"], "sale_value": 0},
        {"key": "FUSE_BOX", "label": "Fuse Box", "weight": w(6), "unit_price": PRICE_PER_LB["FUSE_BOX"], "sale_value": 0},
        {"key": "BATTERY", "label": "Battery", "weight": w(5), "unit_price": PRICE_PER_LB["BATTERY"], "sale_value": 0},
        {"key": "AL_RIMS", "label": "Aluminum Rims", "weight": rims_weight, "unit_price": PRICE_PER_LB["AL_RIMS"], "sale_value": 0},
        {"key": "CATS", "label": "Catalytic Converters", "weight": w(3), "unit_price": PRICE_PER_LB["CATS"], "sale_value": 0},
        {"key": "ECM", "label": "Engine Control Module", "weight": w(2), "unit_price": PRICE_PER_LB["ECM"], "sale_value": 0},
    ]

    # Calculate ELV weight (curb weight minus engine weights)
    al_engine_w = engine_commodities[0]["weight"]  # AL_ENGINE weight
    fe_engine_w = engine_commodities[1]["weight"]  # FE_ENGINE weight
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
    """Format amount as currency with proper rounding."""
    return f"${round(amount, 2):,.2f}"

# --- Streamlit App ---

# Configure page with light mode styling
st.set_page_config(
    page_title="Ruby GEM - Vehicle Weight & Cost Calculator",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "Ruby GEM - Vehicle Weight & Cost Calculator"
    }
)

# Check password protection
if not setup_password_protection():
    st.stop()

# Custom CSS for light theme with ruby and teal accents
st.markdown("""
<style>
    /* Global background and text colors - Light Mode */
    .main {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 50%, #e2e8f0 100%);
        color: #1e293b;
    }
    
    /* Main title styling */
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1.5rem;
        color: #dc2626;
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
        background: rgba(255, 255, 255, 0.95);
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
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid rgba(220, 38, 38, 0.2);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
    }
    
    /* Enhanced input field styling */
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.95) !important;
        border: 1px solid rgba(220, 38, 38, 0.3) !important;
        border-radius: 6px;
        padding: 0.75rem;
        transition: all 0.2s ease;
        color: #1e293b !important;
    }
    
    .stNumberInput > div > div > input {
        background: rgba(127, 29, 29, 0.9) !important;
        border: 1px solid rgba(220, 38, 38, 0.5) !important;
        border-radius: 6px;
        padding: 0.75rem;
        transition: all 0.2s ease;
        color: #ffffff !important;
    }
    
    /* Style number input buttons (plus/minus) */
    .stNumberInput > div > div > div > button {
        background: rgba(127, 29, 29, 0.9) !important;
        color: #ffffff !important;
        border: 1px solid rgba(220, 38, 38, 0.5) !important;
    }
    
    .stNumberInput > div > div > div > button:hover {
        background: rgba(127, 29, 29, 1) !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #dc2626 !important;
        box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.2) !important;
        outline: none;
        background: rgba(255, 255, 255, 1) !important;
    }
    
    .stNumberInput > div > div > input:focus {
        border-color: #dc2626 !important;
        box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.3) !important;
        outline: none;
        background: rgba(127, 29, 29, 1) !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: rgba(71, 85, 105, 0.6) !important;
    }
    
                   /* Button styling */
      .stButton > button {
          background: rgba(20, 184, 166, 0.9) !important;
          color: #ffffff !important;
          border: 2px solid rgba(20, 184, 166, 0.8) !important;
          border-radius: 8px;
          padding: 0.75rem 1.5rem;
          font-weight: 700;
          font-size: 1rem;
          transition: all 0.2s ease;
          box-shadow: 0 4px 12px rgba(20, 184, 166, 0.4);
          text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
      }
      
      .stButton > button:hover {
          transform: translateY(-2px);
          box-shadow: 0 6px 20px rgba(20, 184, 166, 0.5);
          background: rgba(20, 184, 166, 1) !important;
          color: #ffffff !important;
          border-color: rgba(20, 184, 166, 1) !important;
      }
      
      .stButton > button:active {
          background: rgba(15, 118, 110, 1) !important;
          transform: translateY(0);
          box-shadow: 0 2px 8px rgba(15, 118, 110, 0.5);
          border-color: rgba(15, 118, 110, 1) !important;
      }
    
    /* Dataframe styling - Light Mode */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        background: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(10px);
    }
    
    .dataframe th {
        background: rgba(127, 29, 29, 0.9) !important;
        color: #ffffff !important;
        font-weight: 600;
        border-color: rgba(220, 38, 38, 0.5) !important;
    }
    
    .dataframe td {
        background: rgba(255, 255, 255, 0.9) !important;
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
    
    /* Add padding and spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
        max-width: 1400px;
        margin: 0 auto;
    }
    
    /* Add spacing between columns */
    .row-widget.stHorizontal > div {
        margin: 0 1rem;
    }
    
    /* Add some breathing room between sections */
    .main .block-container > div {
        margin-bottom: 2rem;
    }
    
    /* Streamlit metric containers */
    .stMetric {
        background: rgba(255, 255, 255, 0.95);
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
    
    /* Override Streamlit's default dark theme elements */
    .stApp {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 50%, #e2e8f0 100%);
    }
    
    /* Force light mode */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 50%, #e2e8f0 100%) !important;
    }
    
    /* Add subtle spacing to form elements */
    .stForm > div {
        margin-bottom: 1rem;
    }
    
    /* Improve spacing for expanders */
    .streamlit-expanderHeader {
        margin-bottom: 0.5rem;
    }
    
    /* Ensure all Streamlit elements have proper light mode styling */
    .stSelectbox > div > div > div {
        background: rgba(127, 29, 29, 0.9) !important;
        color: #ffffff !important;
        border: 1px solid rgba(220, 38, 38, 0.5) !important;
        border-radius: 6px;
    }
    
    .stSelectbox > div > div > div > div {
        color: #ffffff !important;
    }
    
    /* Style dropdown options */
    .stSelectbox > div > div > div[data-baseweb="select"] {
        background: rgba(127, 29, 29, 0.9) !important;
    }
    
    /* Style the dropdown arrow */
    .stSelectbox > div > div > div > div[data-baseweb="select-arrow"] {
        color: #ffffff !important;
    }
    
         /* Override any remaining dark gray elements */
     .stNumberInput, .stSelectbox, .stButton {
         color: #ffffff !important;
     }
     
     /* Force ruby color on all interactive elements */
     .stNumberInput > div, .stSelectbox > div, .stButton > div {
         background: rgba(127, 29, 29, 0.9) !important;
     }
     
           /* Additional comprehensive overrides for all dark gray elements */
      .stNumberInput > div > div > div > button,
      .stNumberInput > div > div > div > div,
      .stSelectbox > div > div > div > div,
      .stSelectbox > div > div > div > div > div {
          background: rgba(127, 29, 29, 0.9) !important;
          color: #ffffff !important;
          border-color: rgba(220, 38, 38, 0.5) !important;
      }
      
      /* Buttons should use teal styling, not ruby */
      .stButton > div > button,
      .stButton > div > div {
          background: rgba(20, 184, 166, 0.9) !important;
          color: #ffffff !important;
          border-color: rgba(20, 184, 166, 0.8) !important;
      }
     
           /* Override all possible Streamlit dark elements */
      [data-testid="stNumberInput"] > div > div > div > button,
      [data-testid="stSelectbox"] > div > div > div {
          background: rgba(127, 29, 29, 0.9) !important;
          color: #ffffff !important;
      }
      
      /* Buttons should use teal styling */
      [data-testid="stButton"] > div > button {
          background: rgba(20, 184, 166, 0.9) !important;
          color: #ffffff !important;
      }
     
     /* Force ruby color on table headers */
     .dataframe thead th,
     .dataframe th,
     table th {
         background: rgba(127, 29, 29, 0.9) !important;
         color: #ffffff !important;
         border-color: rgba(220, 38, 38, 0.5) !important;
     }
     
           /* Override any remaining dark backgrounds - but be more specific */
      .stNumberInput > div > div > div > button,
      .stNumberInput > div > div > div > div[data-baseweb="select"],
      .stSelectbox > div > div > div > div[data-baseweb="select"] {
          background: rgba(127, 29, 29, 0.9) !important;
          color: #ffffff !important;
      }
      
      /* Buttons should use teal styling */
      .stButton > div > button {
          background: rgba(20, 184, 166, 0.9) !important;
          color: #ffffff !important;
      }
     
     /* Keep labels and text elements with proper styling */
     .stNumberInput > div > label,
     .stSelectbox > div > label,
     .stButton > div > label,
     .stTextInput > div > label {
         background: transparent !important;
         color: #475569 !important;
         font-weight: 500;
     }
     
     /* Exception for text inputs - keep them white */
     .stTextInput > div > div > input {
         background: rgba(255, 255, 255, 0.95) !important;
         color: #1e293b !important;
     }
    
    /* Style info messages */
    .stAlert {
        background: rgba(255, 255, 255, 0.95) !important;
        color: #1e293b !important;
        border: 1px solid rgba(220, 38, 38, 0.2) !important;
    }
    
         /* Style spinner */
     .stSpinner > div {
         color: #dc2626 !important;
     }
     
     /* FORCE BUTTON STYLING - Override everything else */
     button[data-testid="baseButton-primary"],
     button[data-testid="baseButton-secondary"],
     .stButton > button,
     .stButton > div > button,
     .stButton > div > div > button,
     [data-testid="stButton"] > div > button,
     [data-testid="stButton"] > div > div > button,
     /* Additional ultra-specific selectors */
     .stButton button,
     .stButton div button,
     .stButton div div button,
     .stButton div div div button,
     .stButton div div div div button,
     /* Streamlit form button selectors */
     .stForm button,
     .stForm div button,
     .stForm div div button,
     .stForm div div div button,
     /* Any button within Streamlit containers */
     .block-container button,
     .main button,
     /* Universal button override for Streamlit */
     button[class*="stButton"],
     button[class*="baseButton"] {
         background: rgba(20, 184, 166, 0.9) !important;
         color: #ffffff !important;
         border: 2px solid rgba(20, 184, 166, 0.8) !important;
         border-radius: 8px !important;
         padding: 0.75rem 1.5rem !important;
         font-weight: 700 !important;
         font-size: 1rem !important;
         transition: all 0.2s ease !important;
         box-shadow: 0 4px 12px rgba(20, 184, 166, 0.4) !important;
         text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1) !important;
     }
     
     /* Force button hover states */
     button[data-testid="baseButton-primary"]:hover,
     button[data-testid="baseButton-secondary"]:hover,
     .stButton > button:hover,
     .stButton > div > button:hover,
     .stButton > div > div > button:hover,
     [data-testid="stButton"] > div > button:hover,
     [data-testid="stButton"] > div > div > button:hover,
     /* Additional ultra-specific hover selectors */
     .stButton button:hover,
     .stButton div button:hover,
     .stButton div div button:hover,
     .stButton div div div button:hover,
     .stButton div div div div button:hover,
     /* Streamlit form button hover selectors */
     .stForm button:hover,
     .stForm div button:hover,
     .stForm div div button:hover,
     .stForm div div div button:hover,
     /* Any button within Streamlit containers */
     .block-container button:hover,
     .main button:hover,
     /* Universal button hover override for Streamlit */
     button[class*="stButton"]:hover,
     button[class*="baseButton"]:hover {
         transform: translateY(-2px) !important;
         box-shadow: 0 6px 20px rgba(20, 184, 166, 0.5) !important;
         background: rgba(20, 184, 166, 1) !important;
         color: #ffffff !important;
         border-color: rgba(20, 184, 166, 1) !important;
     }
     
     /* Force button active states */
     button[data-testid="baseButton-primary"]:active,
     button[data-testid="baseButton-secondary"]:active,
     .stButton > button:active,
     .stButton > div > button:active,
     .stButton > div > div > button:active,
     [data-testid="stButton"] > div > button:active,
     [data-testid="stButton"] > div > div > button:active,
     /* Additional ultra-specific active selectors */
     .stButton button:active,
     .stButton div button:active,
     .stButton div div button:active,
     .stButton div div div button:active,
     .stButton div div div div button:active,
     /* Streamlit form button active selectors */
     .stForm button:active,
     .stForm div button:active,
     .stForm div div button:active,
     .stForm div div div button:active,
     /* Any button within Streamlit containers */
     .block-container button:active,
     .main button:active,
     /* Universal button active override for Streamlit */
     button[class*="stButton"]:active,
     button[class*="baseButton"]:active {
         background: rgba(15, 118, 110, 1) !important;
         transform: translateY(0) !important;
         box-shadow: 0 2px 8px rgba(15, 118, 110, 0.5) !important;
         border-color: rgba(15, 118, 110, 1) !important;
     }
</style>
""", unsafe_allow_html=True)

# Main title with ruby gradient effect
st.markdown('<h1 class="main-title">🚗 Ruby GEM</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #475569; font-size: 1.1rem; margin-bottom: 2rem; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);">Vehicle Weight Estimator & Cost Calculator</p>', unsafe_allow_html=True)

# Create two columns for the main layout with spacing
left_col, spacer, right_col = st.columns([1, 0.1, 1])

# --- Left Column: Vehicle Search & Recent Entries ---
with left_col:
    st.markdown("""
    <h2 class="section-header">
        Vehicle Search & Estimator
        <div class="info-icon-container">
            <span class="info-icon" title="Search for vehicle details to get curb weight and specifications, then calculate costs automatically.">ⓘ</span>
        </div>
    </h2>
    """, unsafe_allow_html=True)

    # --- Main Form ---
    with st.form(key="vehicle_form"):
        st.markdown('<h3 class="subsection-header">Look Up Vehicle</h3>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            year_input = st.text_input("Year", placeholder="e.g., 2013", value="2013")
        with col2:
            make_input = st.text_input("Make", placeholder="e.g., Toyota", value="Toyota")
        with col3:
            model_input = st.text_input("Model", placeholder="e.g., Camry", value="Camry")

        submit_button = st.form_submit_button(label="Search Vehicle & Calculate", use_container_width=True)

    # --- Processing and Output ---
    if submit_button:
        if not make_input or not model_input:
            st.markdown("""
            <div class="warning-message">
                <strong>Missing Information:</strong> Please enter both a make and a model.
            </div>
            """, unsafe_allow_html=True)
        else:
            # Convert year to integer and validate
            try:
                year_int = int(year_input.strip())
                if year_int < 1900 or year_int > 2050:
                    st.markdown("""
                    <div class="warning-message">
                        <strong>Invalid Year:</strong> Please enter a year between 1900 and 2050.
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    with st.spinner(f"Searching for {year_int} {make_input} {model_input}..."):
                        vehicle_data = process_vehicle(year_int, make_input.strip(), model_input.strip())
                    
                    if vehicle_data and vehicle_data['curb_weight_lbs']:
                        # Display simple success message
                        st.markdown(f"""
                        <div class="success-message">
                            <strong>Vehicle Found!</strong> {year_int} {make_input} {model_input}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Store the detailed vehicle info for display on the right
                        st.session_state['detailed_vehicle_info'] = {
                            'year': year_int,
                            'make': make_input,
                            'model': model_input,
                            'weight': vehicle_data['curb_weight_lbs'],
                            'aluminum_engine': vehicle_data['aluminum_engine'],
                            'aluminum_rims': vehicle_data['aluminum_rims']
                        }
                        
                        # Store the data in session state for the cost estimator
                        st.session_state['last_curb_weight'] = vehicle_data['curb_weight_lbs']
                        st.session_state['last_aluminum_engine'] = vehicle_data['aluminum_engine']
                        st.session_state['last_aluminum_rims'] = vehicle_data['aluminum_rims']
                        st.session_state['last_vehicle_info'] = f"{year_int} {make_input} {model_input}"
                        
                        # Auto-populate and calculate the cost estimator
                        st.session_state['auto_calculate'] = True
                    else:
                        st.markdown("""
                        <div class="error-message">
                            <strong>Weight Not Found:</strong> Could not determine the curb weight. 
                            The result has been stored as 'Inconclusive' to prevent repeated searches.
                        </div>
                        """, unsafe_allow_html=True)
            except ValueError:
                st.markdown("""
                <div class="warning-message">
                    <strong>Invalid Year:</strong> Please enter a valid year (e.g., 2023).
                </div>
                """, unsafe_allow_html=True)

    # --- Display Recent Entries (Minimized) ---
    with st.expander("📋 Recently Searched Vehicles (Last 5)", expanded=False):
        try:
            recent_entries_df = get_last_ten_entries()
            if not recent_entries_df.empty:
                # Take only the last 5 entries
                recent_entries_df = recent_entries_df.head(5)
                
                # Format the aluminum columns for better display
                def format_aluminum(value):
                    if value is None:
                        return "?"
                    elif value:
                        return "Al"
                    else:
                        return "Fe/St"
                
                # Create a copy for display with formatted columns
                display_df = recent_entries_df.copy()
                display_df['E'] = display_df['aluminum_engine'].apply(format_aluminum)
                display_df['W'] = display_df['aluminum_rims'].apply(format_aluminum)
                
                # Select and rename columns for display (more compact)
                display_df = display_df[['year', 'make', 'model', 'curb_weight_lbs', 'E', 'W']]
                display_df.columns = ['Year', 'Make', 'Model', 'Weight', 'E', 'W']
                
                # Style the dataframe
                styled_df = display_df.style.set_properties(**{
                    'background-color': 'rgba(255, 255, 255, 0.95)',
                    'color': '#1e293b',
                    'border-color': 'rgba(220, 38, 38, 0.1)',
                    'font-size': '0.8rem'
                }).format({'Weight': '{:,.0f}'})
                
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
                st.caption("E = Engine (Al=Aluminum, Fe=Iron), W = Wheels (Al=Aluminum, St=Steel)")
            else:
                st.info("No vehicles searched yet.")
        except Exception as e:
            st.error(f"Error fetching recent entries: {e}")

# --- Right Column: Cost Estimator Results ---
with right_col:
    # Dynamic header based on vehicle info
    if 'detailed_vehicle_info' in st.session_state:
        vehicle_info = st.session_state['detailed_vehicle_info']
        vehicle_name = f"{vehicle_info['year']} {vehicle_info['make']} {vehicle_info['model']}"
        header_text = vehicle_name
    else:
        header_text = "Cost Estimate Results"
    
    st.markdown(f"""
    <h2 class="section-header">
        {header_text}
        <div class="info-icon-container">
            <span class="info-icon" title="Automatically calculated commodity weights, sale values, costs, and net profit based on the searched vehicle.">ⓘ</span>
        </div>
    </h2>
    """, unsafe_allow_html=True)
    
    # Auto-calculate if vehicle was just searched
    if st.session_state.get('auto_calculate', False):
        # Clear the auto_calculate flag
        st.session_state['auto_calculate'] = False
        
        # Store calculation results in session state for display
        try:
            cars_int = 1  # Default to 1 car
            curb_weight_int = st.session_state.get('last_curb_weight', 3600)
            
            # Convert selectbox values to boolean/None for the function
            aluminum_engine = None
            last_aluminum_engine = st.session_state.get('last_aluminum_engine')
            if last_aluminum_engine is True or last_aluminum_engine == 1:
                aluminum_engine = True
            elif last_aluminum_engine is False or last_aluminum_engine == 0:
                aluminum_engine = False
            
            aluminum_rims = None
            last_aluminum_rims = st.session_state.get('last_aluminum_rims')
            if last_aluminum_rims is True or last_aluminum_rims == 1:
                aluminum_rims = True
            elif last_aluminum_rims is False or last_aluminum_rims == 0:
                aluminum_rims = False
            
            # Perform the calculation
            commodities = compute_commodities(cars_int, curb_weight_int, aluminum_engine, aluminum_rims)
            totals = calculate_totals(commodities, cars_int, curb_weight_int)
            
            # Store results in session state
            st.session_state['calculation_results'] = {
                'commodities': commodities,
                'totals': totals,
                'cars': cars_int,
                'curb_weight': curb_weight_int
            }
            
        except Exception as e:
            st.error(f"Error during auto-calculation: {e}")
    
    # Show a message when no vehicle has been searched yet
    if st.session_state.get('last_curb_weight') is None:
        st.markdown("""
        <div style="background: rgba(156, 163, 175, 0.1); padding: 2rem; border-radius: 8px; text-align: center; border: 1px solid #9ca3af;">
            <h3 style="color: #6b7280; margin-bottom: 1rem;">Search for a vehicle to see value estimate</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Show manual entry option when no vehicle is selected
        with st.expander("❓ Unknown make/model? Enter curb weight manually", expanded=False):
            with st.form(key="manual_calc_form_no_vehicle"):
                col1, col2 = st.columns(2)
                with col1:
                    cars_input = st.text_input("Number of Cars", placeholder="e.g., 1", value="1", key="cars_no_vehicle")
                with col2:
                    curb_weight_input = st.text_input("Combined Curb Weight (lb)", placeholder="e.g., 3600", value="3600", key="weight_no_vehicle")
                
                # Engine and Rims Type Selection
                col1, col2 = st.columns(2)
                with col1:
                    engine_type = st.selectbox(
                        "Engine Block Type",
                        options=["Unknown", "Aluminum", "Iron"],
                        index=0,
                        key="engine_no_vehicle"
                    )
                with col2:
                    rims_type = st.selectbox(
                        "Wheels/Rims Type",
                        options=["Unknown", "Aluminum", "Steel"],
                        index=0,
                        key="rims_no_vehicle"
                    )
                
                manual_calculate_button = st.form_submit_button(label="Calculate Estimate", use_container_width=True)
                
                # Handle manual calculation
                if manual_calculate_button:
                    try:
                        cars_int = int(cars_input.strip())
                        curb_weight_int = int(curb_weight_input.strip())
                        
                        # Convert selectbox values to boolean/None for the function
                        aluminum_engine = None
                        if engine_type == "Aluminum":
                            aluminum_engine = True
                        elif engine_type == "Iron":
                            aluminum_engine = False
                        
                        aluminum_rims = None
                        if rims_type == "Aluminum":
                            aluminum_rims = True
                        elif rims_type == "Steel":
                            aluminum_rims = False
                        
                        # Perform the calculation
                        commodities = compute_commodities(cars_int, curb_weight_int, aluminum_engine, aluminum_rims)
                        totals = calculate_totals(commodities, cars_int, curb_weight_int)
                        
                        # Store results in session state
                        st.session_state['calculation_results'] = {
                            'commodities': commodities,
                            'totals': totals,
                            'cars': cars_int,
                            'curb_weight': curb_weight_int
                        }
                        
                        # Update session state with new values
                        st.session_state['last_curb_weight'] = curb_weight_int
                        st.session_state['last_aluminum_engine'] = aluminum_engine
                        st.session_state['last_aluminum_rims'] = aluminum_rims
                        st.session_state['last_vehicle_info'] = f"Manual Entry ({curb_weight_int} lbs)"
                        
                        # Create detailed vehicle info for display
                        st.session_state['detailed_vehicle_info'] = {
                            'year': 'Manual',
                            'make': 'Entry',
                            'model': f'{curb_weight_int} lbs',
                            'weight': curb_weight_int,
                            'aluminum_engine': aluminum_engine,
                            'aluminum_rims': aluminum_rims
                        }
                        
                        st.success("Manual estimate calculated!")
                        st.rerun()
                        
                    except ValueError:
                        st.error("Please enter valid numbers for cars and curb weight.")
                    except Exception as e:
                        st.error(f"Error during calculation: {e}")
    else:
        # Display the current vehicle info with detailed styling
        if 'detailed_vehicle_info' in st.session_state:
            vehicle_info = st.session_state['detailed_vehicle_info']
            
            # Display curb weight, engine, and rims info in three side-by-side boxes
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div style="background: rgba(34, 197, 94, 0.1); padding: 0.5rem; border-radius: 6px; margin: 0.25rem 0; border-left: 3px solid #22c55e;">
                    <strong>Weight:</strong> <span style="color: #22c55e; font-weight: 600;">{vehicle_info['weight']} lbs</span>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if vehicle_info['aluminum_engine'] is not None:
                    engine_status = "Aluminum" if vehicle_info['aluminum_engine'] else "Iron"
                    engine_color = "#22c55e" if vehicle_info['aluminum_engine'] else "#f59e0b"
                    st.markdown(f"""
                    <div style="background: rgba(34, 197, 94, 0.1); padding: 0.5rem; border-radius: 6px; margin: 0.25rem 0; border-left: 3px solid {engine_color};">
                        <strong>Engine:</strong> <span style="color: {engine_color}; font-weight: 600;">{engine_status}</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background: rgba(156, 163, 175, 0.1); padding: 0.5rem; border-radius: 6px; margin: 0.25rem 0; border-left: 3px solid #9ca3af;">
                        <strong>Engine:</strong> <span style="color: #6b7280;">Unknown</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col3:
                if vehicle_info['aluminum_rims'] is not None:
                    rims_status = "Aluminum" if vehicle_info['aluminum_rims'] else "Steel"
                    rims_color = "#22c55e" if vehicle_info['aluminum_rims'] else "#f59e0b"
                    st.markdown(f"""
                    <div style="background: rgba(34, 197, 94, 0.1); padding: 0.5rem; border-radius: 6px; margin: 0.25rem 0; border-left: 3px solid {rims_color};">
                        <strong>Rims:</strong> <span style="color: {rims_color}; font-weight: 600;">{rims_status}</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background: rgba(156, 163, 175, 0.1); padding: 0.5rem; border-radius: 6px; margin: 0.25rem 0; border-left: 3px solid #9ca3af;">
                        <strong>Rims:</strong> <span style="color: #6b7280;">Unknown</span>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            # Fallback to simple display if no detailed info
            vehicle_name = st.session_state.get('last_vehicle_info', 'Unknown Vehicle')
            vehicle_info = f"""
            <div style="background: rgba(20, 184, 166, 0.1); padding: 1rem; border-radius: 8px; border: 1px solid #14b8a6; margin-bottom: 1rem;">
                <h4 style="margin: 0; color: #0f766e;">Current Vehicle</h4>
                <p style="margin: 0.5rem 0; color: #0f766e;">
                    <strong>{vehicle_name}</strong>
                </p>
                <p style="margin: 0.5rem 0; color: #0f766e;">
                    Weight: <strong>{st.session_state['last_curb_weight']} lbs</strong>
                </p>
            """
            
            # Add engine and rims info if available
            if 'last_aluminum_engine' in st.session_state and st.session_state['last_aluminum_engine'] is not None:
                engine_status = "Aluminum" if st.session_state['last_aluminum_engine'] else "Iron"
                vehicle_info += f'<p style="margin: 0.25rem 0; color: #0f766e;">Engine: <strong>{engine_status}</strong></p>'
            
            if 'last_aluminum_rims' in st.session_state and st.session_state['last_aluminum_rims'] is not None:
                rims_status = "Aluminum" if st.session_state['last_aluminum_rims'] else "Steel"
                vehicle_info += f'<p style="margin: 0.25rem 0; color: #0f766e;">Wheels: <strong>{rims_status}</strong></p>'
            
            vehicle_info += '</div>'
            st.markdown(vehicle_info, unsafe_allow_html=True)
        

        
        # Calculate and display results if vehicle is selected
        if st.session_state.get('last_curb_weight') is not None:
            # If no calculation results yet, calculate them
            if 'calculation_results' not in st.session_state:
                try:
                    cars_int = 1  # Default to 1 car
                    curb_weight_int = st.session_state.get('last_curb_weight', 3600)
                    
                    # Convert session state values to boolean/None for the function
                    aluminum_engine = None
                    last_aluminum_engine = st.session_state.get('last_aluminum_engine')
                    if last_aluminum_engine is True or last_aluminum_engine == 1:
                        aluminum_engine = True
                    elif last_aluminum_engine is False or last_aluminum_engine == 0:
                        aluminum_engine = False
                    
                    aluminum_rims = None
                    last_aluminum_rims = st.session_state.get('last_aluminum_rims')
                    if last_aluminum_rims is True or last_aluminum_rims == 1:
                        aluminum_rims = True
                    elif last_aluminum_rims is False or last_aluminum_rims == 0:
                        aluminum_rims = False
                    
                    # Perform the calculation
                    commodities = compute_commodities(cars_int, curb_weight_int, aluminum_engine, aluminum_rims)
                    totals = calculate_totals(commodities, cars_int, curb_weight_int)
                    
                    # Store results in session state
                    st.session_state['calculation_results'] = {
                        'commodities': commodities,
                        'totals': totals,
                        'cars': cars_int,
                        'curb_weight': curb_weight_int
                    }
                except Exception as e:
                    st.error(f"Error during calculation: {e}")
                    st.stop()
            
            # Display calculation results
            results = st.session_state['calculation_results']
            commodities = results['commodities']
            totals = results['totals']
            
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
            
            # Disclaimer about estimates and accuracy
            st.markdown("""
            <div style="background: rgba(245, 158, 11, 0.1); padding: 1rem; border-radius: 8px; margin: 1rem 0; border-left: 4px solid #f59e0b;">
                <p style="margin: 0; color: #92400e; font-size: 0.9rem; line-height: 1.4;">
                    <strong>Disclaimer:</strong> Information is an estimate from AI search. Double-check numbers that don't look right.
                </p>
                <p style="margin: 0.5rem 0 0 0; color: #92400e; font-size: 0.9rem; line-height: 1.4;">
                    <strong>🔧 Catalytic Converter:</strong> Costs still being factored in. Current figures are not accurate.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Create DataFrame for better display
            commodity_data = []
            for commodity in commodities:
                commodity_data.append({
                    "Commodity": commodity["label"],
                    "Weight (lb)": commodity['weight'],
                    "$/lb": commodity['unit_price'],
                    "Sale Value": commodity["sale_value"]
                })
            
            commodity_df = pd.DataFrame(commodity_data)
            
            # Style the commodity dataframe
            styled_commodity_df = commodity_df.style.set_properties(**{
                'background-color': 'rgba(255, 255, 255, 0.95)',
                'color': '#1e293b',
                'border-color': 'rgba(220, 38, 38, 0.1)'
            }).format({
                'Weight (lb)': '{:,.1f}',
                '$/lb': '{:.2f}',
                'Sale Value': '{:.2f}'
            })
            
            st.dataframe(styled_commodity_df, use_container_width=True, hide_index=True)
            
            # Add note about engine weight estimation
            st.markdown("""
            <div style="background: rgba(156, 163, 175, 0.1); padding: 0.75rem; border-radius: 6px; margin: 0.5rem 0; border-left: 3px solid #9ca3af;">
                <p style="margin: 0; color: #6b7280; font-size: 0.875rem;">
                    <strong>Note:</strong> Engine weight estimated at 13.9% of curb weight based on typical engine weights: 
                    4-cylinder (300-400 lbs), V6 (400-500 lbs), V8 (500-700 lbs). 
                    For unknown engine materials, using conservative estimate of 275 lbs each.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
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
                'background-color': 'rgba(255, 255, 255, 0.95)',
                'color': '#1e293b',
                'border-color': 'rgba(220, 38, 38, 0.1)'
            })
            
            st.dataframe(styled_summary_df, use_container_width=True, hide_index=True)
            

        
        # Manual calculation form at the bottom when results are displayed
        with st.expander("❓ Unknown make/model? Enter curb weight manually", expanded=False):
            with st.form(key="manual_calc_form_with_vehicle"):
                col1, col2 = st.columns(2)
                with col1:
                    cars_input = st.text_input("Number of Cars", placeholder="e.g., 1", value="1", key="cars_with_vehicle")
                with col2:
                    curb_weight_input = st.text_input("Combined Curb Weight (lb)", placeholder="e.g., 3600", value=str(st.session_state.get('last_curb_weight', 3600)), key="weight_with_vehicle")
                
                # Engine and Rims Type Selection
                col1, col2 = st.columns(2)
                with col1:
                    default_engine = "Unknown"
                    if 'last_aluminum_engine' in st.session_state and st.session_state['last_aluminum_engine'] is not None:
                        default_engine = "Aluminum" if st.session_state['last_aluminum_engine'] else "Iron"
                    
                    engine_type = st.selectbox(
                        "Engine Block Type",
                        options=["Unknown", "Aluminum", "Iron"],
                        index=["Unknown", "Aluminum", "Iron"].index(default_engine),
                        key="engine_with_vehicle"
                    )
                with col2:
                    default_rims = "Unknown"
                    if 'last_aluminum_rims' in st.session_state and st.session_state['last_aluminum_rims'] is not None:
                        default_rims = "Aluminum" if st.session_state['last_aluminum_rims'] else "Steel"
                    
                    rims_type = st.selectbox(
                        "Wheels/Rims Type",
                        options=["Unknown", "Aluminum", "Steel"],
                        index=["Unknown", "Aluminum", "Steel"].index(default_rims),
                        key="rims_with_vehicle"
                    )
                
                manual_calculate_button = st.form_submit_button(label="Recalculate", use_container_width=True)
                
                # Handle manual calculation
                if manual_calculate_button:
                    try:
                        cars_int = int(cars_input.strip())
                        curb_weight_int = int(curb_weight_input.strip())
                        
                        # Convert selectbox values to boolean/None for the function
                        aluminum_engine = None
                        if engine_type == "Aluminum":
                            aluminum_engine = True
                        elif engine_type == "Iron":
                            aluminum_engine = False
                        
                        aluminum_rims = None
                        if rims_type == "Aluminum":
                            aluminum_rims = True
                        elif rims_type == "Steel":
                            aluminum_rims = False
                        
                        # Perform the calculation
                        commodities = compute_commodities(cars_int, curb_weight_int, aluminum_engine, aluminum_rims)
                        totals = calculate_totals(commodities, cars_int, curb_weight_int)
                        
                        # Store results in session state
                        st.session_state['calculation_results'] = {
                            'commodities': commodities,
                            'totals': totals,
                            'cars': cars_int,
                            'curb_weight': curb_weight_int
                        }
                        
                        # Update session state with new values
                        st.session_state['last_curb_weight'] = curb_weight_int
                        st.session_state['last_aluminum_engine'] = aluminum_engine
                        st.session_state['last_aluminum_rims'] = aluminum_rims
                        
                    except ValueError:
                        st.error("Please enter valid numbers for cars and curb weight.")
                    except Exception as e:
                        st.error(f"Error during calculation: {e}")
    

    


# --- Footer ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #475569; padding: 1rem 0;">
    <p style="margin: 0; font-size: 0.9rem; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);">
        Built with Streamlit | Ruby GEM v1.0
    </p>
</div>
""", unsafe_allow_html=True)

# --- Initial Setup ---
if 'db_created' not in st.session_state:
    try:
        # Test database connection
        success, message = test_database_connection()
        if success:
            print("✅ Database connection successful")
            st.session_state['db_created'] = True
        else:
            print(f"❌ Database connection failed: {message}")
            st.error(f"Database connection failed: {message}")
            st.stop()
    except Exception as e:
        print(f"Error during database setup: {e}")
        st.error(f"Database setup error: {e}")
        st.stop()

# Initialize session state variables if they don't exist
if 'last_curb_weight' not in st.session_state:
    st.session_state['last_curb_weight'] = None
if 'last_aluminum_engine' not in st.session_state:
    st.session_state['last_aluminum_engine'] = None
if 'last_aluminum_rims' not in st.session_state:
    st.session_state['last_aluminum_rims'] = None
if 'last_vehicle_info' not in st.session_state:
    st.session_state['last_vehicle_info'] = None
if 'auto_calculate' not in st.session_state:
    st.session_state['auto_calculate'] = False
if 'detailed_vehicle_info' not in st.session_state:
    st.session_state['detailed_vehicle_info'] = None
