import streamlit as st
from dotenv import load_dotenv
import logging
import sys
import re
import time
import html

# Configure logging FIRST (before any other imports that might use logging)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file for local development
load_dotenv()

# Log startup
logger.info("🚀 Ruby GEM Application Starting...")

# Configure page with light mode styling (must be first Streamlit command)
st.set_page_config(
    page_title="Ruby GEM - Vehicle Weight & Cost Calculator",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "Ruby GEM - Vehicle Weight & Cost Calculator"
    }
)

import pandas as pd
from vehicle_data import (
    process_vehicle, get_last_ten_entries,
    suggest_make, suggest_model,
    get_all_makes, get_models_for_make, get_catalog_stats,
    import_catalog_from_json, export_catalog_to_json, invalidate_catalog_cache,
    mark_run_bought,
    get_admin_history,
    get_admin_profit_stats
)
from auth import (
    require_admin_password, 
    clear_admin_auth, 
    render_login_ui, 
    create_user, 
    list_users,
    ensure_admin_user
)
from database_config import test_database_connection, get_database_info, get_app_config, upsert_app_config, create_database_engine
from confidence_ui import (
    render_confidence_badge, render_warning_banner, 
    add_confidence_css
)

from typing import Dict, Any, List, Optional
import os
from styles import generate_main_app_css, generate_admin_mode_css, get_semantic_colors, Colors
from cat_prices import CatPriceManager
from sqlalchemy import text
from datetime import datetime, timedelta

# HTML escape helper for unsafe_allow_html blocks
def _escape_html(value: object) -> str:
    return html.escape(str(value), quote=True)

# --- Streamlit App Styling (must apply before any gated UI, including login) ---
# Add confidence indicator CSS
add_confidence_css()
# Apply main app CSS from centralized styles module
st.markdown(generate_main_app_css(), unsafe_allow_html=True)

# --- Buyer Login Gate ---
# If we are not in admin mode, require buyer login.
if not st.session_state.get("admin_mode", False):
    is_logged_in = render_login_ui(session_key="buyer_user")
    if not is_logged_in:
        st.stop()

# Get current buyer (if any)
current_buyer = st.session_state.get("buyer_user")
current_buyer_id = current_buyer["id"] if current_buyer else None
current_buyer_name = current_buyer["username"] if current_buyer else "guest"

# Default configuration values (used when DB has no overrides)
DEFAULT_PRICE_PER_LB: Dict[str, float] = {
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
    "TIRES": 4.5,
    "ECM": 1.32,
}

DEFAULT_FLAT_COSTS: Dict[str, float] = {
    "PURCHASE": 475.0,
    "TOW": 90.0,
    "LEAD_PER_CAR": 107.5,
    "NUT_PER_LB": 0.015,
}

DEFAULT_WEIGHTS_FIXED: Dict[str, float] = {
    "rims_aluminum_weight_lbs": 40.0,
    "battery_baseline_weight_lbs": 35.0,
    "harness_weight_lbs": 23.0,
    "fe_radiator_weight_lbs": 20.5,
    "breakage_weight_lbs": 5.0,
    "alternator_weight_lbs": 12.0,
    "starter_weight_lbs": 5.5,
    "ac_compressor_weight_lbs": 13.5,
    "fuse_box_weight_lbs": 3.5,
}

DEFAULT_ASSUMPTIONS: Dict[str, float] = {
    "engine_weight_percent_of_curb": 0.139,
    "battery_recovery_factor": 0.8,
    "cats_per_car_default_average": 1.36,
    "unknown_engine_split_aluminum_percent": 0.5,
    # Profit styling threshold (admin-controlled)
    "minimum_goal_profit": 25.0,
}

ADMIN_FIELD_METADATA = {
    # Assumptions
    "engine_weight_percent_of_curb": {
        "label": "Engine Weight % of Curb",
        "helper": "Percentage of total vehicle weight attributed to the engine (e.g., 0.139 = 13.9%).",
        "format": "%.3f"
    },
    "battery_recovery_factor": {
        "label": "Battery Recovery Factor",
        "helper": "Adjustment factor for battery weight recovery (e.g., 0.8 means 80% of baseline weight).",
        "format": "%.2f"
    },
    "cats_per_car_default_average": {
        "label": "Avg. Cats per Car",
        "helper": "Default number of catalytic converters assumed if not specified.",
        "format": "%.2f"
    },
    "minimum_goal_profit": {
        "label": "Minimum Goal Profit ($)",
        "helper": "Profit color floor for estimates. Net profit below this is highlighted as tight margin (yellow).",
        "format": "%.2f",
    },
    "unknown_engine_split_aluminum_percent": {
        "label": "Assumed Aluminum Share (Unknown Engine)",
        "helper": "0.75 means 75% aluminum / 25% iron in the estimate.",
        "format": "%.2f"
    },
    # Prices
    "ELV": {"label": "ELV (End of Life Vehicle)", "helper": "Price per lb for vehicle body scrap."},
    "AL_ENGINE": {"label": "Aluminum Engine", "helper": "Price per lb for aluminum engines."},
    "FE_ENGINE": {"label": "Iron Engine", "helper": "Price per lb for iron engines."},
    "HARNESS": {"label": "Wiring Harness", "helper": "Price per lb for wiring harnesses."},
    "FE_RAD": {"label": "Iron Radiator", "helper": "Price per lb for iron radiators."},
    "BREAKAGE": {"label": "Breakage", "helper": "Price per lb for breakage material."},
    "ALT": {"label": "Alternator", "helper": "Price per lb for alternators."},
    "STARTER": {"label": "Starter", "helper": "Price per lb for starters."},
    "AC_COMP": {"label": "A/C Compressor", "helper": "Price per lb for A/C compressors."},
    "FUSE_BOX": {"label": "Fuse Box", "helper": "Price per lb for fuse boxes."},
    "BATTERY": {"label": "Battery", "helper": "Price per lb for lead-acid batteries."},
    "AL_RIMS": {"label": "Aluminum Rims", "helper": "Price per lb for aluminum rims."},
    "CATS": {"label": "Catalytic Converters (Generic)", "helper": "Price per unit for generic cats (fallback)."},
    "TIRES": {"label": "Tires", "helper": "Price per unit (or lb depending on usage) for tires."},
    "ECM": {"label": "ECM", "helper": "Price per lb for Engine Control Modules."},
    # Costs
    "PURCHASE": {"label": "Flat Purchase Cost", "helper": "Fixed cost deducted per vehicle purchased."},
    "TOW": {"label": "Flat Tow Fee", "helper": "Fixed cost deducted for towing per vehicle."},
    "LEAD_PER_CAR": {"label": "Lead Fee (per car)", "helper": "Fixed environmental fee per car."},
    "NUT_PER_LB": {"label": "Nut Fee (per lb)", "helper": "Processing fee per lb of material."},
    # Weights
    "rims_aluminum_weight_lbs": {"label": "Rims (Aluminum)", "helper": "Assumed total weight of aluminum rims."},
    "battery_baseline_weight_lbs": {"label": "Battery (Baseline)", "helper": "Baseline weight for a car battery."},
    "harness_weight_lbs": {"label": "Wiring Harness", "helper": "Assumed weight of wiring harness."},
    "fe_radiator_weight_lbs": {"label": "Iron Radiator", "helper": "Assumed weight of radiator."},
    "breakage_weight_lbs": {"label": "Breakage", "helper": "Assumed weight of breakage."},
    "alternator_weight_lbs": {"label": "Alternator", "helper": "Assumed weight of alternator."},
    "starter_weight_lbs": {"label": "Starter", "helper": "Assumed weight of starter."},
    "ac_compressor_weight_lbs": {"label": "A/C Compressor", "helper": "Assumed weight of A/C compressor."},
    "fuse_box_weight_lbs": {"label": "Fuse Box", "helper": "Assumed weight of fuse box."},
}

DEFAULT_HEURISTICS: Dict[str, Any] = {
    "performance_indicators": ["gt", "rs", "ss", "amg", "type r", "m3", "m4", "m5", "v8"],
    "v8_keywords": ["v8", "5.0", "6.2"],
    "fallback_cats_default_if_no_match": 1,
}

DEFAULT_GROUNDING_SETTINGS: Dict[str, Any] = {
    "target_candidates": 3,
    "clustering_tolerance": 0.15,
    "confidence_threshold": 0.7,
    "outlier_threshold": 2.0,
    "nut_fee_applies_to": "curb_weight",  # "curb_weight" or "elv_weight"
}

DEFAULT_CONSENSUS_SETTINGS: Dict[str, Any] = {
    "min_agreement_ratio": 0.6,
    "preferred_sources": ["kbb.com", "edmunds.com", "manufacturer"],
    "source_weights": {
        "kbb.com": 1.2,
        "edmunds.com": 1.2,
        "manufacturer": 1.5,
        "default": 1.0
    }
}

# Make-year compatibility list for validation
MAKE_YEAR_COMPATIBILITY: list[Dict[str, Any]] = [
    {"make": "Acura",       "start_year": 1986, "end_year": None},
    {"make": "Audi",        "start_year": 1970, "end_year": None},
    {"make": "BMW",         "start_year": 1956, "end_year": None},
    {"make": "Buick",       "start_year": 1899, "end_year": None},
    {"make": "Cadillac",    "start_year": 1902, "end_year": None},
    {"make": "Chevrolet",   "start_year": 1911, "end_year": None},
    {"make": "Chrysler",    "start_year": 1925, "end_year": None},
    {"make": "Dodge",       "start_year": 1914, "end_year": None},
    {"make": "Ford",        "start_year": 1903, "end_year": None},
    {"make": "Genesis",     "start_year": 2015, "end_year": None},
    {"make": "GMC",         "start_year": 1911, "end_year": None},
    {"make": "Honda",       "start_year": 1969, "end_year": None},
    {"make": "Hummer",      "start_year": 1992, "end_year": 2010},
    {"make": "Hyundai",     "start_year": 1986, "end_year": None},
    {"make": "Infiniti",    "start_year": 1989, "end_year": None},
    {"make": "Jaguar",      "start_year": 1945, "end_year": None},
    {"make": "Jeep",        "start_year": 1941, "end_year": None},
    {"make": "Kia",         "start_year": 1994, "end_year": None},
    {"make": "Land Rover",  "start_year": 1948, "end_year": None},
    {"make": "Lexus",       "start_year": 1989, "end_year": None},
    {"make": "Lincoln",     "start_year": 1917, "end_year": None},
    {"make": "Mazda",       "start_year": 1970, "end_year": None},
    {"make": "Mercedes-Benz","start_year": 1954, "end_year": None},
    {"make": "Mercury",     "start_year": 1939, "end_year": 2011},
    {"make": "Mini",        "start_year": 1959, "end_year": None},
    {"make": "Mitsubishi",  "start_year": 1982, "end_year": None},
    {"make": "Nissan",      "start_year": 1958, "end_year": None},
    {"make": "Oldsmobile",  "start_year": 1897, "end_year": 2004},
    {"make": "Plymouth",    "start_year": 1928, "end_year": 2001},
    {"make": "Pontiac",     "start_year": 1926, "end_year": 2010},
    {"make": "Porsche",     "start_year": 1950, "end_year": None},
    {"make": "Ram",         "start_year": 2009, "end_year": None},
    {"make": "Saab",        "start_year": 1945, "end_year": 2016},
    {"make": "Saturn",      "start_year": 1985, "end_year": 2010},
    {"make": "Scion",       "start_year": 2003, "end_year": 2016},
    {"make": "Subaru",      "start_year": 1968, "end_year": None},
    {"make": "Suzuki",      "start_year": 1985, "end_year": 2013},
    {"make": "Tesla",       "start_year": 2003, "end_year": None},
    {"make": "Toyota",      "start_year": 1958, "end_year": None},
    {"make": "Volkswagen",  "start_year": 1949, "end_year": None},
    {"make": "Volvo",       "start_year": 1955, "end_year": None}
]

def _merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for k, v in (override or {}).items():
        # Shallow merge is sufficient for flat dicts
        merged[k] = v
    return merged

@st.cache_data(show_spinner=False)
def load_db_config() -> Dict[str, Any]:
    try:
        return get_app_config() or {}
    except Exception as e:
        st.warning(f"Database connection failed, using default configuration: {e}")
        return {}

def get_config() -> Dict[str, Any]:
    db_cfg = load_db_config()
    return {
        "price_per_lb": _merge_dicts(DEFAULT_PRICE_PER_LB, db_cfg.get("price_per_lb", {})),
        "flat_costs": _merge_dicts(DEFAULT_FLAT_COSTS, db_cfg.get("flat_costs", {})),
        "weights_fixed": _merge_dicts(DEFAULT_WEIGHTS_FIXED, db_cfg.get("weights_fixed", {})),
        "assumptions": _merge_dicts(DEFAULT_ASSUMPTIONS, db_cfg.get("assumptions", {})),
        "heuristics": _merge_dicts(DEFAULT_HEURISTICS, db_cfg.get("heuristics", {})),
        "grounding_settings": _merge_dicts(DEFAULT_GROUNDING_SETTINGS, db_cfg.get("grounding_settings", {})),
        "consensus_settings": _merge_dicts(DEFAULT_CONSENSUS_SETTINGS, db_cfg.get("consensus_settings", {})),
    }

def refresh_config_cache():
    load_db_config.clear()

def validate_make_year_compatibility(make: str, year: int) -> tuple[bool, str]:
    """
    Validate if the entered year is within the make's production period.
    
    Args:
        make: The vehicle make name (case-insensitive)
        year: The vehicle year as an integer
        
    Returns:
        tuple[bool, str]: (is_valid, warning_message)
            - is_valid: True if year is valid or make is not in list, False if year is outside production period
            - warning_message: Warning message if invalid, empty string if valid
    """
    # Normalize make name for comparison (case-insensitive)
    make_normalized = make.strip().lower()
    
    # Find matching make in compatibility list
    make_info = None
    for entry in MAKE_YEAR_COMPATIBILITY:
        if entry["make"].lower() == make_normalized:
            make_info = entry
            break
    
    # If make is not in the list, allow search (don't show warning)
    if make_info is None:
        return (True, "")
    
    start_year = make_info["start_year"]
    end_year = make_info["end_year"]
    
    # Check if year is before start_year
    if year < start_year:
        make_safe = _escape_html(make_info["make"])
        year_safe = _escape_html(year)
        warning_msg = (
            "⚠️ Are you sure that date is from before the production time of "
            f"{make_safe}?<br>{make_safe} started production in {start_year}, but you entered {year_safe}."
        )
        return (False, warning_msg)
    
    # Check if year is after end_year (only if end_year is not None)
    if end_year is not None and year > end_year:
        make_safe = _escape_html(make_info["make"])
        year_safe = _escape_html(year)
        warning_msg = (
            "⚠️ Are you sure that date is from after the production time of "
            f"{make_safe}?<br>{make_safe} ended production in {end_year}, but you entered {year_safe}."
        )
        return (False, warning_msg)
    
    # Year is within valid range
    return (True, "")

def render_admin_ui():
    """Render the admin configuration UI with restore to default functionality."""
    # SECURITY: Verify current user is actually an admin
    current_buyer = st.session_state.get("buyer_user")
    if not (current_buyer and current_buyer.get("is_admin", False)):
        st.error("🔒 Access denied. You must be an administrator to view this page.")
        st.session_state["admin_mode"] = False
        st.stop()
    
    st.markdown('<div class="main-title">Admin Configuration</div>', unsafe_allow_html=True)
    
    # Info banner
    st.info(
        "🔧 **Admin Settings** - Configure default values used throughout the application. "
        "Changes are saved to the database and persist across sessions. "
        "Use the **🔄 Restore to Default** buttons to reset individual sections to factory defaults."
    )
    st.markdown("---")
    
    # Initialize restore flags in session state
    if 'restore_prices' not in st.session_state:
        st.session_state['restore_prices'] = False
    if 'restore_costs' not in st.session_state:
        st.session_state['restore_costs'] = False
    if 'restore_weights' not in st.session_state:
        st.session_state['restore_weights'] = False
    if 'restore_assumptions' not in st.session_state:
        st.session_state['restore_assumptions'] = False
    
    cfg = get_config()

    # Hide +/- buttons on number inputs while in admin UI
    st.markdown(
        """
        <style>
        [data-testid="stNumberInput"] button { display: none !important; }
        [data-testid="stNumberInput"] input { padding-right: 0.5rem !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Main tabs: General Settings, Cat Prices, Manage Users, History
    tab_general, tab_cat_prices, tab_users, tab_history = st.tabs(["General Settings", "Cat Prices", "Manage Users", "History & Stats"])
    
    with tab_general:
        with st.form("admin_settings_form"):
            st.markdown("### 📝 Configuration Settings")
            st.markdown("Adjust values below and click **Save All Changes** at the bottom. Use **Restore to Default** buttons to reset individual sections.")

            tab_prices, tab_costs, tab_weights, tab_assumptions = st.tabs(
                ["Prices", "Costs", "Weights", "Assumptions"]
            )

            with tab_prices:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader("Commodity Prices ($/lb)")
                with col2:
                    if st.form_submit_button("🔄 Restore to Default", key="restore_prices_btn"):
                        st.session_state['restore_prices'] = True
                
                if st.session_state.get('restore_prices', False):
                    prices_to_use = DEFAULT_PRICE_PER_LB
                    st.session_state['restore_prices'] = False
                else:
                    prices_to_use = cfg["price_per_lb"]
                
                # Prepare data with metadata
                price_rows = []
                for k, v in prices_to_use.items():
                    meta = ADMIN_FIELD_METADATA.get(k, {})
                    label = meta.get("label", k)
                    helper = meta.get("helper", "")
                    price_rows.append({
                        "key": k,
                        "Description": label,
                        "value": float(v),
                        "Helper": helper
                    })
                
                price_df = pd.DataFrame(price_rows).sort_values("Description")
                
                price_df = st.data_editor(
                    price_df, 
                    width='stretch', 
                    num_rows="fixed", 
                    hide_index=True, 
                    key="editor_prices",
                    column_order=["Description", "value"],
                    column_config={
                        "Description": st.column_config.TextColumn("Commodity", disabled=True, help="Description of the item"),
                        "value": st.column_config.NumberColumn("Price ($/lb)", required=True, min_value=0.0, format="$%.4f")
                    }
                )

            with tab_costs:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader("Flat Costs")
                with col2:
                    if st.form_submit_button("🔄 Restore to Default", key="restore_costs_btn"):
                        st.session_state['restore_costs'] = True
                
                costs_to_use = DEFAULT_FLAT_COSTS if st.session_state.get('restore_costs', False) else cfg["flat_costs"]
                if st.session_state.get('restore_costs', False):
                    st.session_state['restore_costs'] = False
                
                # Prepare data with metadata
                cost_rows = []
                for k, v in costs_to_use.items():
                    meta = ADMIN_FIELD_METADATA.get(k, {})
                    label = meta.get("label", k)
                    helper = meta.get("helper", "")
                    cost_rows.append({
                        "key": k,
                        "Description": label,
                        "value": float(v),
                        "Helper": helper
                    })
                
                costs_df = pd.DataFrame(cost_rows).sort_values("Description")
                
                costs_df = st.data_editor(
                    costs_df, 
                    width='stretch', 
                    num_rows="fixed", 
                    hide_index=True, 
                    key="editor_costs",
                    column_order=["Description", "value"],
                    column_config={
                        "Description": st.column_config.TextColumn("Cost Item", disabled=True),
                        "value": st.column_config.NumberColumn("Amount ($)", required=True, min_value=0.0, format="$%.2f")
                    }
                )

            with tab_weights:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader("Component Weights (lb per car)")
                with col2:
                    if st.form_submit_button("🔄 Restore to Default", key="restore_weights_btn"):
                        st.session_state['restore_weights'] = True
                
                weights_to_use = DEFAULT_WEIGHTS_FIXED if st.session_state.get('restore_weights', False) else cfg["weights_fixed"]
                if st.session_state.get('restore_weights', False):
                    st.session_state['restore_weights'] = False
                
                # Prepare data with metadata
                weight_rows = []
                for k, v in weights_to_use.items():
                    meta = ADMIN_FIELD_METADATA.get(k, {})
                    label = meta.get("label", k)
                    helper = meta.get("helper", "")
                    weight_rows.append({
                        "key": k,
                        "Description": label,
                        "value": float(v),
                        "Helper": helper
                    })
                
                weights_df = pd.DataFrame(weight_rows).sort_values("Description")
                
                weights_df = st.data_editor(
                    weights_df, 
                    width='stretch', 
                    num_rows="fixed", 
                    hide_index=True, 
                    key="editor_weights",
                    column_order=["Description", "value"],
                    column_config={
                        "Description": st.column_config.TextColumn("Component", disabled=True),
                        "value": st.column_config.NumberColumn("Weight (lbs)", required=True, min_value=0.0, format="%.1f")
                    }
                )

            with tab_assumptions:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader("Assumptions / Factors")
                with col2:
                    if st.form_submit_button("🔄 Restore to Default", key="restore_assumptions_btn"):
                        st.session_state['restore_assumptions'] = True
                
                assumptions_to_use = DEFAULT_ASSUMPTIONS if st.session_state.get('restore_assumptions', False) else cfg["assumptions"]
                if st.session_state.get('restore_assumptions', False):
                    st.session_state['restore_assumptions'] = False
                
                # Prepare data with metadata
                assumption_rows = []
                for k, v in assumptions_to_use.items():
                    meta = ADMIN_FIELD_METADATA.get(k, {})
                    label = meta.get("label", k)
                    helper = meta.get("helper", "")
                    fmt = meta.get("format", "%.4f")
                    assumption_rows.append({
                        "key": k,
                        "Description": label,
                        "value": float(v),
                        "Helper": helper,
                        "format": fmt
                    })
                
                assumptions_df = pd.DataFrame(assumption_rows)
                
                # Since we can't apply per-row formatting in st.data_editor column_config easily,
                # we'll stick to a high precision default or try to be smart.
                # However, st.column_config applies to the whole column.
                # If we want mixed formatting, it's tricky.
                # But most assumptions are percentages (0.139) or small factors. %.4f is generally safe.
                # The user asked for "show decimal places to places as fits a percentage".
                # 0.139 -> 0.1390 (4 decimal places).
                # 0.5 -> 0.5000.
                # If we use %.3f, 0.139 -> 0.139. 0.5 -> 0.500.
                
                assumptions_df = st.data_editor(
                    assumptions_df,
                    width='stretch',
                    num_rows="fixed",
                    hide_index=True,
                    column_order=["Description", "value"],
                    column_config={
                        "Description": st.column_config.TextColumn("Description", disabled=True),
                        "value": st.column_config.NumberColumn("Value", required=True, step=0.001, format="%.3f")
                    },
                    key="editor_assumptions"
                )

                # Show helper text for unknown engine split
                split_row = assumptions_df[assumptions_df["key"] == "unknown_engine_split_aluminum_percent"]
                if not split_row.empty:
                    val = float(split_row.iloc[0]["value"])
                    al_pct = val * 100
                    fe_pct = (1.0 - val) * 100
                    st.info(f"ℹ️ **Split Calculation:** {ADMIN_FIELD_METADATA['unknown_engine_split_aluminum_percent']['helper']}\n\n"
                            f"Current setting: **{al_pct:.1f}% Aluminum** / **{fe_pct:.1f}% Iron**")

            # Save button outside all tabs
            st.markdown("---")
            st.markdown("### 💾 Save Changes")
            
            # Confirmation checkbox
            confirm_save = st.checkbox("I confirm that I want to update the database with these changes.", key="confirm_save_checkbox")
            
            col1, col2, col3 = st.columns([2, 1, 2])
            with col2:
                save = st.form_submit_button("💾 Save All Changes", width='stretch', disabled=not confirm_save)
            
            if save and confirm_save:
                # Gather updates from DataFrames
                new_prices = {str(row["key"]): float(row["value"]) for _, row in price_df.iterrows()}
                new_flat = {str(row["key"]): float(row["value"]) for _, row in costs_df.iterrows()}
                new_weights = {str(row["key"]): float(row["value"]) for _, row in weights_df.iterrows()}
                new_assumptions = {str(row["key"]): float(row["value"]) for _, row in assumptions_df.iterrows()}

                # Persist
                updated_by = os.getenv("USER") or os.getenv("USERNAME") or "admin"
                ok = True
                ok &= upsert_app_config("price_per_lb", new_prices, "$/lb commodity prices", updated_by)
                ok &= upsert_app_config("flat_costs", new_flat, "Flat costs", updated_by)
                ok &= upsert_app_config("weights_fixed", new_weights, "Fixed component weights", updated_by)
                ok &= upsert_app_config("assumptions", new_assumptions, "Estimator assumptions", updated_by)
                
                # Note: Heuristics, Grounding, and Consensus are preserved as is (not updated here)

                if ok:
                    refresh_config_cache()
                    st.success("✅ Settings saved successfully! Reloading configuration...")
                    st.rerun()
                else:
                    st.error("❌ Failed to save one or more configuration groups. Please try again.")
    
    with tab_cat_prices:
        st.markdown("### Catalytic Converter Prices")
        st.markdown("Manage the internal price list of catalytic converters from especially valuable cars.")
        
        cat_manager = CatPriceManager.get_instance()
        
        # Get current entries
        cat_df = cat_manager.get_all_entries()
        
        if cat_df.empty:
            st.info("No cat price entries found. The table will be populated from CSV on first load.")
        else:
            # Display editable table
            st.markdown("**Edit entries below. Add new rows, modify existing ones, or delete rows.**")
            
            # Use data_editor with num_rows="dynamic" to allow adding rows
            edited_df = st.data_editor(
                cat_df,
                width='stretch',
                num_rows="dynamic",
                hide_index=True,
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True, format="%d"),
                    "vehicle_name": st.column_config.TextColumn("Vehicle Name", required=True),
                    "cat_count": st.column_config.NumberColumn("# of Cats", min_value=0, format="%d"),
                    "total_sale": st.column_config.NumberColumn("Total Sale ($)", min_value=0.0, format="$%.2f"),
                    "current_sale": st.column_config.NumberColumn("Current Sale ($)", min_value=0.0, format="$%.2f"),
                    "extra_cat_value": st.column_config.NumberColumn("Extra Cat Value ($)", min_value=0.0, format="$%.2f")
                },
                key="cat_prices_editor"
            )
            
            col1, col2, col3 = st.columns([2, 1, 2])
            with col2:
                if st.button("💾 Save Cat Prices", use_container_width=True):
                    try:
                        # Validate that vehicle_name is not empty for all rows
                        if edited_df['vehicle_name'].isna().any() or (edited_df['vehicle_name'].astype(str).str.strip() == '').any():
                            st.error("❌ Error: Vehicle name cannot be empty. Please fill in all vehicle names.")
                        else:
                            # Check for duplicate vehicle names within the edited DataFrame
                            vehicle_names = edited_df['vehicle_name'].astype(str).str.strip().str.upper()
                            duplicates = vehicle_names[vehicle_names.duplicated()]
                            if not duplicates.empty:
                                dup_list = duplicates.unique().tolist()
                                st.error(f"❌ Error: Duplicate vehicle names found: {', '.join(dup_list)}. Each vehicle name must be unique.")
                            else:
                                success = cat_manager.update_entries(edited_df)
                                if success:
                                    st.success("✅ Cat prices saved successfully!")
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to save cat prices. Please check the logs for details.")
                    except ValueError as e:
                        # Handle specific validation errors from update_entries
                        st.error(f"❌ {str(e)}")
                        logger.error(f"Validation error saving cat prices: {e}", exc_info=True)
                    except Exception as e:
                        st.error(f"❌ Error saving cat prices: {e}")
                        logger.error(f"Error saving cat prices: {e}", exc_info=True)

    with tab_users:
        st.subheader("Manage Buyers")
        
        # Create User
        with st.expander("Create New Buyer", expanded=False):
            with st.form("create_user_form"):
                new_username = st.text_input("Username (letters/numbers, ., _, -)")
                new_display_name = st.text_input("Display Name (optional)")
                new_password = st.text_input("Password", type="password")
                
                if st.form_submit_button("Create User"):
                    if not new_username:
                        st.error("Username required.")
                    else:
                        ok, msg = create_user(new_username, new_display_name, new_password)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                            
        # List Users
        st.markdown("### Existing Buyers")
        users = list_users()
        if users:
            udf = pd.DataFrame(users)
            # Hide technical fields
            udf = udf.drop(columns=["id", "password_hash"], errors="ignore")
            # Rename for display
            udf = udf.rename(columns={
                "username": "Username",
                "display_name": "Display Name",
                "has_password": "Has Password",
                "is_admin": "Is Admin",
                "created_at": "Created At"
            })
            st.dataframe(udf, use_container_width=True, hide_index=True)
        else:
            st.info("No users found.")

    with tab_history:
        st.subheader("Activity History & Stats")
        
        # SECURITY: Verify current user is admin
        current_buyer = st.session_state.get("buyer_user")
        if not (current_buyer and current_buyer.get("is_admin", False)):
            st.error("🔒 Access denied. History and statistics are only available to administrators.")
            st.stop()
        
        # Filters
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            date_range = st.date_input(
                "Date Range", 
                value=(datetime.now() - timedelta(days=30), datetime.now()),
                max_value=datetime.now()
            )
        
        start_date, end_date = None, None
        if isinstance(date_range, tuple):
            if len(date_range) > 0: start_date = datetime.combine(date_range[0], datetime.min.time())
            if len(date_range) > 1: end_date = datetime.combine(date_range[1], datetime.max.time())
            if len(date_range) == 1: end_date = datetime.combine(date_range[0], datetime.max.time())
            
        with col_f2:
            # User filter
            all_users = list_users()
            user_opts = {u["username"]: u["id"] for u in all_users}
            sel_usernames = st.multiselect("Filter by Buyer", list(user_opts.keys()))
            sel_user_id = user_opts[sel_usernames[0]] if len(sel_usernames) == 1 else None 
            
        with col_f3:
            bought_only = st.checkbox("Bought Only", value=True)
            
        # Stats
        if st.button("Refresh Data", type="primary"):
            st.rerun()
            
        st.markdown("### Performance (Profit by Buyer)")
        profit_stats = get_admin_profit_stats(start_date, end_date)
        if not profit_stats.empty:
            # Highlight top performer
            st.dataframe(
                profit_stats.style.background_gradient(subset=["Total Spend"], cmap="Greens"), 
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.info("No purchase data in this range.")
            
        st.markdown("### Detailed Activity Log")
        # Fetch log
        activity_log = get_admin_history(start_date, end_date, user_id=sel_user_id, bought_only=bought_only)
        if not activity_log.empty:
            st.dataframe(activity_log, use_container_width=True, hide_index=True)
        else:
            st.info("No activity found.")


# Load current config (fallback to defaults)
CONFIG = get_config()

# Make module-level variables for existing functions to use
PRICE_PER_LB = CONFIG["price_per_lb"]
FLAT_COSTS = CONFIG["flat_costs"]

ENGINE_WEIGHT_PERCENT = float(CONFIG["assumptions"]["engine_weight_percent_of_curb"])  # fraction
BATTERY_RECOVERY_FACTOR = float(CONFIG["assumptions"]["battery_recovery_factor"])      # fraction
CATS_PER_CAR = float(CONFIG["assumptions"]["cats_per_car_default_average"])            # count avg
UNKNOWN_ENGINE_SPLIT_AL_PCT = float(CONFIG["assumptions"]["unknown_engine_split_aluminum_percent"])  # fraction
MINIMUM_GOAL_PROFIT = float(CONFIG["assumptions"].get("minimum_goal_profit", 25.0))  # dollars

WEIGHTS = CONFIG["weights_fixed"]
RIMS_AL_WEIGHT_LBS = float(WEIGHTS["rims_aluminum_weight_lbs"]) 
BATTERY_BASELINE_WEIGHT_LBS = float(WEIGHTS["battery_baseline_weight_lbs"]) 
HARNESS_WEIGHT_LBS = float(WEIGHTS["harness_weight_lbs"]) 
FE_RADIATOR_WEIGHT_LBS = float(WEIGHTS["fe_radiator_weight_lbs"]) 
BREAKAGE_WEIGHT_LBS = float(WEIGHTS["breakage_weight_lbs"]) 
ALTERNATOR_WEIGHT_LBS = float(WEIGHTS["alternator_weight_lbs"]) 
STARTER_WEIGHT_LBS = float(WEIGHTS["starter_weight_lbs"]) 
AC_COMPRESSOR_WEIGHT_LBS = float(WEIGHTS["ac_compressor_weight_lbs"]) 
FUSE_BOX_WEIGHT_LBS = float(WEIGHTS["fuse_box_weight_lbs"]) 

# --- Cost Estimator Functions ---
def compute_commodities(cars, curb_weight, aluminum_engine=None, aluminum_rims=None, catalytic_converters=None, cat_value_override=None):
    """Compute all commodity weights, prices, and sale values."""
    w = lambda lbs: cars * lbs
    
    # Calculate engine weight as a percentage of curb weight
    # Based on typical engine weights: 4-cyl (300-400 lbs), V6 (400-500 lbs), V8 (500-700 lbs)
    total_engine_weight = curb_weight * ENGINE_WEIGHT_PERCENT
    
    # Determine engine type based on aluminum_engine parameter
    if aluminum_engine is True:
        # All aluminum engines
        engine_commodities = [
            {"key": "AL_ENGINE", "label": "Aluminum Engine Block", "weight": w(total_engine_weight), "unit_price": PRICE_PER_LB["AL_ENGINE"], "sale_value": 0, "is_engine": True},
        ]
    elif aluminum_engine is False:
        # All iron engines
        engine_commodities = [
            {"key": "FE_ENGINE", "label": "Iron Engine Block", "weight": w(total_engine_weight), "unit_price": PRICE_PER_LB["FE_ENGINE"], "sale_value": 0, "is_engine": True},
        ]
    else:
        # Unknown engine type - split per configured percentage
        aluminum_share = UNKNOWN_ENGINE_SPLIT_AL_PCT
        iron_share = max(0.0, 1.0 - aluminum_share)
        engine_commodities = [
            {"key": "AL_ENGINE", "label": "Aluminum Engine Block", "weight": w(total_engine_weight * aluminum_share), "unit_price": PRICE_PER_LB["AL_ENGINE"], "sale_value": 0, "is_engine": True},
            {"key": "FE_ENGINE", "label": "Iron Engine Block", "weight": w(total_engine_weight * iron_share), "unit_price": PRICE_PER_LB["FE_ENGINE"], "sale_value": 0, "is_engine": True},
        ]
    
    # Determine rims type based on aluminum_rims parameter
    if aluminum_rims is True:
        rims_weight = w(RIMS_AL_WEIGHT_LBS)
    else:
        rims_weight = 0
    
    # Calculate battery weight with recovery factor
    battery_weight = BATTERY_BASELINE_WEIGHT_LBS * BATTERY_RECOVERY_FACTOR
    
    list_commodities = engine_commodities + [
        {"key": "HARNESS", "label": "Wiring Harness", "weight": w(HARNESS_WEIGHT_LBS), "unit_price": PRICE_PER_LB["HARNESS"], "sale_value": 0},
        {"key": "FE_RAD", "label": "FE Radiator", "weight": w(FE_RADIATOR_WEIGHT_LBS), "unit_price": PRICE_PER_LB["FE_RAD"], "sale_value": 0},
        {"key": "BREAKAGE", "label": "Breakage", "weight": w(BREAKAGE_WEIGHT_LBS), "unit_price": PRICE_PER_LB["BREAKAGE"], "sale_value": 0},
        {"key": "ALT", "label": "Alternator", "weight": w(ALTERNATOR_WEIGHT_LBS), "unit_price": PRICE_PER_LB["ALT"], "sale_value": 0},
        {"key": "STARTER", "label": "Starter", "weight": w(STARTER_WEIGHT_LBS), "unit_price": PRICE_PER_LB["STARTER"], "sale_value": 0},
        {"key": "AC_COMP", "label": "A/C Compressor", "weight": w(AC_COMPRESSOR_WEIGHT_LBS), "unit_price": PRICE_PER_LB["AC_COMP"], "sale_value": 0},
        {"key": "FUSE_BOX", "label": "Fuse Box", "weight": w(FUSE_BOX_WEIGHT_LBS), "unit_price": PRICE_PER_LB["FUSE_BOX"], "sale_value": 0},
        {"key": "BATTERY", "label": "Battery", "weight": w(battery_weight), "unit_price": PRICE_PER_LB["BATTERY"], "sale_value": 0},
        {"key": "AL_RIMS", "label": "Aluminum Rims", "weight": rims_weight, "unit_price": PRICE_PER_LB["AL_RIMS"], "sale_value": 0},
    ]

    # Calculate ELV weight per car (curb weight minus engine and all fixed components)
    # Note: engine weights are already multiplied by cars, so we need per-car values
    total_engine_weight_per_car = sum(commodity["weight"] for commodity in engine_commodities) / cars if cars > 0 else 0
    
    # Sum of all fixed component weights per car
    fixed_components_per_car = (
        HARNESS_WEIGHT_LBS + FE_RADIATOR_WEIGHT_LBS + BREAKAGE_WEIGHT_LBS +
        ALTERNATOR_WEIGHT_LBS + STARTER_WEIGHT_LBS + AC_COMPRESSOR_WEIGHT_LBS +
        FUSE_BOX_WEIGHT_LBS + battery_weight + (RIMS_AL_WEIGHT_LBS if aluminum_rims is True else 0)
    )
    
    # ELV weight per car, then multiply by number of cars
    elv_per_car = curb_weight - total_engine_weight_per_car - fixed_components_per_car
    elv_weight = max(0, elv_per_car * cars)  # Ensure non-negative

    # Add ELV at the beginning
    list_commodities.insert(0, {
        "key": "ELV",
        "label": "ELV",
        "weight": elv_weight,
        "unit_price": PRICE_PER_LB["ELV"],
        "sale_value": 0,
    })

    # Add count-based catalytic converters
    cats_count = cars * (catalytic_converters if catalytic_converters is not None else CATS_PER_CAR)
    
    cat_unit_price = PRICE_PER_LB["CATS"]
    cat_sale_value = cats_count * cat_unit_price
    cat_label = "Catalytic Converters"
    
    if cat_value_override is not None:
        # Override value (cat_value_override is total value per car)
        cat_sale_value = cars * cat_value_override
        cat_label = "Catalytic Converters (Price List)"
        # Adjust unit price for display if count > 0
        if cats_count > 0:
            cat_unit_price = cat_sale_value / cats_count
            
    list_commodities.append({
        "key": "CATS", 
        "label": cat_label,
        "weight": cats_count,  # Store count in weight field for display
        "unit_price": cat_unit_price,
        "sale_value": cat_sale_value,
        "is_count_based": True  # Flag to indicate this is count-based
    })
    
    # Add TIRES (special handling - one tire per car at fixed price)
    list_commodities.append({
        "key": "TIRES",
        "label": "Tires",
        "weight": cars,  # Store car count for display
        "unit_price": PRICE_PER_LB["TIRES"],
        "sale_value": cars * PRICE_PER_LB["TIRES"],  # One tire per car
        "is_special": True  # Flag to indicate special handling
    })

    # Compute sale values for weight-based commodities only
    for commodity in list_commodities:
        if not commodity.get("is_count_based") and not commodity.get("is_special"):
            commodity["sale_value"] = commodity["weight"] * commodity["unit_price"]
    
    # Ensure all sale values are positive (revenue items)
    for commodity in list_commodities:
        commodity["sale_value"] = abs(commodity["sale_value"])

    return list_commodities

def calculate_totals(commodities, cars, curb_weight, purchase_price=None, tow_fee=None):
    """Calculate total sale value and all costs with proper sign conventions."""
    # Ensure all revenues are positive
    total_sale = sum(abs(c["sale_value"]) for c in commodities)
    
    # Use provided values or fall back to defaults - ensure costs are negative
    purchase = -(abs(purchase_price) if purchase_price is not None else FLAT_COSTS["PURCHASE"])
    tow = -(abs(tow_fee) if tow_fee is not None else FLAT_COSTS["TOW"])
    
    lead = -(cars * FLAT_COSTS["LEAD_PER_CAR"])
    
    # Calculate Nut fee based on admin setting (curb_weight or elv_weight)
    # Get current config to ensure we have the latest settings
    current_config = get_config()
    grounding_settings = current_config["grounding_settings"]
    nut_fee_applies_to = grounding_settings.get("nut_fee_applies_to", "curb_weight")
    
    if nut_fee_applies_to == "elv_weight":
        # Calculate ELV weight from commodities
        elv_commodity = next((c for c in commodities if c["key"] == "ELV"), None)
        if elv_commodity:
            elv_weight = elv_commodity["weight"]
            nut = -(elv_weight * FLAT_COSTS["NUT_PER_LB"])
        else:
            # Fallback to curb weight if ELV not found
            nut = -(curb_weight * cars * FLAT_COSTS["NUT_PER_LB"])
    else:
        # Default: apply to curb weight
        nut = -(curb_weight * cars * FLAT_COSTS["NUT_PER_LB"])
    
    # Calculate total costs (all negative values)
    total_costs = purchase + tow + lead + nut
    
    # Net = Gross + Costs (where Costs are negative)
    net = total_sale + total_costs
    
    return {
        "total_sale": total_sale,
        "purchase": purchase,
        "tow": tow,
        "lead": lead,
        "nut": nut,
        "total_costs": total_costs,
        "net": net
    }

def validate_pricing_conventions(commodities, totals):
    """Validate that pricing sign conventions are properly enforced."""
    validation_errors = []
    
    # Check that all revenue items have positive sale values
    for commodity in commodities:
        if commodity["sale_value"] < 0:
            validation_errors.append(f"Revenue item '{commodity['label']}' has negative sale value: {commodity['sale_value']}")
    
    # Check that all costs are negative
    if totals["purchase"] > 0:
        validation_errors.append(f"Purchase cost should be negative, got: {totals['purchase']}")
    if totals["tow"] > 0:
        validation_errors.append(f"Tow fee should be negative, got: {totals['tow']}")
    if totals["lead"] > 0:
        validation_errors.append(f"Lead fee should be negative, got: {totals['lead']}")
    if totals["nut"] > 0:
        validation_errors.append(f"Nut fee should be negative, got: {totals['nut']}")
    
    # Check that Net = Gross + Costs
    expected_net = totals["total_sale"] + totals["total_costs"]
    if abs(totals["net"] - expected_net) > 0.01:  # Allow for small rounding differences
        validation_errors.append(f"Net calculation incorrect. Expected: {expected_net}, Got: {totals['net']}")
    
    # Check that tires are treated as revenue
    tire_commodity = next((c for c in commodities if c["key"] == "TIRES"), None)
    if tire_commodity and tire_commodity["sale_value"] <= 0:
        validation_errors.append("Tires should be treated as revenue item with positive sale value")
    
    return validation_errors

def format_currency(amount):
    """Format amount as currency with proper rounding."""
    return f"${round(amount, 2):,.2f}"


def is_valid_dispatch_number(dispatch_number: str) -> bool:
    """
    Validate dispatch number format (admin requirement).

    Dispatch numbers are numeric and currently 6 digits, with eventual growth to 7 digits.
    Leading zeros are allowed.
    """
    cleaned = (dispatch_number or "").strip()
    return cleaned.isdigit() and 6 <= len(cleaned) <= 7


def sanitize_input(text):
    """
    Clean and standardize user input text.
    
    - Strips leading/trailing whitespace
    - Converts multiple spaces to single spaces
    - Removes special characters that could cause issues
    - Returns cleaned string or empty string if None
    
    Args:
        text: Input string to sanitize
        
    Returns:
        Cleaned string with standardized formatting
    """
    if text is None:
        return ""
    
    # Convert to string if not already
    text = str(text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove any non-printable characters
    text = ''.join(char for char in text if char.isprintable())
    
    return text


def exact_match_in_list(user_input: str, options_list: list) -> bool:
    """
    Check if user input exactly matches any item in the list (case-insensitive, after sanitization).
    
    Args:
        user_input: User's typed input
        options_list: List of valid options
        
    Returns:
        bool: True if exact match found, False otherwise
    """
    if not user_input or not options_list:
        return False
    
    sanitized_input = sanitize_input(user_input).lower()
    
    for option in options_list:
        if sanitize_input(option).lower() == sanitized_input:
            return True
    
    return False

# --- Top Navigation Bar ---
# Clean, cohesive banner with title centered, admin on left, user info on right
preferred_display_name = ""
if current_buyer and (current_buyer.get("display_name") or "").strip():
    preferred_display_name = (current_buyer.get("display_name") or "").strip()

admin_label = "Admin" if not st.session_state.get("admin_mode", False) else "Close Admin"

# Check if current user is admin
is_current_user_admin = current_buyer and current_buyer.get("is_admin", False)

# Create top bar with three equal-width columns for proper alignment
topbar_left, topbar_center, topbar_right = st.columns([1, 1, 1], gap="small")

with topbar_left:
    # Only show admin button if current user is admin
    if is_current_user_admin:
        if st.button(admin_label, key="top_admin_toggle_btn"):
            st.session_state["admin_mode"] = not st.session_state.get("admin_mode", False)
            if not st.session_state["admin_mode"]:
                clear_admin_auth()
            st.rerun()

with topbar_center:
    st.markdown('<div class="topbar-title">Ruby G-E-M</div>', unsafe_allow_html=True)

with topbar_right:
    # Right side: username and logout button in a horizontal layout
    if preferred_display_name:
        user_text_col, logout_btn_col = st.columns([3, 1], gap="small")
        with user_text_col:
            safe_display_name = _escape_html(preferred_display_name)
            st.markdown(f'<div class="topbar-user">{safe_display_name}</div>', unsafe_allow_html=True)
        with logout_btn_col:
            if st.button("Logout", key="buyer_logout_btn"):
                if "buyer_user" in st.session_state:
                    del st.session_state["buyer_user"]
                clear_admin_auth()
                st.session_state["admin_mode"] = False
                st.rerun()
    else:
        if st.button("Logout", key="buyer_logout_btn"):
            if "buyer_user" in st.session_state:
                del st.session_state["buyer_user"]
            clear_admin_auth()
            st.session_state["admin_mode"] = False
            st.rerun()

# Additional CSS to hide keyboard shortcuts but keep expander labels visible
st.markdown("""
<style>
    /* Keep expander labels visible and styled */
    [data-testid="stExpander"] details summary {
        color: #990C41 !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        display: flex !important;
        align-items: center !important;
    }
    
    /* CRITICAL: Hide ALL children except first two (icon/emoji and label text) */
    /* This prevents keyboard_arrow_down/keyboard_arrow_right text from showing */
    [data-testid="stExpander"] details summary > *:nth-child(n+3) {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        font-size: 0 !important;
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
        line-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        position: absolute !important;
        left: -9999px !important;
        text-indent: -9999px !important;
        clip: rect(0, 0, 0, 0) !important;
    }
    
    /* Hide only keyboard shortcut text (not the label) - including on hover */
    [data-testid="stExpander"] details summary span[class*="keyboard"],
    [data-testid="stExpander"] details summary span[aria-label*="keyboard"],
    [data-testid="stExpander"] details summary:hover span[class*="keyboard"],
    [data-testid="stExpander"] details summary:hover span[aria-label*="keyboard"],
    [data-testid="stExpander"] details summary *[class*="keyboard"],
    [data-testid="stExpander"] details summary *[aria-label*="keyboard"],
    [data-testid="stExpander"] details summary *[data-testid*="keyboard"],
    [data-testid="stExpander"] details summary:hover *[class*="keyboard"],
    [data-testid="stExpander"] details summary:hover *[aria-label*="keyboard"],
    [data-testid="stExpander"] details summary:hover *[data-testid*="keyboard"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
        font-size: 0 !important;
        line-height: 0 !important;
    }
    
    /* Hide pseudo-elements on keyboard-related elements only */
    [data-testid="stExpander"] details summary *[class*="keyboard"]::after,
    [data-testid="stExpander"] details summary *[class*="keyboard"]::before,
    [data-testid="stExpander"] details summary *[aria-label*="keyboard"]::after,
    [data-testid="stExpander"] details summary *[aria-label*="keyboard"]::before {
        content: none !important;
    }
    
    /* Disable tooltip popups and remove title attributes */
    [data-testid="stExpander"] details summary[title]:hover::after,
    [data-testid="stExpander"] details summary[title]:hover::before,
    [data-testid="stExpander"] details summary *[title]:hover::after,
    [data-testid="stExpander"] details summary *[title]:hover::before {
        display: none !important;
        content: none !important;
        visibility: hidden !important;
    }
    
    /* Remove title tooltips completely */
    [data-testid="stExpander"] details summary[title],
    [data-testid="stExpander"] details summary *[title] {
        pointer-events: auto !important;
    }
    
    /* Hide any Material Icons that might show keyboard arrow (but keep emoji icons) */
    [data-testid="stExpander"] details summary .material-icons,
    [data-testid="stExpander"] details summary *[class*="material-icons"],
    [data-testid="stExpander"] details summary:hover .material-icons,
    [data-testid="stExpander"] details summary:hover *[class*="material-icons"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
    }
    
    /* Aggressively hide keyboard shortcut indicators - including arrow characters */
    [data-testid="stExpander"] details summary *[aria-label*="arrow"],
    [data-testid="stExpander"] details summary *[aria-label*="right"],
    [data-testid="stExpander"] details summary *[aria-label*="Arrow"],
    [data-testid="stExpander"] details summary *[aria-label*="Right"],
    [data-testid="stExpander"] details summary *[title*="arrow"],
    [data-testid="stExpander"] details summary *[title*="right"],
    [data-testid="stExpander"] details summary *[title*="Arrow"],
    [data-testid="stExpander"] details summary *[title*="Right"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
        font-size: 0 !important;
        line-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Hide any element with specific Streamlit keyboard shortcut classes */
    [data-testid="stExpander"] details summary [class*="stKeyboardShortcut"],
    [data-testid="stExpander"] details summary [class*="keyboard-shortcut"],
    [data-testid="stExpander"] details summary [data-baseweb*="keyboard"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        width: 0 !important;
        height: 0 !important;
        font-size: 0 !important;
        line-height: 0 !important;
        overflow: hidden !important;
    }
    
    /* Hide keyboard shortcut text that appears as "keyboard_arrow_down" or "keyboard_arrow_right" */
    /* These appear as text when Material Icons font doesn't load - hide them completely */
    
    /* Hide all Material Icons elements in expander headers */
    [data-testid="stExpander"] details summary .material-icons,
    [data-testid="stExpander"] details summary .material-symbols-outlined,
    [data-testid="stExpander"] details summary [class*="material-icons"],
    [data-testid="stExpander"] details summary [class*="material-symbols"],
    [data-testid="stExpander"] details summary span[class*="material"],
    [data-testid="stExpander"] details summary i[class*="material"],
    [data-testid="stExpander"] details summary *[class*="material-icons"],
    [data-testid="stExpander"] details summary *[class*="material-symbols"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        font-size: 0 !important;
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
        line-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        position: absolute !important;
        left: -9999px !important;
        text-indent: -9999px !important;
    }
    
    /* Hide any element from the 3rd child onwards (keeping icon/emoji and label text) */
    [data-testid="stExpander"] details summary > span:nth-child(n+3),
    [data-testid="stExpander"] details summary > div:nth-child(n+3),
    [data-testid="stExpander"] details summary > p:nth-child(n+3),
    [data-testid="stExpander"] details summary > *:nth-child(n+3) {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        font-size: 0 !important;
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
        line-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        position: absolute !important;
        left: -9999px !important;
        text-indent: -9999px !important;
    }
    
    /* Hide the last child if it's not the first or second (likely keyboard shortcut) */
    [data-testid="stExpander"] details summary > *:last-child:not(:first-child):not(:nth-child(2)) {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        font-size: 0 !important;
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
        line-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        position: absolute !important;
        left: -9999px !important;
        text-indent: -9999px !important;
    }
    
    /* Hide any span that might contain the keyboard arrow text */
    [data-testid="stExpander"] details summary span:not(:first-child):not(:nth-child(2)) {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        font-size: 0 !important;
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
        line-height: 0 !important;
        text-indent: -9999px !important;
    }
    
    /* Hide pseudo-elements */
    [data-testid="stExpander"] details summary::after,
    [data-testid="stExpander"] details summary::before {
        display: none !important;
        content: "" !important;
    }
    
    /* Ensure summary is positioned correctly */
    [data-testid="stExpander"] details summary {
        position: relative !important;
    }
    
    /* Hide elements with attributes containing keyboard_arrow */
    [data-testid="stExpander"] details summary *[aria-label*="keyboard_arrow"],
    [data-testid="stExpander"] details summary *[title*="keyboard_arrow"],
    [data-testid="stExpander"] details summary *[class*="keyboard_arrow"],
    [data-testid="stExpander"] details summary *[data-testid*="keyboard_arrow"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        font-size: 0 !important;
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
    }
    
    /* FINAL FALLBACK: Force hide any element that might contain keyboard_arrow text */
    /* Target all possible elements that could contain this text */
    [data-testid="stExpander"] details summary span,
    [data-testid="stExpander"] details summary div,
    [data-testid="stExpander"] details summary p {
        /* Only show if it's the first or second child */
    }
    
    /* Explicitly hide any element containing "keyboard_arrow" in any form */
    /* Since CSS can't select by text content, we hide all suspicious elements */
    [data-testid="stExpander"] details summary > *:not(:first-child):not(:nth-child(2)) {
        font-size: 0 !important;
        line-height: 0 !important;
        max-width: 0 !important;
        max-height: 0 !important;
        overflow: hidden !important;
        text-overflow: clip !important;
        white-space: nowrap !important;
    }
</style>
""", unsafe_allow_html=True)

# Admin toggle - Initialize state
if 'admin_mode' not in st.session_state:
    st.session_state['admin_mode'] = False

if st.session_state['admin_mode']:
    # Apply admin-specific CSS for distinct mode styling
    st.markdown(generate_admin_mode_css(), unsafe_allow_html=True)
    if require_admin_password():
        render_admin_ui()
    st.stop()  # Don't show the main app when in admin mode

# Create two columns for the main layout with better spacing (2:1 ratio for vehicle search:cost estimate)
left_col, right_col = st.columns([1.5, 1])

# --- Left Column: Vehicle Search & Recent Entries ---
with left_col:
    st.markdown('<div class="section-header">Vehicle Search</div>', unsafe_allow_html=True)

    # Create a container for vehicle details that can be cleared
    vehicle_details_container = st.empty()

    # --- Display Current Vehicle Details (if available and not in pending search) ---
    if st.session_state.get('detailed_vehicle_info') and not st.session_state.get('pending_search'):
        # Use the container to render vehicle details
        with vehicle_details_container.container():
            vehicle_info = st.session_state['detailed_vehicle_info']
            
            # Display vehicle name with blue styling
            vehicle_name = f"{vehicle_info['year']} {vehicle_info['make']} {vehicle_info['model']}"
            safe_vehicle_name = _escape_html(vehicle_name)
            st.markdown(f"""
            <div style="background: #eff6ff; padding: 1rem; border-radius: 6px; border: 1px solid #bfdbfe; margin-bottom: 1rem;">
                <div style="margin: 0; color: #1e40af; font-weight: 700; text-align: center; font-size: 1.25rem;">{safe_vehicle_name}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Display vehicle details in the left column
            # Display curb weight, engine, and rims info in four side-by-side boxes
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div style="background: #f8fafc; padding: 0.5rem; border-radius: 6px; margin: 0.25rem 0; border: 1px solid #e2e8f0; text-align: center;">
                    <strong style="color: #64748b; font-size: 0.8rem;">WEIGHT</strong><br>
                    <span style="color: #0f172a; font-weight: 600;">{vehicle_info['weight']} lbs</span>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if vehicle_info['aluminum_engine'] is not None:
                    engine_status = "Al" if vehicle_info['aluminum_engine'] else "Fe"
                    # Teal for Al, Orange for Fe
                    engine_color = "#0d9488" if vehicle_info['aluminum_engine'] else "#d97706"
                    engine_bg = "#f0fdfa" if vehicle_info['aluminum_engine'] else "#fffbeb"
                    engine_border = "#ccfbf1" if vehicle_info['aluminum_engine'] else "#fef3c7"
                    
                    st.markdown(f"""
                    <div style="background: {engine_bg}; padding: 0.5rem; border-radius: 6px; margin: 0.25rem 0; border: 1px solid {engine_border}; text-align: center;">
                        <strong style="color: {engine_color}; font-size: 0.8rem;">ENGINE</strong><br>
                        <span style="color: {engine_color}; font-weight: 600;">{engine_status}</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background: #f8fafc; padding: 0.5rem; border-radius: 6px; margin: 0.25rem 0; border: 1px solid #e2e8f0; text-align: center;">
                        <strong style="color: #64748b; font-size: 0.8rem;">ENGINE</strong><br>
                        <span style="color: #94a3b8;">?</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col3:
                if vehicle_info['aluminum_rims'] is not None:
                    rims_status = "Al" if vehicle_info['aluminum_rims'] else "Fe"
                    rims_color = "#0d9488" if vehicle_info['aluminum_rims'] else "#d97706"
                    rims_bg = "#f0fdfa" if vehicle_info['aluminum_rims'] else "#fffbeb"
                    rims_border = "#ccfbf1" if vehicle_info['aluminum_rims'] else "#fef3c7"
                    
                    st.markdown(f"""
                    <div style="background: {rims_bg}; padding: 0.5rem; border-radius: 6px; margin: 0.25rem 0; border: 1px solid {rims_border}; text-align: center;">
                        <strong style="color: {rims_color}; font-size: 0.8rem;">RIMS</strong><br>
                        <span style="color: {rims_color}; font-weight: 600;">{rims_status}</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background: #f8fafc; padding: 0.5rem; border-radius: 6px; margin: 0.25rem 0; border: 1px solid #e2e8f0; text-align: center;">
                        <strong style="color: #64748b; font-size: 0.8rem;">RIMS</strong><br>
                        <span style="color: #94a3b8;">?</span>
                    </div>
                    """, unsafe_allow_html=True)

            with col4:
                if vehicle_info.get('catalytic_converters') is not None:
                    cats_count = vehicle_info['catalytic_converters']
                    
                    st.markdown(f"""
                    <div style="background: #eff6ff; padding: 0.5rem; border-radius: 6px; margin: 0.25rem 0; border: 1px solid #bfdbfe; text-align: center;">
                        <strong style="color: #3b82f6; font-size: 0.8rem;">CATS</strong><br>
                        <span style="color: #1d4ed8; font-weight: 600;">{cats_count}</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background: #f8fafc; padding: 0.5rem; border-radius: 6px; margin: 0.25rem 0; border: 1px solid #e2e8f0; text-align: center;">
                        <strong style="color: #64748b; font-size: 0.8rem;">CATS</strong><br>
                        <span style="color: #94a3b8;">?</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Display validation warnings if present
            validation_warnings = vehicle_info.get('validation_warnings', [])
            
            # Show positive indicator if cat price was found (internal override)
            if vehicle_info.get('cat_value_override'):
                 st.markdown(f"""
                <div class="success-message">
                    <strong>Cat Price Found!</strong><br>
                    Using specific pricing from internal list: ${vehicle_info['cat_value_override']:,.2f}
                </div>
                """, unsafe_allow_html=True)
            
            if validation_warnings:
                from confidence_ui import render_warning_banner
                st.markdown("### Data Quality Alerts")
                for warning in validation_warnings:
                    render_warning_banner([warning])
        
        # Source attribution removed - using Gemini Search Grounding for all lookups

    # --- Main Form ---
    # Simplified column layout for cleaner professional look
    col1, col2, col3 = st.columns([1, 2, 2])

    # Year input (simple text input, no suggestions needed)
    with col1:
        # Match label style used for Make/Model
        st.markdown("**Year**")
        year_input = st.text_input(
            "",
            placeholder="",
            value="",
            key="year_input_main",
            label_visibility="collapsed",
        )

    # Make input with dropdown list and text field
    with col2:
        # Label for Make
        st.markdown("**Make**")
        
        # Get all makes for dropdown (already alphabetized)
        all_makes_list = get_all_makes()
        
        # Get current accepted value for display
        current_make_value = st.session_state.get('make_input_accepted', "")

        # Dropdown list above text input - "Choose from list" as first option
        make_dropdown_options = ["Choose from list"] + (all_makes_list.copy() if all_makes_list else [])
        make_dropdown_index = 0  # Default to "Choose from list"
        if current_make_value and current_make_value in all_makes_list:
            # Find index in the full list (add 1 because "Choose from list" is first)
            make_dropdown_index = all_makes_list.index(current_make_value) + 1
        
        make_dropdown_selection = st.selectbox(
            "",
            options=make_dropdown_options,
            index=make_dropdown_index,
            key="make_input_dropdown",
            label_visibility="collapsed"
        )

        # Text input field for make - use value from session state to sync with dropdown
        # Use a dynamic key to force update when value changes
        make_input_key = f"make_input_text_{current_make_value}"
        make_input = st.text_input("", value=current_make_value, placeholder="or type here.", key=make_input_key, label_visibility="collapsed")
        
        # Track previous dropdown selection to detect changes
        previous_dropdown_selection = st.session_state.get('make_dropdown_previous', None)
        
        # Handle selection from dropdown - update text input FIRST (takes priority over text input)
        # Always replace input field with dropdown selection (skip only if "Choose from list")
        if make_dropdown_selection and make_dropdown_selection != "Choose from list":
            # Update if dropdown selection differs from accepted value OR if dropdown actually changed
            if previous_dropdown_selection != make_dropdown_selection or make_dropdown_selection != current_make_value:
                previous_make = st.session_state.get('make_input_accepted', "")
                st.session_state['make_input_accepted'] = make_dropdown_selection
                # Always clear model when make changes via dropdown
                if 'model_input_accepted' in st.session_state:
                    del st.session_state['model_input_accepted']
                # Clear model dropdown previous to force refresh
                if 'model_dropdown_previous' in st.session_state:
                    del st.session_state['model_dropdown_previous']
                # Reset prompt states
                if 'make_prompt_pending' in st.session_state:
                    del st.session_state['make_prompt_pending']
                if 'make_suggestion' in st.session_state:
                    del st.session_state['make_suggestion']
                if 'model_prompt_pending' in st.session_state:
                    del st.session_state['model_prompt_pending']
                if 'model_suggestion' in st.session_state:
                    del st.session_state['model_suggestion']
                st.session_state['make_dropdown_previous'] = make_dropdown_selection
                st.rerun()
        
        # Store current dropdown selection for next comparison
        st.session_state['make_dropdown_previous'] = make_dropdown_selection
        
        # Validate typed input when dropdown is clicked (user changed focus)
        # Only process if dropdown hasn't changed (to avoid conflicts)
        if previous_dropdown_selection == make_dropdown_selection and make_input != current_make_value and make_input and make_dropdown_selection == "Choose from list":
            if exact_match_in_list(make_input, all_makes_list):
                # Found exact match - accept it and update dropdown index
                previous_make = st.session_state.get('make_input_accepted', "")
                matched_make = None
                for make in all_makes_list:
                    if sanitize_input(make).lower() == sanitize_input(make_input).lower():
                        matched_make = make
                        break
                if matched_make:
                    st.session_state['make_input_accepted'] = matched_make
                    # Clear model if make changed
                    if previous_make != matched_make:
                        if 'model_input_accepted' in st.session_state:
                            del st.session_state['model_input_accepted']
                        if 'model_prompt_pending' in st.session_state:
                            del st.session_state['model_prompt_pending']
                        if 'model_suggestion' in st.session_state:
                            del st.session_state['model_suggestion']
                    # Reset prompt states
                    if 'make_prompt_pending' in st.session_state:
                        del st.session_state['make_prompt_pending']
                    if 'make_suggestion' in st.session_state:
                        del st.session_state['make_suggestion']
                    st.rerun()
        
        # Handle text input changes (only if dropdown hasn't changed)
        if previous_dropdown_selection == make_dropdown_selection and make_input != current_make_value:
            # User typed something different from the accepted value
            if make_input:
                # Check if user typed something that exactly matches a list item
                if exact_match_in_list(make_input, all_makes_list):
                    # Exact match - accept it directly, but use the actual make from list (preserve case)
                    previous_make = st.session_state.get('make_input_accepted', "")
                    matched_make = None
                    for make in all_makes_list:
                        if sanitize_input(make).lower() == sanitize_input(make_input).lower():
                            matched_make = make
                            break
                    if matched_make:
                        st.session_state['make_input_accepted'] = matched_make
                        final_make = matched_make
                    else:
                        st.session_state['make_input_accepted'] = make_input
                        final_make = make_input
                    # Clear model if make changed (always clear when make changes)
                    if previous_make != final_make:
                        if 'model_input_accepted' in st.session_state:
                            del st.session_state['model_input_accepted']
                        # Reset model prompt states too
                        if 'model_prompt_pending' in st.session_state:
                            del st.session_state['model_prompt_pending']
                        if 'model_suggestion' in st.session_state:
                            del st.session_state['model_suggestion']
                    # Reset prompt states
                    if 'make_prompt_pending' in st.session_state:
                        del st.session_state['make_prompt_pending']
                    if 'make_suggestion' in st.session_state:
                        del st.session_state['make_suggestion']
                    st.rerun()
                else:
                    # Check for fuzzy match
                    fuzzy_make = suggest_make(make_input)
                    if fuzzy_make and fuzzy_make.lower() != sanitize_input(make_input).lower():
                        # Update suggestion if it changed or if no prompt is pending
                        current_suggestion = st.session_state.get('make_suggestion')
                        prompt_pending = st.session_state.get('make_prompt_pending', False)
                        
                        # Update suggestion if it changed or if no prompt is pending
                        if not prompt_pending or current_suggestion != fuzzy_make:
                            # Update accepted make temporarily so model list updates
                            previous_make = st.session_state.get('make_input_accepted', "")
                            st.session_state['make_input_accepted'] = make_input
                            # Clear model if make changed
                            if previous_make != make_input:
                                if 'model_input_accepted' in st.session_state:
                                    del st.session_state['model_input_accepted']
                                if 'model_prompt_pending' in st.session_state:
                                    del st.session_state['model_prompt_pending']
                                if 'model_suggestion' in st.session_state:
                                    del st.session_state['model_suggestion']
                            # Set prompt state and rerun to show the prompt immediately
                            st.session_state['make_suggestion'] = fuzzy_make
                            st.session_state['make_prompt_pending'] = True
                            st.rerun()
                        else:
                            # Prompt already pending with same suggestion - just update accepted make
                            previous_make = st.session_state.get('make_input_accepted', "")
                            st.session_state['make_input_accepted'] = make_input
                            # Clear model if make changed
                            if previous_make != make_input:
                                if 'model_input_accepted' in st.session_state:
                                    del st.session_state['model_input_accepted']
                                if 'model_prompt_pending' in st.session_state:
                                    del st.session_state['model_prompt_pending']
                                if 'model_suggestion' in st.session_state:
                                    del st.session_state['model_suggestion']
                    else:
                        # No match - accept typed value but don't rerun (let user continue typing)
                        previous_make = st.session_state.get('make_input_accepted', "")
                        st.session_state['make_input_accepted'] = make_input
                        # Clear model if make changed
                        if previous_make != make_input:
                            if 'model_input_accepted' in st.session_state:
                                del st.session_state['model_input_accepted']
                            if 'model_prompt_pending' in st.session_state:
                                del st.session_state['model_prompt_pending']
                            if 'model_suggestion' in st.session_state:
                                del st.session_state['model_suggestion']
                        # Reset prompt states
                        if 'make_prompt_pending' in st.session_state:
                            del st.session_state['make_prompt_pending']
                        if 'make_suggestion' in st.session_state:
                            del st.session_state['make_suggestion']
            else:
                # Text input cleared
                if 'make_input_accepted' in st.session_state:
                    del st.session_state['make_input_accepted']
                if 'model_input_accepted' in st.session_state:
                    del st.session_state['model_input_accepted']
                if 'make_prompt_pending' in st.session_state:
                    del st.session_state['make_prompt_pending']
                if 'make_suggestion' in st.session_state:
                    del st.session_state['make_suggestion']
                if 'model_prompt_pending' in st.session_state:
                    del st.session_state['model_prompt_pending']
                if 'model_suggestion' in st.session_state:
                    del st.session_state['model_suggestion']

    # Model input with dropdown list and text field
    with col3:
        # Get the accepted make
        accepted_make = st.session_state.get('make_input_accepted', None)
        
        # Label for Model
        model_label = "Model" + (f" ({accepted_make})" if accepted_make else "")
        st.markdown(f"**{model_label}**")

        # Get models for the selected make (already alphabetized)
        if accepted_make:
            model_options_list = get_models_for_make(accepted_make)
        else:
            model_options_list = []
        
        # Get current accepted value for display
        current_model_value = st.session_state.get('model_input_accepted', "")
        
        # Dropdown list above text input - "Choose from list" as first option
        model_dropdown_options = ["Choose from list"] + (model_options_list.copy() if model_options_list else [])
        model_dropdown_index = 0  # Default to "Choose from list"
        if current_model_value and current_model_value in model_options_list:
            # Find index in the full list (add 1 because "Choose from list" is first)
            model_dropdown_index = model_options_list.index(current_model_value) + 1
        
        model_dropdown_selection = st.selectbox(
            "",
            options=model_dropdown_options,
            index=model_dropdown_index,
            key="model_input_dropdown",
            disabled=not accepted_make,
            label_visibility="collapsed"
        )
        
        # Show fuzzy match suggestion above text input
        if st.session_state.get('model_prompt_pending'):
            suggested_model = st.session_state.get('model_suggestion', '')
            if suggested_model:
                st.markdown(f"💡 Did you mean **{suggested_model}**?")
                if st.button("Use suggested model", key="model_use_suggestion"):
                    st.session_state['model_input_accepted'] = suggested_model
                    del st.session_state['model_prompt_pending']
                    del st.session_state['model_suggestion']
                    st.rerun()
        
        # Text input field for model (disabled until make is selected) - use value from session state to sync with dropdown
        # Use a dynamic key to force update when value changes
        model_input_key = f"model_input_text_{current_model_value}_{accepted_make}"
        model_input = st.text_input(
            "",
            value=current_model_value,
            placeholder="or type here.",
            key=model_input_key,
            disabled=not accepted_make,
            label_visibility="collapsed"
        )
        
        # Track previous dropdown selection to detect changes
        previous_model_dropdown_selection = st.session_state.get('model_dropdown_previous', None)
        
        # Handle selection from dropdown - update text input FIRST (takes priority over text input)
        # Always replace input field with dropdown selection (skip only if "Choose from list")
        if accepted_make and model_dropdown_selection and model_dropdown_selection != "Choose from list":
            # Update if dropdown selection differs from accepted value OR if dropdown actually changed
            if previous_model_dropdown_selection != model_dropdown_selection or model_dropdown_selection != current_model_value:
                st.session_state['model_input_accepted'] = model_dropdown_selection
                # Reset prompt states
                if 'model_prompt_pending' in st.session_state:
                    del st.session_state['model_prompt_pending']
                if 'model_suggestion' in st.session_state:
                    del st.session_state['model_suggestion']
                st.session_state['model_dropdown_previous'] = model_dropdown_selection
                st.rerun()
        
        # Store current dropdown selection for next comparison
        st.session_state['model_dropdown_previous'] = model_dropdown_selection
        
        # Validate typed input when dropdown is clicked (user changed focus)
        # Only process if dropdown hasn't changed (to avoid conflicts)
        if accepted_make and previous_model_dropdown_selection == model_dropdown_selection and model_input != current_model_value and model_input and model_dropdown_selection == "Choose from list":
            if exact_match_in_list(model_input, model_options_list):
                # Found exact match - accept it
                matched_model = None
                for model in model_options_list:
                    if sanitize_input(model).lower() == sanitize_input(model_input).lower():
                        matched_model = model
                        break
                if matched_model:
                    st.session_state['model_input_accepted'] = matched_model
                    # Reset prompt states
                    if 'model_prompt_pending' in st.session_state:
                        del st.session_state['model_prompt_pending']
                    if 'model_suggestion' in st.session_state:
                        del st.session_state['model_suggestion']
                    st.rerun()
        
        # Handle text input changes (only if dropdown hasn't changed)
        if accepted_make and previous_model_dropdown_selection == model_dropdown_selection and model_input != current_model_value:
            # User typed something different from the accepted value
            if model_input:
                # Check if user typed something that exactly matches a list item
                if exact_match_in_list(model_input, model_options_list):
                    # Exact match - accept it directly, but use the actual model from list (preserve case)
                    matched_model = None
                    for model in model_options_list:
                        if sanitize_input(model).lower() == sanitize_input(model_input).lower():
                            matched_model = model
                            break
                    if matched_model:
                        st.session_state['model_input_accepted'] = matched_model
                    else:
                        st.session_state['model_input_accepted'] = model_input
                    # Reset prompt states
                    if 'model_prompt_pending' in st.session_state:
                        del st.session_state['model_prompt_pending']
                    if 'model_suggestion' in st.session_state:
                        del st.session_state['model_suggestion']
                    st.rerun()
                else:
                    # Check for fuzzy match
                    fuzzy_model = suggest_model(accepted_make, model_input)
                    if fuzzy_model and fuzzy_model.lower() != sanitize_input(model_input).lower():
                        # Update suggestion if it changed or if no prompt is pending
                        current_suggestion = st.session_state.get('model_suggestion')
                        prompt_pending = st.session_state.get('model_prompt_pending', False)
                        
                        # Update suggestion if it changed or if no prompt is pending
                        if not prompt_pending or current_suggestion != fuzzy_model:
                            st.session_state['model_suggestion'] = fuzzy_model
                            st.session_state['model_prompt_pending'] = True
                            # Rerun to show the prompt immediately
                            st.rerun()
                    else:
                        # No match - accept typed value but don't rerun (let user continue typing)
                        st.session_state['model_input_accepted'] = model_input
                        # Reset prompt states
                        if 'model_prompt_pending' in st.session_state:
                            del st.session_state['model_prompt_pending']
                        if 'model_suggestion' in st.session_state:
                            del st.session_state['model_suggestion']
            else:
                # Text input cleared
                if 'model_input_accepted' in st.session_state:
                    del st.session_state['model_input_accepted']
                if 'model_prompt_pending' in st.session_state:
                    del st.session_state['model_prompt_pending']
                if 'model_suggestion' in st.session_state:
                    del st.session_state['model_suggestion']

    # Submit button (moved outside form for dynamic enabling)
    # Check if year, make and model are all filled
    year_input_value = year_input.strip() if year_input else ""
    make_accepted = st.session_state.get('make_input_accepted', "")
    model_accepted = st.session_state.get('model_input_accepted', "")
    
    submit_disabled = (
        st.session_state.get('make_prompt_pending', False) or
        st.session_state.get('model_prompt_pending', False) or
        not year_input_value or
        not make_accepted or
        not model_accepted
    )

    submit_button = st.button(
        "Search Vehicle",
        disabled=submit_disabled,
        use_container_width=True,
        key="submit_vehicle_search"
    )

    # --- Progress Area ---
    # Create a container for the progress area that can be shown/hidden
    progress_container = st.empty()

    # --- Processing and Output ---
    if submit_button:
        # Use accepted values (from suggestions/"did you mean?" confirmations)
        year_input = sanitize_input(year_input)
        make_input = sanitize_input(st.session_state.get('make_input_accepted', ""))
        model_input = sanitize_input(st.session_state.get('model_input_accepted', ""))

        # Store the search inputs
        st.session_state['pending_search'] = {
            'year': year_input,
            'make': make_input,
            'model': model_input
        }
        
        # Clear all previous vehicle data immediately when new search is initiated
        st.session_state['detailed_vehicle_info'] = None
        st.session_state['last_curb_weight'] = None
        st.session_state['last_aluminum_engine'] = None
        st.session_state['last_aluminum_rims'] = None
        st.session_state['last_catalytic_converters'] = None
        st.session_state['last_vehicle_info'] = None
        st.session_state['calculation_results'] = None
        st.session_state['last_processed_vehicle'] = None
        st.session_state['auto_calculate'] = False

        # Reset reference catalog prompt states for new search
        st.session_state['make_prompt_pending'] = False
        st.session_state['make_prompt_answered'] = False
        st.session_state['model_prompt_pending'] = False
        st.session_state['model_prompt_answered'] = False
        # Clear any stored suggestions and hints
        for key in ['make_suggestion', 'model_suggestion', 'cross_make_hint']:
            if key in st.session_state:
                del st.session_state[key]
        
        # Rerun to clear the display immediately
        # The containers will be cleared by conditional rendering based on pending_search flag
        st.rerun()
    
    # Process pending search after rerun
    if st.session_state.get('pending_search'):
        search_data = st.session_state['pending_search']
        year_input = sanitize_input(search_data['year'])
        make_input = sanitize_input(search_data['make'])
        model_input = sanitize_input(search_data['model'])
        
        # Don't clear the pending search flag yet - keep it active to prevent old UI from showing
        # We'll clear it only when we successfully complete the search or encounter an error
        
        if not make_input or not model_input:
            # Clear pending search on error
            del st.session_state['pending_search']
            st.markdown("""
            <div class="warning-message">
                <strong>Missing Information:</strong> Please enter both a make and a model.
            </div>
            """, unsafe_allow_html=True)
        else:
            # Convert year to integer and validate
            try:
                year_int = int(year_input)
                if year_int < 1900 or year_int > 2050:
                    # Clear pending search on error
                    del st.session_state['pending_search']
                    st.markdown("""
                    <div class="warning-message">
                        <strong>Invalid Year:</strong> Please enter a year between 1900 and 2050.
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Validate make-year compatibility (skip if bypass flag is set)
                    bypass_validation = st.session_state.get('bypass_year_validation', False)
                    if bypass_validation:
                        # Clear the bypass flag and proceed with search
                        del st.session_state['bypass_year_validation']
                        is_valid = True
                    else:
                        is_valid, warning_message = validate_make_year_compatibility(make_input, year_int)
                    
                    if not is_valid:
                        # Clear pending search to prevent automatic search
                        del st.session_state['pending_search']
                        
                        # Store search data for "Search anyway" button
                        st.session_state['pending_search_after_warning'] = {
                            'year': year_input,
                            'make': make_input,
                            'model': model_input
                        }
                        
                        # Display warning with line breaks and "Search anyway" button
                        st.markdown(f"""
                        <div class="warning-message">
                            {warning_message}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Add "Search anyway" button
                        col1, col2, col3 = st.columns([1, 1, 1])
                        with col2:
                            if st.button("Search anyway", key="search_anyway_button", use_container_width=True):
                                # Set bypass flag and restore pending search to proceed with search
                                st.session_state['bypass_year_validation'] = True
                                if 'pending_search_after_warning' in st.session_state:
                                    st.session_state['pending_search'] = st.session_state['pending_search_after_warning']
                                    del st.session_state['pending_search_after_warning']
                                
                                # Clear all previous vehicle data immediately when proceeding with search (same as Search Vehicle button)
                                st.session_state['detailed_vehicle_info'] = None
                                st.session_state['last_curb_weight'] = None
                                st.session_state['last_aluminum_engine'] = None
                                st.session_state['last_aluminum_rims'] = None
                                st.session_state['last_catalytic_converters'] = None
                                st.session_state['last_vehicle_info'] = None
                                st.session_state['calculation_results'] = None
                                st.session_state['last_processed_vehicle'] = None
                                st.session_state['auto_calculate'] = False
                                
                                # Reset reference catalog prompt states for new search
                                st.session_state['make_prompt_pending'] = False
                                st.session_state['make_prompt_answered'] = False
                                st.session_state['model_prompt_pending'] = False
                                st.session_state['model_prompt_answered'] = False
                                # Clear any stored suggestions and hints
                                for key in ['make_suggestion', 'model_suggestion', 'cross_make_hint']:
                                    if key in st.session_state:
                                        del st.session_state[key]
                                
                                st.rerun()
                    else:
                        # Create a unique identifier for this vehicle search
                        vehicle_id = f"{year_int}_{make_input}_{model_input}"
                        
                        # Check if we've already processed this vehicle in this session
                        if st.session_state.get('last_processed_vehicle') != vehicle_id:
                            # Show simplified progress indicator
                            with progress_container.container():
                                st.markdown("""
                                <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 50%, #93c5fd 100%); border-radius: 12px; padding: 1.5rem; border: 3px solid #3b82f6; box-shadow: 0 6px 24px rgba(59, 130, 246, 0.3); margin-bottom: 1rem;">
                                    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                                        <div style="font-size: 1.75rem; margin-right: 0.75rem; animation: pulse-icon 1.5s ease-in-out infinite;">🔍</div>
                                        <div style="font-size: 1.2rem; font-weight: 700; color: #1e40af; text-shadow: 0 1px 2px rgba(255, 255, 255, 0.5);">Searching the web for vehicle info...</div>
                                    </div>
                                    <div style="background: rgba(255, 255, 255, 0.8); border-radius: 8px; height: 12px; overflow: hidden; margin-bottom: 0.5rem; position: relative; border: 2px solid #3b82f6;">
                                        <div style="background: linear-gradient(90deg, #3b82f6 0%, #60a5fa 25%, #2dd4bf 50%, #14b8a6 75%, #3b82f6 100%); height: 100%; width: 50%; position: absolute; animation: progress-slide 1.5s ease-in-out infinite; box-shadow: 0 0 12px rgba(59, 130, 246, 0.6);"></div>
                                    </div>
                                    <div style="text-align: center; font-size: 0.875rem; color: #1e3a8a; font-weight: 500; margin-top: 0.5rem;">may take 5-10 seconds</div>
                                </div>
                                <style>
                                    @keyframes progress-slide {
                                        0% { 
                                            left: -50%; 
                                        }
                                        100% { 
                                            left: 100%; 
                                        }
                                    }
                                    @keyframes pulse-icon {
                                        0%, 100% { 
                                            transform: scale(1); 
                                            opacity: 1;
                                        }
                                        50% { 
                                            transform: scale(1.1); 
                                            opacity: 0.8;
                                        }
                                    }
                                </style>
                                """, unsafe_allow_html=True)
                            
                            # Process vehicle (single API call gets all specs at once)
                            # Process vehicle with current buyer ID
                            vehicle_data = process_vehicle(
                                year_int, 
                                make_input, 
                                model_input, 
                                user_id=current_buyer_id
                            )
                            
                            # Clear progress indicator
                            progress_container.empty()
                            
                            # Mark this vehicle as processed to prevent duplicate processing
                            st.session_state['last_processed_vehicle'] = vehicle_id
                        else:
                            # Use the existing vehicle data from session state
                            vehicle_data = {
                                'curb_weight_lbs': st.session_state.get('last_curb_weight'),
                                'aluminum_engine': st.session_state.get('last_aluminum_engine'),
                                'aluminum_rims': st.session_state.get('last_aluminum_rims'),
                                'catalytic_converters': st.session_state.get('last_catalytic_converters')
                            }
                        
                        if vehicle_data is None:
                            # Vehicle validation failed - it's fake or doesn't exist
                            # Clear pending search on error
                            if 'pending_search' in st.session_state:
                                del st.session_state['pending_search']
                            safe_make = _escape_html(make_input)
                            safe_model = _escape_html(model_input)
                            safe_year = _escape_html(year_int)
                            st.markdown(f"""
                            <div class="error-message">
                                <strong>Vehicle Not Found:</strong> {safe_year} {safe_make} {safe_model} does not appear to be a real vehicle or was not manufactured in this year. Please check your input.
                            </div>
                            """, unsafe_allow_html=True)
                        elif 'error' in vehicle_data and vehicle_data['error']:
                            # API call failed (503, timeout, etc.)
                            # Clear pending search on error
                            if 'pending_search' in st.session_state:
                                del st.session_state['pending_search']
                            error_msg = vehicle_data['error']
                            st.markdown(f"""
                            <div class="error-message">
                                <strong>Search Error:</strong> Unable to search for vehicle data due to a temporary issue.
                            </div>
                            """, unsafe_allow_html=True)
                            st.error(f"Error details: {error_msg}")
                            st.info("💡 **What to do next:**\n- Try again in a few moments (API might be overloaded)\n- Use the Manual Entry option below if you know the vehicle's curb weight")
                        elif vehicle_data and vehicle_data.get('curb_weight_lbs'):
                            # Display simple success message
                            safe_make = _escape_html(make_input)
                            safe_model = _escape_html(model_input)
                            safe_year = _escape_html(year_int)
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); padding: 1rem 1.5rem; border-radius: 8px; border: 3px solid #16a34a; margin: 1rem 0; color: #15803d; font-weight: 600; box-shadow: 0 4px 12px rgba(22, 163, 74, 0.2);">
                                ✅ <strong>Vehicle Found!</strong> {safe_year} {safe_make} {safe_model}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Store the detailed vehicle info for display on the right
                            # Check if we have confidence information from staged resolver
                            confidence_info = vehicle_data.get('confidence_scores', {})
                            validation_warnings = vehicle_data.get('warnings', [])
                            source_attribution = vehicle_data.get('source_attribution', {})
                            citations = vehicle_data.get('citations', {})
                            
                            st.session_state['detailed_vehicle_info'] = {
                                'year': year_int,
                                'make': make_input,
                                'model': model_input,
                                'weight': vehicle_data['curb_weight_lbs'],
                                'aluminum_engine': vehicle_data['aluminum_engine'],
                                'aluminum_rims': vehicle_data['aluminum_rims'],
                                'catalytic_converters': vehicle_data['catalytic_converters'],
                                'confidence_scores': confidence_info,
                                'validation_warnings': validation_warnings,
                                'source_attribution': source_attribution,
                                'citations': citations,
                                'cat_value_override': vehicle_data.get('cat_value_override'),
                                'run_id': vehicle_data.get('run_id')
                            }
                            
                            # Store the data in session state for the cost estimator
                            st.session_state['last_curb_weight'] = vehicle_data['curb_weight_lbs']
                            st.session_state['last_aluminum_engine'] = vehicle_data['aluminum_engine']
                            st.session_state['last_aluminum_rims'] = vehicle_data['aluminum_rims']
                            st.session_state['last_catalytic_converters'] = vehicle_data['catalytic_converters']
                            st.session_state['last_cat_value_override'] = vehicle_data.get('cat_value_override')
                            st.session_state['last_vehicle_info'] = f"{year_int} {make_input} {model_input}"
                            
                            # Auto-populate and calculate the cost estimator
                            st.session_state['auto_calculate'] = True
                            # Clear pending search before rerun now that we have new data
                            if 'pending_search' in st.session_state:
                                del st.session_state['pending_search']
                            
                            # Reset input fields after successful search
                            # Note: Cannot directly modify widget state keys during script execution
                            # Widgets will maintain their values, which is acceptable UX
                            # Users can manually clear fields if needed
                            
                            # Clear dropdown previous values to reset dropdowns to "Choose from list"
                            if 'make_dropdown_previous' in st.session_state:
                                del st.session_state['make_dropdown_previous']
                            if 'model_dropdown_previous' in st.session_state:
                                del st.session_state['model_dropdown_previous']
                            
                            # Clear any dynamic text input keys that might be cached
                            # These keys are generated dynamically, so we clear them by pattern
                            keys_to_delete = []
                            for key in list(st.session_state.keys()):
                                if key.startswith('make_input_text_') or key.startswith('model_input_text_'):
                                    keys_to_delete.append(key)
                            for key in keys_to_delete:
                                del st.session_state[key]
                            
                            # Reset dropdown selections by clearing their session state
                            # This ensures they default to "Choose from list" (index 0)
                            if 'make_input_dropdown' in st.session_state:
                                del st.session_state['make_input_dropdown']
                            if 'model_input_dropdown' in st.session_state:
                                del st.session_state['model_input_dropdown']
                            
                            # Clear prompt states
                            if 'make_prompt_pending' in st.session_state:
                                del st.session_state['make_prompt_pending']
                            if 'make_suggestion' in st.session_state:
                                del st.session_state['make_suggestion']
                            if 'model_prompt_pending' in st.session_state:
                                del st.session_state['model_prompt_pending']
                            if 'model_suggestion' in st.session_state:
                                del st.session_state['model_suggestion']
                            
                            # Refresh the page to show the updated vehicle details and cost estimate
                            st.rerun()
                        else:
                            # API succeeded but curb weight not found in search results
                            # Clear pending search on error
                            if 'pending_search' in st.session_state:
                                del st.session_state['pending_search']
                            
                            # Check if we got any other fields successfully
                            has_partial_data = any([
                                vehicle_data.get('aluminum_engine') is not None,
                                vehicle_data.get('aluminum_rims') is not None,
                                vehicle_data.get('catalytic_converters') is not None
                            ])
                            
                            # Determine if vehicle likely doesn't exist (no data found at all)
                            # vs. vehicle exists but just missing curb weight
                            critical_fields_found = sum([
                                vehicle_data.get('aluminum_engine') is not None,
                                vehicle_data.get('aluminum_rims') is not None,
                                vehicle_data.get('catalytic_converters') is not None
                            ])
                            
                            vehicle_likely_doesnt_exist = (critical_fields_found == 0)
                            
                            if vehicle_likely_doesnt_exist:
                                # Vehicle doesn't appear to exist
                                safe_make = _escape_html(make_input)
                                safe_model = _escape_html(model_input)
                                safe_year = _escape_html(year_int)
                                st.markdown(f"""
                                <div class="warning-message" style="background-color: #fee2e2; border-left: 4px solid #dc2626;">
                                    <strong>⚠️ Vehicle Not Found:</strong> Unable to find a <strong>{safe_year} {safe_make} {safe_model}</strong> in our search results.
                                    <br><br>
                                    <strong>Please verify:</strong>
                                    <ul style="margin: 0.5rem 0 0 1rem; padding-left: 1rem;">
                                        <li>Year is correct (this make/model may not have been produced in {year_int})</li>
                                        <li>Make and model names are spelled correctly</li>
                                        <li>This vehicle actually exists (not a concept car or unreleased model)</li>
                                    </ul>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                st.info("💡 **Suggestions:**\n- Check if this model was produced in a different year range\n- Try searching for a similar year (e.g., try years +/- 2 years)\n- Verify the spelling of the make and model\n- If you're certain this vehicle exists, use Manual Entry below")
                            else:
                                # Vehicle exists but curb weight not found
                                st.markdown("""
                                <div class="warning-message">
                                    <strong>Curb Weight Not Found:</strong> The search completed but could not find reliable curb weight data for this vehicle.
                                </div>
                                """, unsafe_allow_html=True)
                                
                                if has_partial_data:
                                    st.info(f"ℹ️ **Found partial data:**")
                                    cols = st.columns(3)
                                    if vehicle_data.get('aluminum_engine') is not None:
                                        cols[0].write(f"✓ Aluminum Engine: {vehicle_data['aluminum_engine']}")
                                    if vehicle_data.get('aluminum_rims') is not None:
                                        cols[1].write(f"✓ Aluminum Rims: {vehicle_data['aluminum_rims']}")
                                    if vehicle_data.get('catalytic_converters') is not None:
                                        cols[2].write(f"✓ Cat Converters: {vehicle_data['catalytic_converters']}")
                                
                                st.info("💡 **What to do next:**\n- Try a different model year (curb weight data may be available for nearby years)\n- Use the Manual Entry option below if you know the vehicle's curb weight")
            except ValueError:
                # Clear pending search on error
                if 'pending_search' in st.session_state:
                    del st.session_state['pending_search']
                st.markdown("""
                <div class="warning-message">
                    <strong>Invalid Year:</strong> Please enter a valid year (e.g., 2023).
                </div>
                """, unsafe_allow_html=True)


# --- Right Column: Cost Estimator Results ---
with right_col:
    st.markdown('<div class="section-header">Cost Estimate</div>', unsafe_allow_html=True)
    
    # Create a container for cost estimate results that can be cleared
    cost_estimate_container = st.empty()
    
    # Skip display entirely if we're in pending search state
    if st.session_state.get('pending_search'):
        with cost_estimate_container.container():
            st.info("Searching for vehicle...")
    else:
        # Auto-calculate if vehicle was just searched and we have valid data
        if st.session_state.get('auto_calculate', False) and st.session_state.get('last_curb_weight') is not None:
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
                
                # Use stored count if available; otherwise rely on default average (CATS_PER_CAR) in compute_commodities
                catalytic_converters = st.session_state.get('last_catalytic_converters')
                cat_value_override = st.session_state.get('last_cat_value_override')

                # Get stored purchase price and tow fee, or use defaults
                stored_results = st.session_state.get('calculation_results')
                if stored_results:
                    purchase_price = stored_results.get('purchase_price', FLAT_COSTS["PURCHASE"])
                    tow_fee = stored_results.get('tow_fee', FLAT_COSTS["TOW"])
                else:
                    purchase_price = FLAT_COSTS["PURCHASE"]
                    tow_fee = FLAT_COSTS["TOW"]
            
                # Perform the calculation
                commodities = compute_commodities(cars_int, curb_weight_int, aluminum_engine, aluminum_rims, catalytic_converters=catalytic_converters, cat_value_override=cat_value_override)
                totals = calculate_totals(commodities, cars_int, curb_weight_int, purchase_price, tow_fee)
                
                # Store results in session state
                st.session_state['calculation_results'] = {
                    'commodities': commodities,
                    'totals': totals,
                    'cars': cars_int,
                    'curb_weight': curb_weight_int,
                    'purchase_price': purchase_price,
                    'tow_fee': tow_fee
                }
                
            except Exception as e:
                st.error(f"Error during auto-calculation: {e}")
        
        # Check if we have vehicle data to show results
        if st.session_state.get('last_curb_weight') is not None:
                # If no calculation results yet, calculate them
                if 'calculation_results' not in st.session_state or st.session_state.get('calculation_results') is None:
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
                        
                        # Use stored count if available; otherwise rely on default average (CATS_PER_CAR)
                        catalytic_converters = st.session_state.get('last_catalytic_converters')
                        cat_value_override = st.session_state.get('last_cat_value_override')

                        # Use default purchase price and tow fee for initial calculation
                        purchase_price = FLAT_COSTS["PURCHASE"]
                        tow_fee = FLAT_COSTS["TOW"]
                        
                        # Perform the calculation
                        commodities = compute_commodities(cars_int, curb_weight_int, aluminum_engine, aluminum_rims, catalytic_converters=catalytic_converters, cat_value_override=cat_value_override)
                        totals = calculate_totals(commodities, cars_int, curb_weight_int, purchase_price, tow_fee)
                        
                        # Store results in session state
                        st.session_state['calculation_results'] = {
                            'commodities': commodities,
                            'totals': totals,
                            'cars': cars_int,
                            'curb_weight': curb_weight_int,
                            'purchase_price': purchase_price,
                            'tow_fee': tow_fee
                        }
                    except Exception as e:
                        st.error(f"Error during calculation: {e}")
                        st.stop()
                
                # Display calculation results
                results = st.session_state.get('calculation_results')
                if results is None:
                    # If results are still None after calculation attempt, skip display
                    st.warning("Unable to calculate results. Please try searching again.")
                else:
                    commodities = results['commodities']
                    totals = results['totals']
                    
                    # Validate pricing conventions
                    validation_errors = validate_pricing_conventions(commodities, totals)
                    if validation_errors:
                        st.error("Pricing validation errors detected:")
                        for error in validation_errors:
                            st.error(f"• {error}")
                    
                    # Display summary metrics with semantic colors
                    # Row 1: Net Profit (full width)
                    profit_colors = get_semantic_colors(
                        totals["net"],
                        "profit",
                        minimum_goal_profit=MINIMUM_GOAL_PROFIT,
                    )
                    profit_bg = profit_colors["background"]
                    profit_border = profit_colors["border"]
                    profit_text = profit_colors["text"]
                    st.markdown(f"""
                <div style="background: {profit_bg}; padding: 1.5rem; border-radius: 8px; border: 1px solid {profit_border}; margin-bottom: 1rem; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);">
                    <div style="text-align: center;">
                        <div style="font-size: 0.875rem; color: {profit_text}; font-weight: 600; margin-bottom: 0.25rem;">NET PROFIT</div>
                        <div style="font-size: 2rem; color: {profit_text}; font-weight: 700; white-space: nowrap;">{format_currency(totals["net"])}</div>
                    </div>
                </div>
                    """, unsafe_allow_html=True)
                    
                    # Row 2: Total Sale Value and Total Costs (side by side)
                    col1, col2 = st.columns(2)
                    with col1:
                        # Total Sale Value - Blue/Info styling
                        st.markdown(f"""
                <div style="background: #eff6ff; padding: 1rem; border-radius: 8px; border: 1px solid #bfdbfe; margin-bottom: 1rem;">
                    <div style="text-align: center;">
                        <div style="font-size: 0.75rem; color: #1e40af; font-weight: 600; margin-bottom: 0.25rem; text-transform: uppercase;">Total Sale Value</div>
                        <div style="font-size: 1.25rem; color: #1e40af; font-weight: 700; white-space: nowrap;">{format_currency(totals["total_sale"])}</div>
                    </div>
                </div>
                    """, unsafe_allow_html=True)
                    with col2:
                        # Total Costs - Neutral styling
                        st.markdown(f"""
                <div style="background: #f8fafc; padding: 1rem; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 1rem;">
                    <div style="text-align: center;">
                        <div style="font-size: 0.75rem; color: #64748b; font-weight: 600; margin-bottom: 0.25rem; text-transform: uppercase;">Total Costs</div>
                        <div style="font-size: 1.25rem; color: #0f172a; font-weight: 700; white-space: nowrap;">{format_currency(totals["total_costs"])}</div>
                    </div>
                </div>
                    """, unsafe_allow_html=True)
                

                

                
                # Separate commodities by estimation method and add confidence indicators
                weight_based = []
                count_based = []
                
                # Note: Confidence badges will be added later during display rendering
                # to avoid duplication when creating enhanced display tables
                for commodity in commodities:
                    
                    if commodity.get("is_count_based"):
                        count_based.append({
                            "Commodity": commodity["label"],
                            "Count": f"{commodity['weight']:.2f}",
                            "Price/Unit": f"${commodity['unit_price']:.2f}",
                            "Sale Value": f"${commodity['sale_value']:.2f}"
                        })
                    elif commodity.get("is_special"):
                        count_based.append({
                            "Commodity": commodity["label"],
                            "Count": f"{commodity['weight']:.0f}",
                            "Price/Unit": f"${commodity['unit_price']:.2f}",
                            "Sale Value": f"${commodity['sale_value']:.2f}"
                        })
                    else:
                        # Filter out zero-weight engine entries
                        if commodity.get("is_engine") and commodity["weight"] == 0:
                            continue
                        
                        weight_based.append({
                            "Commodity": commodity["label"],
                            "Weight (lb)": f"{commodity['weight']:,.1f}",
                            "$/lb": f"${commodity['unit_price']:.2f}",
                            "Sale Value": f"${commodity['sale_value']:.2f}",
                            "is_engine": commodity.get("is_engine", False)
                        })
                
                # --- Mark as Bought UI ---
                current_info = st.session_state.get('detailed_vehicle_info', {})
                current_run_id = current_info.get('run_id')
                
                # Check if we've already marked this specific run as bought in this session
                is_bought_session = st.session_state.get(f'run_bought_{current_run_id}', False)

                if current_run_id:
                    if not is_bought_session:
                        # Toggle key for showing/hiding the buy form
                        buy_form_key = f'show_buy_form_{current_run_id}'
                        show_buy_form = st.session_state.get(buy_form_key, False)
                        
                        # Button to toggle the form
                        if st.button("💰 Bought this car", key=f"buy_button_{current_run_id}", use_container_width=True):
                            st.session_state[buy_form_key] = not show_buy_form
                            st.rerun()
                        
                        # Show form if toggled
                        if show_buy_form:
                            with st.form(key=f"buy_form_{current_run_id}"):
                                st.caption("Record this purchase to your history.")
                                
                                # Get purchase price from current calculation (already submitted)
                                current_calc_price = st.session_state.get('calculation_results', {}).get('purchase_price', 0.0)
                                
                                # Display purchase price (read-only)
                                st.text_input("Purchase Price ($)", value=f"${current_calc_price:,.2f}", disabled=True, key="display_price")
                                
                                b_dispatch = st.text_input("Dispatch Number", help="Enter at least 6 digits (e.g., 123456)", key=f"dispatch_{current_run_id}")
                                
                                if st.form_submit_button("Confirm Purchase", type="primary", use_container_width=True):
                                    if not b_dispatch:
                                        st.error("Please enter a dispatch number.")
                                    elif not is_valid_dispatch_number(b_dispatch):
                                        st.error("Dispatch number must be at least 6 digits (e.g., 123456).")
                                    else:
                                        success = mark_run_bought(current_run_id, current_calc_price, b_dispatch)
                                        if success:
                                            st.session_state[f'run_bought_{current_run_id}'] = True
                                            st.session_state[buy_form_key] = False
                                            st.success("Purchase recorded! 🎉")
                                            time.sleep(1) # Brief pause to show success
                                            st.rerun()
                                        else:
                                            st.error("Failed to record purchase. It may have already been marked or the ID is invalid.")
                    else:
                         st.markdown("""
                         <div style="background: #ecfdf5; color: #065f46; padding: 1rem; border-radius: 8px; border: 1px solid #6ee7b7; margin-top: 1rem; text-align: center;">
                            <strong>✓ Purchase Recorded</strong>
                         </div>
                         """, unsafe_allow_html=True)
                
                # --- Purchase Price and Tow Fee Adjustment ---
                with st.form(key="cost_adjustment_form_right"):
                    col1_r, col2_r = st.columns(2)
                    with col1_r:
                        purchase_price_input = st.text_input("Purchase Price ($)", value=str(int(FLAT_COSTS["PURCHASE"])), key="purchase_adjustment_right")
                    with col2_r:
                        tow_fee_input = st.text_input("Tow Fee ($)", value=str(int(FLAT_COSTS["TOW"])), key="tow_adjustment_right")
                    recalculate_button_r = st.form_submit_button("🔄 Update Costs", width='stretch')
                    if recalculate_button_r:
                        try:
                            purchase_price_float = float(purchase_price_input.strip())
                            tow_fee_float = float(tow_fee_input.strip())
                            if purchase_price_float < 0 or tow_fee_float < 0:
                                st.error("Purchase price and tow fee must be non-negative values.")
                            else:
                                results = st.session_state.get('calculation_results', {})
                                if results:
                                    commodities = compute_commodities(results['cars'], results['curb_weight'],
                                                                    st.session_state.get('last_aluminum_engine'),
                                                                    st.session_state.get('last_aluminum_rims'),
                                                                    catalytic_converters=st.session_state.get('last_catalytic_converters'),
                                                                    cat_value_override=st.session_state.get('last_cat_value_override'))
                                    totals = calculate_totals(commodities, results['cars'], results['curb_weight'],
                                                            purchase_price_float, tow_fee_float)
                                    st.session_state['calculation_results'] = {
                                        'commodities': commodities,
                                        'totals': totals,
                                        'cars': results['cars'],
                                        'curb_weight': results['curb_weight'],
                                        'purchase_price': purchase_price_float,
                                        'tow_fee': tow_fee_float
                                    }
                                    st.markdown("""
                                    <div style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); padding: 1rem 1.5rem; border-radius: 8px; border: 3px solid #16a34a; margin: 1rem 0; color: #15803d; font-weight: 600; box-shadow: 0 4px 12px rgba(22, 163, 74, 0.2);">
                                        ✅ <strong>Costs updated and recalculated!</strong>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    st.rerun()
                        except ValueError:
                            st.error("Please enter valid numbers for purchase price and tow fee.")
                        except Exception as e:
                            st.error(f"Error during recalculation: {e}")

                # Display weight-based commodities
                if weight_based:
                    st.markdown('<div class="subsection-header">Estimated by Weight</div>', unsafe_allow_html=True)
                    
                    # Create display dataframe
                    display_df = pd.DataFrame(weight_based)
                    display_df = display_df.drop('is_engine', axis=1)
                    
                    # Display the table
                    st.dataframe(display_df, width='stretch', hide_index=True)
                    
                    # Check if there are engine commodities and add a small note below the chart
                    engine_commodities = [item for item in weight_based if item.get('is_engine')]
                    if engine_commodities:
                        info_text = (
                            f"Engine weight estimated at {ENGINE_WEIGHT_PERCENT*100:.1f}% of curb weight. "
                            f"For unknown materials, weight is split {UNKNOWN_ENGINE_SPLIT_AL_PCT*100:.0f}% Al / {100-UNKNOWN_ENGINE_SPLIT_AL_PCT*100:.0f}% Fe."
                        )
                        st.caption(info_text)
                
                # Display count-based commodities  
                if count_based:
                    st.markdown('<div class="subsection-header">Estimated by Count</div>', unsafe_allow_html=True)
                    
                    # Display count-based commodities
                    count_df = pd.DataFrame(count_based)
                    
                    st.dataframe(count_df, width='stretch', hide_index=True)
                

                
                # Display detailed cost breakdown
                st.markdown('<div class="subsection-header">Cost Breakdown</div>', unsafe_allow_html=True)
                
                # Determine Nut fee description based on admin setting
                # Get current config to ensure we have the latest settings
                current_config = get_config()
                grounding_settings = current_config["grounding_settings"]
                nut_fee_applies_to = grounding_settings.get("nut_fee_applies_to", "curb_weight")
                nut_fee_description = f"Nut Fee ({'ELV' if nut_fee_applies_to == 'elv_weight' else 'Curb'} Weight)"
                
                # Create summary DataFrame with better formatting
                summary_data = [
                    {"Item": "Total Sale", "Amount": format_currency(totals["total_sale"]), "Type": "Revenue"},
                    {"Item": "Purchase Cost", "Amount": format_currency(totals['purchase']), "Type": "Cost"},
                    {"Item": "Tow Fee", "Amount": format_currency(totals['tow']), "Type": "Cost"},
                    {"Item": "Lead Fee", "Amount": format_currency(totals['lead']), "Type": "Cost"},
                    {"Item": nut_fee_description, "Amount": format_currency(totals['nut']), "Type": "Cost"},
                    {"Item": "Total Costs", "Amount": format_currency(totals['total_costs']), "Type": "Cost"},
                    {"Item": "Net Profit", "Amount": format_currency(totals['net']), "Type": "Net"},
                ]
                
                summary_df = pd.DataFrame(summary_data)
                
                def _style_profit_row(row: pd.Series):
                    if str(row.get("Item", "")).strip().lower() != "net profit":
                        return [""] * len(row)
                    colors = get_semantic_colors(
                        float(totals["net"]),
                        "profit",
                        minimum_goal_profit=MINIMUM_GOAL_PROFIT,
                    )
                    # Highlight the full row, with stronger emphasis on the Amount cell.
                    styles = [""] * len(row)
                    for i, col in enumerate(row.index):
                        if col == "Amount":
                            styles[i] = (
                                f"background-color: {colors['background']};"
                                f"color: {colors['text']};"
                                f"font-weight: 700;"
                            )
                        else:
                            styles[i] = f"background-color: {colors['background']};"
                    return styles

                st.dataframe(
                    summary_df.style.apply(_style_profit_row, axis=1),
                    width='stretch',
                    hide_index=True,
                )
        
        else:
            # Show a message when no vehicle has been searched yet
            st.markdown("""
            <div style="background: #f8fafc; padding: 3rem 1.5rem; border-radius: 8px; text-align: center; border: 1px dashed #cbd5e1;">
                <h3 style="color: #64748b; margin: 0; font-size: 1rem; font-weight: 500;">Search for a vehicle to view estimate</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Show manual entry option when no vehicle is selected
            with st.expander("Enter curb weight manually", expanded=False):
                with st.form(key="manual_calc_form_no_vehicle"):
                    col1, col2 = st.columns(2)
                    with col1:
                        cars_input = st.text_input("Number of Cars", placeholder="e.g., 1", value="1", key="cars_no_vehicle")
                    with col2:
                        curb_weight_input = st.text_input("Curb Weight per Car (lb)", placeholder="e.g., 3600", value="3600", key="weight_no_vehicle")
                    
                    # Purchase Price and Tow Fee
                    col1, col2 = st.columns(2)
                    with col1:
                        purchase_price_input = st.text_input("Purchase Price ($)", value=str(int(FLAT_COSTS["PURCHASE"])), key="purchase_no_vehicle")
                    with col2:
                        tow_fee_input = st.text_input("Tow Fee ($)", value=str(int(FLAT_COSTS["TOW"])), key="tow_no_vehicle")
                    
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
                    
                    manual_calculate_button = st.form_submit_button(label="Calculate Estimate", width='stretch')
                    
                    # Handle manual calculation
                    if manual_calculate_button:
                        try:
                            cars_int = int(cars_input.strip())
                            curb_weight_int = int(curb_weight_input.strip())
                            purchase_price_float = float(purchase_price_input.strip())
                            tow_fee_float = float(tow_fee_input.strip())
                            
                            # Validate values are non-negative
                            if cars_int <= 0 or curb_weight_int <= 0 or purchase_price_float < 0 or tow_fee_float < 0:
                                st.error("Please enter positive values for cars and curb weight, and non-negative values for purchase price and tow fee.")
                            else:
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
                                
                                # Perform the calculation (use default average cats when not provided)
                                commodities = compute_commodities(cars_int, curb_weight_int, aluminum_engine, aluminum_rims, catalytic_converters=None)
                                totals = calculate_totals(commodities, cars_int, curb_weight_int, purchase_price_float, tow_fee_float)
                            
                                # Store results in session state
                                st.session_state['calculation_results'] = {
                                    'commodities': commodities,
                                    'totals': totals,
                                    'cars': cars_int,
                                    'curb_weight': curb_weight_int,
                                    'purchase_price': purchase_price_float,
                                    'tow_fee': tow_fee_float
                                }
                                
                                # Update session state with new values
                                st.session_state['last_curb_weight'] = curb_weight_int
                                st.session_state['last_aluminum_engine'] = aluminum_engine
                                st.session_state['last_aluminum_rims'] = aluminum_rims
                                # Leave converter count unset so default average is used in calculations
                                st.session_state['last_catalytic_converters'] = None
                                st.session_state['last_vehicle_info'] = f"Manual Entry ({curb_weight_int} lbs)"
                                
                                # Create detailed vehicle info for display
                                st.session_state['detailed_vehicle_info'] = {
                                    'year': 'Manual',
                                    'make': 'Entry',
                                    'model': f'{curb_weight_int} lbs',
                                    'weight': curb_weight_int,
                                    'aluminum_engine': aluminum_engine,
                                    'aluminum_rims': aluminum_rims,
                                    'catalytic_converters': None
                                }
                                
                                st.markdown("""
                                <div style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); padding: 1rem 1.5rem; border-radius: 8px; border: 3px solid #16a34a; margin: 1rem 0; color: #15803d; font-weight: 600; box-shadow: 0 4px 12px rgba(22, 163, 74, 0.2);">
                                    ✅ <strong>Manual estimate calculated!</strong>
                                </div>
                                """, unsafe_allow_html=True)
                                st.rerun()
                            
                        except ValueError:
                            st.error("Please enter valid numbers for cars, curb weight, purchase price, and tow fee.")
                        except Exception as e:
                            st.error(f"Error during calculation: {e}")




# --- Footer ---
st.markdown("---")

# Add title at bottom in smaller format
st.markdown("""
<div style="text-align: center; margin-top: 5rem; padding-bottom: 2rem;">
    <p style="margin: 0; font-size: 0.85rem; color: #990C41; font-weight: 600;">
        Ruby G.E.M. <span style="font-weight: 400; color: #6b7280;">· General Estimation Model</span>
    </p>
    <p style="margin: 0.5rem 0 0 0; font-size: 0.8rem; color: #9ca3af;">
        Built with Streamlit | v1.0
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

            # Optionally bootstrap an admin user from environment variables
            try:
                bootstrap_username = os.getenv("ADMIN_BOOTSTRAP_USERNAME", "").strip()
                bootstrap_password = os.getenv("ADMIN_BOOTSTRAP_PASSWORD", "").strip()
                if bootstrap_username and bootstrap_password:
                    ok, msg = ensure_admin_user(username=bootstrap_username, passcode=bootstrap_password)
                    if ok:
                        print(f"✅ {msg}")
                    else:
                        print(f"⚠️ Could not ensure admin user: {msg}")
                else:
                    print("ℹ️ Admin bootstrap skipped (set ADMIN_BOOTSTRAP_USERNAME and ADMIN_BOOTSTRAP_PASSWORD to enable).")
            except Exception as e:
                print(f"⚠️ Error ensuring admin user: {e}")

            # Ensure catalog cache is loaded (static, no database rebuild)
            try:
                from vehicle_data import ensure_catalog_cached
                print("📚 Loading static catalog from seed_catalog.json...")
                cache_data = ensure_catalog_cached()
                if cache_data and cache_data.get("make_index", {}).get("all_makes"):
                    make_count = len(cache_data["make_index"]["all_makes"])
                    model_count = sum(len(models.get("all_models", [])) for models in cache_data.get("model_index_by_make", {}).values())
                    print(f"✅ Static catalog loaded: {make_count} makes, {model_count} models")
                else:
                    print("⚠️ Catalog cache is empty or invalid")
            except Exception as e:
                print(f"⚠️ Error loading catalog cache: {e}")

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
if 'last_catalytic_converters' not in st.session_state:
    st.session_state['last_catalytic_converters'] = None
if 'last_cat_value_override' not in st.session_state:
    st.session_state['last_cat_value_override'] = None
if 'last_vehicle_info' not in st.session_state:
    st.session_state['last_vehicle_info'] = None
if 'auto_calculate' not in st.session_state:
    st.session_state['auto_calculate'] = False
if 'detailed_vehicle_info' not in st.session_state:
    st.session_state['detailed_vehicle_info'] = None
