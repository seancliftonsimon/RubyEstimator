import streamlit as st
from dotenv import load_dotenv
import logging
import sys

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
logger.info("="*70)
logger.info("🚀 Ruby GEM Application Starting...")
logger.info("="*70)

# Configure page with light mode styling (must be first Streamlit command)
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

logger.info("✓ Streamlit page configured")

import pandas as pd
from vehicle_data import process_vehicle, get_last_ten_entries
from auth import setup_password_protection
from database_config import test_database_connection, get_database_info, get_app_config, upsert_app_config

logger.info("✓ Core modules imported")
from confidence_ui import (
    render_confidence_badge, render_warning_banner, 
    add_confidence_css
)
# Simplified UI components no longer needed - using inline progress indicator
from typing import Dict, Any
import os
from styles import generate_main_app_css, generate_admin_mode_css, get_semantic_colors, Colors

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

def _merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for k, v in (override or {}).items():
        # Shallow merge is sufficient for flat dicts
        merged[k] = v
    return merged

@st.cache_data(show_spinner=False)
def load_db_config() -> Dict[str, Any]:
    return get_app_config() or {}

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

def render_admin_ui():
    """Render the admin configuration UI with restore to default functionality."""
    st.markdown('<div class="main-title">⚙️ Admin Configuration</div>', unsafe_allow_html=True)
    
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
    if 'restore_heuristics' not in st.session_state:
        st.session_state['restore_heuristics'] = False
    if 'restore_grounding' not in st.session_state:
        st.session_state['restore_grounding'] = False
    if 'restore_consensus' not in st.session_state:
        st.session_state['restore_consensus'] = False
    
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

    with st.form("admin_settings_form"):
        st.markdown("### 📝 Configuration Settings")
        st.markdown("Adjust values below and click **Save All Changes** at the bottom. Use **Restore to Default** buttons to reset individual sections.")

        tab_prices, tab_costs, tab_weights, tab_assumptions, tab_heuristics, tab_grounding, tab_consensus = st.tabs(
            ["💰 Prices", "💵 Costs", "⚖️ Weights", "📊 Assumptions", "🔍 Heuristics", "🌐 Grounding", "🤝 Consensus"]
        )

        with tab_prices:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader("Commodity Prices ($/lb)")
            with col2:
                if st.form_submit_button("🔄 Restore to Default", key="restore_prices_btn"):
                    st.session_state['restore_prices'] = True
            
            if st.session_state.get('restore_prices', False):
                price_df = pd.DataFrame(
                    [(k, float(v)) for k, v in DEFAULT_PRICE_PER_LB.items()], columns=["key", "value"]
                ).sort_values("key").reset_index(drop=True)
                st.session_state['restore_prices'] = False
            else:
                price_df = pd.DataFrame(
                    [(k, float(v)) for k, v in cfg["price_per_lb"].items()], columns=["key", "value"]
                ).sort_values("key").reset_index(drop=True)
            
            price_df = st.data_editor(price_df, width='stretch', num_rows="fixed", hide_index=True)

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
            
            col_fc1, col_fc2, col_fc3, col_fc4 = st.columns(4)
            purchase = col_fc1.number_input("PURCHASE ($)", value=float(costs_to_use["PURCHASE"]))
            tow = col_fc2.number_input("TOW ($)", value=float(costs_to_use["TOW"]))
            lead = col_fc3.number_input("LEAD_PER_CAR ($)", value=float(costs_to_use["LEAD_PER_CAR"]))
            nut = col_fc4.number_input("NUT_PER_LB ($/lb)", value=float(costs_to_use["NUT_PER_LB"]))

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
            
            c1, c2, c3, c4 = st.columns(4)
            rims_al = c1.number_input("Aluminum Rims Weight", value=float(weights_to_use["rims_aluminum_weight_lbs"]))
            battery_baseline = c2.number_input("Battery Baseline", value=float(weights_to_use["battery_baseline_weight_lbs"]))
            harness_w = c3.number_input("Wiring Harness", value=float(weights_to_use["harness_weight_lbs"]))
            fe_rad = c4.number_input("FE Radiator", value=float(weights_to_use["fe_radiator_weight_lbs"]))
            c5, c6, c7, c8, c9 = st.columns(5)
            breakage_w = c5.number_input("Breakage", value=float(weights_to_use["breakage_weight_lbs"]))
            alt_w = c6.number_input("Alternator", value=float(weights_to_use["alternator_weight_lbs"]))
            starter_w = c7.number_input("Starter", value=float(weights_to_use["starter_weight_lbs"]))
            ac_comp_w = c8.number_input("A/C Compressor", value=float(weights_to_use["ac_compressor_weight_lbs"]))
            fuse_box_w = c9.number_input("Fuse Box", value=float(weights_to_use["fuse_box_weight_lbs"]))

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
            
            a1, a2, a3, a4 = st.columns(4)
            engine_pct = a1.number_input("Engine % of curb (0-1)", value=float(assumptions_to_use["engine_weight_percent_of_curb"]))
            battery_recov = a2.number_input("Battery Recovery (0-1)", value=float(assumptions_to_use["battery_recovery_factor"]))
            cats_avg = a3.number_input("Default Cats per Car", value=float(assumptions_to_use["cats_per_car_default_average"]))
            unknown_split = a4.number_input("Unknown Engine Al Split (0-1)", value=float(assumptions_to_use["unknown_engine_split_aluminum_percent"]))

        with tab_heuristics:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader("Heuristics (optional)")
            with col2:
                if st.form_submit_button("🔄 Restore to Default", key="restore_heuristics_btn"):
                    st.session_state['restore_heuristics'] = True
            
            heuristics_to_use = DEFAULT_HEURISTICS if st.session_state.get('restore_heuristics', False) else cfg["heuristics"]
            if st.session_state.get('restore_heuristics', False):
                st.session_state['restore_heuristics'] = False
            
            perf_txt = "\n".join(heuristics_to_use.get("performance_indicators", []))
            v8_txt = "\n".join(heuristics_to_use.get("v8_keywords", []))
            h1, h2, h3 = st.columns([2, 2, 1])
            perf_txt = h1.text_area("Performance Indicators (one per line)", value=perf_txt)
            v8_txt = h2.text_area("V8 Keywords (one per line)", value=v8_txt)
            cats_fallback = h3.number_input("Fallback Cats", value=int(heuristics_to_use.get("fallback_cats_default_if_no_match", 1)))

        with tab_grounding:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader("Grounding Search Settings")
            with col2:
                if st.form_submit_button("🔄 Restore to Default", key="restore_grounding_btn"):
                    st.session_state['restore_grounding'] = True
            
            grounding_to_use = DEFAULT_GROUNDING_SETTINGS if st.session_state.get('restore_grounding', False) else cfg["grounding_settings"]
            if st.session_state.get('restore_grounding', False):
                st.session_state['restore_grounding'] = False
            
            g1, g2, g3, g4 = st.columns(4)
            target_candidates = g1.number_input("Target Candidates", value=int(grounding_to_use["target_candidates"]), min_value=1, max_value=10)
            clustering_tolerance = g2.number_input("Clustering Tolerance", value=float(grounding_to_use["clustering_tolerance"]), min_value=0.01, max_value=1.0, step=0.01)
            confidence_threshold = g3.number_input("Confidence Threshold", value=float(grounding_to_use["confidence_threshold"]), min_value=0.0, max_value=1.0, step=0.01)
            outlier_threshold = g4.number_input("Outlier Threshold", value=float(grounding_to_use["outlier_threshold"]), min_value=0.5, max_value=5.0, step=0.1)
            
            st.subheader("Nut Fee Configuration")
            nut_fee_option = st.selectbox(
                "Nut fee applies to:",
                options=["curb_weight", "elv_weight"],
                index=0 if grounding_to_use["nut_fee_applies_to"] == "curb_weight" else 1,
                format_func=lambda x: "Curb Weight" if x == "curb_weight" else "ELV Weight"
            )

        with tab_consensus:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader("Consensus Algorithm Settings")
            with col2:
                if st.form_submit_button("🔄 Restore to Default", key="restore_consensus_btn"):
                    st.session_state['restore_consensus'] = True
            
            consensus_to_use = DEFAULT_CONSENSUS_SETTINGS if st.session_state.get('restore_consensus', False) else cfg["consensus_settings"]
            if st.session_state.get('restore_consensus', False):
                st.session_state['restore_consensus'] = False
            
            c1, c2 = st.columns(2)
            min_agreement_ratio = c1.number_input("Min Agreement Ratio", value=float(consensus_to_use["min_agreement_ratio"]), min_value=0.0, max_value=1.0, step=0.01)
            
            st.subheader("Source Preferences")
            preferred_sources_txt = "\n".join(consensus_to_use.get("preferred_sources", []))
            preferred_sources_txt = st.text_area("Preferred Sources (one per line)", value=preferred_sources_txt)
            
            st.subheader("Source Weights")
            sw = consensus_to_use.get("source_weights", {})
            sw1, sw2, sw3, sw4 = st.columns(4)
            kbb_weight = sw1.number_input("KBB.com Weight", value=float(sw.get("kbb.com", 1.2)), min_value=0.1, max_value=3.0, step=0.1)
            edmunds_weight = sw2.number_input("Edmunds.com Weight", value=float(sw.get("edmunds.com", 1.2)), min_value=0.1, max_value=3.0, step=0.1)
            manufacturer_weight = sw3.number_input("Manufacturer Weight", value=float(sw.get("manufacturer", 1.5)), min_value=0.1, max_value=3.0, step=0.1)
            default_weight = sw4.number_input("Default Weight", value=float(sw.get("default", 1.0)), min_value=0.1, max_value=3.0, step=0.1)

        # Save button outside all tabs
        st.markdown("---")
        st.markdown("### 💾 Save Changes")
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            save = st.form_submit_button("💾 Save All Changes", width='stretch')
        
        if save:
            # Gather updates
            new_prices = {str(row["key"]): float(row["value"]) for _, row in price_df.iterrows()}
            new_flat = {
                "PURCHASE": float(purchase),
                "TOW": float(tow),
                "LEAD_PER_CAR": float(lead),
                "NUT_PER_LB": float(nut),
            }
            new_weights = {
                "rims_aluminum_weight_lbs": float(rims_al),
                "battery_baseline_weight_lbs": float(battery_baseline),
                "harness_weight_lbs": float(harness_w),
                "fe_radiator_weight_lbs": float(fe_rad),
                "breakage_weight_lbs": float(breakage_w),
                "alternator_weight_lbs": float(alt_w),
                "starter_weight_lbs": float(starter_w),
                "ac_compressor_weight_lbs": float(ac_comp_w),
                "fuse_box_weight_lbs": float(fuse_box_w),
            }
            new_assumptions = {
                "engine_weight_percent_of_curb": float(engine_pct),
                "battery_recovery_factor": float(battery_recov),
                "cats_per_car_default_average": float(cats_avg),
                "unknown_engine_split_aluminum_percent": float(unknown_split),
            }
            new_heuristics = {
                "performance_indicators": [s.strip() for s in perf_txt.splitlines() if s.strip()],
                "v8_keywords": [s.strip() for s in v8_txt.splitlines() if s.strip()],
                "fallback_cats_default_if_no_match": int(cats_fallback),
            }
            new_grounding = {
                "target_candidates": int(target_candidates),
                "clustering_tolerance": float(clustering_tolerance),
                "confidence_threshold": float(confidence_threshold),
                "outlier_threshold": float(outlier_threshold),
                "nut_fee_applies_to": str(nut_fee_option),
            }
            new_consensus = {
                "min_agreement_ratio": float(min_agreement_ratio),
                "preferred_sources": [s.strip() for s in preferred_sources_txt.splitlines() if s.strip()],
                "source_weights": {
                    "kbb.com": float(kbb_weight),
                    "edmunds.com": float(edmunds_weight),
                    "manufacturer": float(manufacturer_weight),
                    "default": float(default_weight),
                }
            }

            # Persist
            updated_by = os.getenv("USER") or os.getenv("USERNAME") or "admin"
            ok = True
            ok &= upsert_app_config("price_per_lb", new_prices, "$/lb commodity prices", updated_by)
            ok &= upsert_app_config("flat_costs", new_flat, "Flat costs", updated_by)
            ok &= upsert_app_config("weights_fixed", new_weights, "Fixed component weights", updated_by)
            ok &= upsert_app_config("assumptions", new_assumptions, "Estimator assumptions", updated_by)
            ok &= upsert_app_config("heuristics", new_heuristics, "Cat count heuristics", updated_by)
            ok &= upsert_app_config("grounding_settings", new_grounding, "Grounding search settings", updated_by)
            ok &= upsert_app_config("consensus_settings", new_consensus, "Consensus algorithm settings", updated_by)

            if ok:
                refresh_config_cache()
                st.success("✅ Settings saved successfully! Reloading configuration...")
                st.rerun()
            else:
                st.error("❌ Failed to save one or more configuration groups. Please try again.")

# Load current config (fallback to defaults)
CONFIG = get_config()

# Make module-level variables for existing functions to use
PRICE_PER_LB = CONFIG["price_per_lb"]
FLAT_COSTS = CONFIG["flat_costs"]

ENGINE_WEIGHT_PERCENT = float(CONFIG["assumptions"]["engine_weight_percent_of_curb"])  # fraction
BATTERY_RECOVERY_FACTOR = float(CONFIG["assumptions"]["battery_recovery_factor"])      # fraction
CATS_PER_CAR = float(CONFIG["assumptions"]["cats_per_car_default_average"])            # count avg
UNKNOWN_ENGINE_SPLIT_AL_PCT = float(CONFIG["assumptions"]["unknown_engine_split_aluminum_percent"])  # fraction

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
def compute_commodities(cars, curb_weight, aluminum_engine=None, aluminum_rims=None, catalytic_converters=None):
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
    list_commodities.append({
        "key": "CATS", 
        "label": "Catalytic Converters",
        "weight": cats_count,  # Store count in weight field for display
        "unit_price": PRICE_PER_LB["CATS"],
        "sale_value": cats_count * PRICE_PER_LB["CATS"],
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

# --- Streamlit App ---

# Check password protection
if not setup_password_protection():
    st.stop()

# Add confidence indicator CSS
add_confidence_css()

# Apply main app CSS from centralized styles module
st.markdown(generate_main_app_css(), unsafe_allow_html=True)

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
    
    /* Hide only keyboard shortcut text (not the label) */
    [data-testid="stExpander"] details summary span[class*="keyboard"],
    [data-testid="stExpander"] details summary span[aria-label*="keyboard"] {
        display: none !important;
    }
    
    /* Disable tooltip popups */
    [data-testid="stExpander"] [title]:hover::after {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Main title with minimal padding
st.markdown('<div class="main-title">🚗 Ruby G.E.M.</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">General Estimation Model</div>', unsafe_allow_html=True)

# Admin toggle - Initialize state
if 'admin_mode' not in st.session_state:
    st.session_state['admin_mode'] = False

if st.session_state['admin_mode']:
    # Apply admin-specific CSS for distinct mode styling
    st.markdown(generate_admin_mode_css(), unsafe_allow_html=True)
    render_admin_ui()
    st.stop()  # Don't show the main app when in admin mode

# Create two columns for the main layout with better spacing
left_col, spacer, right_col = st.columns([1, 0.2, 1])

# --- Left Column: Vehicle Search & Recent Entries ---
with left_col:
    st.markdown("""
    <div class="section-header">
        🚗 Vehicle Search
    </div>
    """, unsafe_allow_html=True)

    # --- Display Current Vehicle Details (if available) ---
    if st.session_state.get('detailed_vehicle_info'):
        vehicle_info = st.session_state['detailed_vehicle_info']
        
        # Display vehicle name with blue styling
        vehicle_name = f"{vehicle_info['year']} {vehicle_info['make']} {vehicle_info['model']}"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); padding: 1rem; border-radius: 8px; border: 3px solid #3b82f6; margin-bottom: 1rem; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);">
            <div style="margin: 0; color: #1e40af; font-weight: 700; text-align: center; text-shadow: 0 1px 2px rgba(255, 255, 255, 0.5); font-size: 1.25rem;">{vehicle_name}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Display vehicle details in the left column
        # Display curb weight, engine, and rims info in four side-by-side boxes
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div style="background: rgba(59, 130, 246, 0.1); padding: 0.5rem; border-radius: 6px; margin: 0.25rem 0; border-left: 3px solid #3b82f6; text-align: center;">
                <strong>Weight</strong><br>
                <span style="color: #1e40af; font-weight: 600;">{vehicle_info['weight']} lbs</span>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if vehicle_info['aluminum_engine'] is not None:
                engine_status = "Al" if vehicle_info['aluminum_engine'] else "Fe"
                engine_color = "#14b8a6" if vehicle_info['aluminum_engine'] else "#f59e0b"
                engine_bg = "rgba(20, 184, 166, 0.1)" if vehicle_info['aluminum_engine'] else "rgba(245, 158, 11, 0.1)"
                
                st.markdown(f"""
                <div style="background: {engine_bg}; padding: 0.5rem; border-radius: 6px; margin: 0.25rem 0; border-left: 3px solid {engine_color}; text-align: center;">
                    <strong>Engine</strong><br>
                    <span style="color: {engine_color}; font-weight: 600;">{engine_status}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: rgba(156, 163, 175, 0.1); padding: 0.5rem; border-radius: 6px; margin: 0.25rem 0; border-left: 3px solid #9ca3af; text-align: center;">
                    <strong>Engine</strong><br>
                    <span style="color: #6b7280;">Unknown</span>
                </div>
                """, unsafe_allow_html=True)
        
        with col3:
            if vehicle_info['aluminum_rims'] is not None:
                rims_status = "Al" if vehicle_info['aluminum_rims'] else "Fe"
                rims_color = "#14b8a6" if vehicle_info['aluminum_rims'] else "#f59e0b"
                rims_bg = "rgba(20, 184, 166, 0.1)" if vehicle_info['aluminum_rims'] else "rgba(245, 158, 11, 0.1)"
                
                st.markdown(f"""
                <div style="background: {rims_bg}; padding: 0.5rem; border-radius: 6px; margin: 0.25rem 0; border-left: 3px solid {rims_color}; text-align: center;">
                    <strong>Rims</strong><br>
                    <span style="color: {rims_color}; font-weight: 600;">{rims_status}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: rgba(156, 163, 175, 0.1); padding: 0.5rem; border-radius: 6px; margin: 0.25rem 0; border-left: 3px solid #9ca3af; text-align: center;">
                    <strong>Rims</strong><br>
                    <span style="color: #6b7280;">Unknown</span>
                </div>
                """, unsafe_allow_html=True)

        with col4:
            if vehicle_info.get('catalytic_converters') is not None:
                cats_count = vehicle_info['catalytic_converters']
                
                st.markdown(f"""
                <div style="background: rgba(59, 130, 246, 0.1); padding: 0.5rem; border-radius: 6px; margin: 0.25rem 0; border-left: 3px solid #3b82f6; text-align: center;">
                    <strong>Cats</strong><br>
                    <span style="color: #1e40af; font-weight: 600;">{cats_count}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: rgba(156, 163, 175, 0.1); padding: 0.5rem; border-radius: 6px; margin: 0.25rem 0; border-left: 3px solid #9ca3af; text-align: center;">
                    <strong>Cats</strong><br>
                    <span style="color: #6b7280;">Unknown</span>
                </div>
                """, unsafe_allow_html=True)
        
        # Display validation warnings if present
        validation_warnings = vehicle_info.get('validation_warnings', [])
        if validation_warnings:
            from confidence_ui import render_warning_banner
            st.markdown("### ⚠️ Data Quality Alerts")
            for warning in validation_warnings:
                render_warning_banner([warning])
        
        # Source attribution removed - using Gemini Search Grounding for all lookups

    # --- Main Form ---
    with st.form(key="vehicle_form"):
        # Add small gaps between columns to prevent rendering issues
        col1, gap1, col2, gap2, col3 = st.columns([3, 0.2, 3, 0.2, 3])
        with col1:
            year_input = st.text_input("Year", placeholder="e.g., 2013", value="2013", key="year_input_main")
        with col2:
            make_input = st.text_input("Make", placeholder="e.g., Toyota", value="Toyota", key="make_input_main")
        with col3:
            model_input = st.text_input("Model", placeholder="e.g., Camry", value="Camry", key="model_input_main")

        submit_button = st.form_submit_button(label="Search Vehicle", width='stretch')

    # --- Progress Area ---
    # Create a container for the progress area that can be shown/hidden
    progress_container = st.empty()

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
                    # Create a unique identifier for this vehicle search
                    vehicle_id = f"{year_int}_{make_input.strip()}_{model_input.strip()}"
                    
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
                                <div style="text-align: center; font-size: 0.875rem; color: #1e3a8a; font-weight: 500; margin-top: 0.5rem;">This may take a few moments...</div>
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
                        vehicle_data = process_vehicle(year_int, make_input.strip(), model_input.strip())
                        
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
                        st.markdown(f"""
                        <div class="error-message">
                            <strong>Vehicle Not Found:</strong> {year_int} {make_input} {model_input} does not appear to be a real vehicle or was not manufactured in this year. Please check your input.
                        </div>
                        """, unsafe_allow_html=True)
                    elif 'error' in vehicle_data and vehicle_data['error']:
                        # API call failed (503, timeout, etc.)
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
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); padding: 1rem 1.5rem; border-radius: 8px; border: 3px solid #16a34a; margin: 1rem 0; color: #15803d; font-weight: 600; box-shadow: 0 4px 12px rgba(22, 163, 74, 0.2);">
                            ✅ <strong>Vehicle Found!</strong> {year_int} {make_input} {model_input}
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
                            'citations': citations
                        }
                        
                        # Store the data in session state for the cost estimator
                        st.session_state['last_curb_weight'] = vehicle_data['curb_weight_lbs']
                        st.session_state['last_aluminum_engine'] = vehicle_data['aluminum_engine']
                        st.session_state['last_aluminum_rims'] = vehicle_data['aluminum_rims']
                        st.session_state['last_catalytic_converters'] = vehicle_data['catalytic_converters']
                        st.session_state['last_vehicle_info'] = f"{year_int} {make_input} {model_input}"
                        
                        # Auto-populate and calculate the cost estimator
                        st.session_state['auto_calculate'] = True
                        # Refresh the page to show the updated vehicle details and cost estimate
                        st.rerun()
                    else:
                        # API succeeded but curb weight not found in search results
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
                            st.markdown(f"""
                            <div class="warning-message" style="background-color: #fee2e2; border-left: 4px solid #dc2626;">
                                <strong>⚠️ Vehicle Not Found:</strong> Unable to find a <strong>{year_int} {make_input} {model_input}</strong> in our search results.
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
                st.markdown("""
                <div class="warning-message">
                    <strong>Invalid Year:</strong> Please enter a valid year (e.g., 2023).
                </div>
                """, unsafe_allow_html=True)

    # --- Display Recent Entries (Minimized) ---
    with st.expander("Recently Searched Vehicles (Last 5)", expanded=False, icon="📋"):
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
                
                display_df['C'] = display_df['catalytic_converters'].apply(lambda x: str(int(x)) if pd.notna(x) else "?")

                # Select and rename columns for display (more compact)
                display_df = display_df[['year', 'make', 'model', 'curb_weight_lbs', 'E', 'W', 'C']]
                display_df.columns = ['Year', 'Make', 'Model', 'Weight', 'E', 'W', 'C']
                
                # Format the dataframe for display
                display_df['Weight'] = display_df['Weight'].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "?")
                
                st.dataframe(display_df, width='stretch', hide_index=True)
                st.caption("E = Engine (Al=Aluminum, Fe=Iron), W = Wheels (Al=Aluminum, St=Steel), C = Catalytic Converters")
            else:
                st.info("No vehicles searched yet.")
        except Exception as e:
            st.error(f"Error fetching recent entries: {e}")

# --- Right Column: Cost Estimator Results ---
with right_col:
    st.markdown("""
    <div class="section-header">
        💰 Cost Estimate
    </div>
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
            
            # Use stored count if available; otherwise rely on default average (CATS_PER_CAR) in compute_commodities
            catalytic_converters = st.session_state.get('last_catalytic_converters')

            # Get stored purchase price and tow fee, or use defaults
            stored_results = st.session_state.get('calculation_results', {})
            purchase_price = stored_results.get('purchase_price', FLAT_COSTS["PURCHASE"])
            tow_fee = stored_results.get('tow_fee', FLAT_COSTS["TOW"])
            
            # Perform the calculation (always use default average cats)
            commodities = compute_commodities(cars_int, curb_weight_int, aluminum_engine, aluminum_rims, catalytic_converters=None)
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
                    
                    # Use stored count if available; otherwise rely on default average (CATS_PER_CAR)
                    catalytic_converters = st.session_state.get('last_catalytic_converters')

                    # Use default purchase price and tow fee for initial calculation
                    purchase_price = FLAT_COSTS["PURCHASE"]
                    tow_fee = FLAT_COSTS["TOW"]
                    
                    # Perform the calculation (always use default average cats)
                    commodities = compute_commodities(cars_int, curb_weight_int, aluminum_engine, aluminum_rims, catalytic_converters=None)
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
            results = st.session_state['calculation_results']
            commodities = results['commodities']
            totals = results['totals']
            
            # Validate pricing conventions
            validation_errors = validate_pricing_conventions(commodities, totals)
            if validation_errors:
                st.error("Pricing validation errors detected:")
                for error in validation_errors:
                    st.error(f"• {error}")
            
            # Display summary metrics with semantic colors
            col1, col2, col3 = st.columns(3)
            with col1:
                # Total Sale Value - Blue/Info styling
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); padding: 1.5rem; border-radius: 12px; border: 3px solid #3b82f6; margin-bottom: 1rem; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);">
                    <div style="text-align: center;">
                        <div style="font-size: 0.875rem; color: #1e40af; font-weight: 600; margin-bottom: 0.5rem;">💰 Total Sale Value</div>
                        <div style="font-size: 1.5rem; color: #1e40af; font-weight: 700;">{format_currency(totals["total_sale"])}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                # Total Costs - Neutral styling
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%); padding: 1.5rem; border-radius: 12px; border: 3px solid #9ca3af; margin-bottom: 1rem; box-shadow: 0 4px 12px rgba(156, 163, 175, 0.2);">
                    <div style="text-align: center;">
                        <div style="font-size: 0.875rem; color: #4b5563; font-weight: 600; margin-bottom: 0.5rem;">📉 Total Costs</div>
                        <div style="font-size: 1.5rem; color: #1f2937; font-weight: 700;">-{format_currency(totals["total_costs"])}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                # Net Profit - Dynamic color based on positive/negative
                profit_colors = get_semantic_colors(totals["net"], "profit")
                profit_bg = "linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%)" if totals["net"] >= 0 else "linear-gradient(135deg, #fee2e2 0%, #fecaca 100%)"
                profit_border = "#16a34a" if totals["net"] >= 0 else "#dc2626"
                profit_text = "#15803d" if totals["net"] >= 0 else "#991b1b"
                profit_icon = "✅" if totals["net"] >= 0 else "⚠️"
                st.markdown(f"""
                <div style="background: {profit_bg}; padding: 1.5rem; border-radius: 12px; border: 3px solid {profit_border}; margin-bottom: 1rem; box-shadow: 0 4px 12px rgba({profit_colors['text']}, 0.2);">
                    <div style="text-align: center;">
                        <div style="font-size: 0.875rem; color: {profit_text}; font-weight: 600; margin-bottom: 0.5rem;">{profit_icon} Net Profit</div>
                        <div style="font-size: 1.5rem; color: {profit_text}; font-weight: 700;">{format_currency(totals["net"])}</div>
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
                                                                catalytic_converters=None)
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
            
            st.dataframe(summary_df, width='stretch', hide_index=True)
            
            # Add provenance and confidence details section
            st.markdown('<div class="subsection-header">Data Quality & Sources</div>', unsafe_allow_html=True)
            
            # Enhanced warning banners with specific guidance
            low_confidence_warnings = []
            medium_confidence_warnings = []
            
            # Check for specific data quality issues
            if any('Engine' in item['Commodity'] for item in weight_based):
                if st.session_state.get('last_aluminum_engine') is None:
                    low_confidence_warnings.append("Engine material unknown - using 50/50 aluminum/iron split. Consider manual verification for accurate pricing.")
                else:
                    medium_confidence_warnings.append("Engine material determined from vehicle specifications - confidence level: medium")
            
            if any('Catalytic' in item['Commodity'] for item in count_based):
                if st.session_state.get('last_catalytic_converters') is None:
                    medium_confidence_warnings.append("Catalytic converter count estimated from vehicle type averages - actual count may vary by trim level")
            
            if any('Rims' in item['Commodity'] for item in weight_based):
                if st.session_state.get('last_aluminum_rims') is None:
                    medium_confidence_warnings.append("Rim material unknown - assuming steel rims. Aluminum rims would increase value significantly.")
            
            # Display warnings with appropriate severity
            if low_confidence_warnings:
                render_warning_banner(low_confidence_warnings)
            
            if medium_confidence_warnings:
                for warning in medium_confidence_warnings:
                    st.markdown(f"""
                    <div class="info-banner" style="
                        background: rgba(59, 130, 246, 0.1);
                        border: 1px solid #3b82f6;
                        border-left: 4px solid #3b82f6;
                        padding: 1rem;
                        border-radius: 6px;
                        margin: 0.5rem 0;
                        color: #1e40af;
                        font-weight: 500;
                    ">
                        ℹ️ {warning}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Add visual highlighting for flagged values
            st.markdown("""
            <div class="data-quality-legend" style="
                background: rgba(248, 250, 252, 0.8);
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 1rem;
                margin: 1rem 0;
            ">
                <h4 style="margin: 0 0 0.5rem 0; color: #334155;">Confidence Level Guide:</h4>
                <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
                    <span style="color: #16a34a;">🟢 HIGH (80%+)</span>
                    <span style="color: #d97706;">🟡 MEDIUM (60-80%)</span>
                    <span style="color: #dc2626;">🔴 LOW (<60%)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    else:
        # Show a message when no vehicle has been searched yet
        st.markdown("""
        <div style="background: rgba(156, 163, 175, 0.1); padding: 2rem; border-radius: 8px; text-align: center; border: 1px solid #9ca3af;">
            <h3 style="color: #6b7280; margin-bottom: 1rem;">Search for a vehicle to see value estimate</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Show manual entry option when no vehicle is selected
        with st.expander("❓ Unknown make/model? Enter curb weight manually", expanded=False, icon="❓"):
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

# Admin button in bottom left corner with absolute positioning
st.markdown("""
<style>
    .admin-button-container {
        position: fixed;
        bottom: 1rem;
        left: 1rem;
        z-index: 999;
    }
</style>
""", unsafe_allow_html=True)

# Use a container for admin button that will be positioned
admin_container = st.container()
with admin_container:
    if st.button("⚙️ Admin" if not st.session_state['admin_mode'] else "✕ Close Admin", 
                 key="admin_toggle_btn",
                 help="Access admin settings to configure default values"):
        st.session_state['admin_mode'] = not st.session_state['admin_mode']
        st.rerun()

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
if 'last_catalytic_converters' not in st.session_state:
    st.session_state['last_catalytic_converters'] = None
if 'last_vehicle_info' not in st.session_state:
    st.session_state['last_vehicle_info'] = None
if 'auto_calculate' not in st.session_state:
    st.session_state['auto_calculate'] = False
if 'detailed_vehicle_info' not in st.session_state:
    st.session_state['detailed_vehicle_info'] = None
