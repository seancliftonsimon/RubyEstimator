import sys
import os
import logging
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_cat_prices():
    print("Testing CatPriceManager...")
    from cat_prices import CatPriceManager
    
    manager = CatPriceManager.get_instance()
    
    # Test cases from the CSV
    test_cases = [
        ("Ford", "Taurus", 3, 212.0),
        ("FORD", "TAURUS", 3, 212.0),
        ("Ford", "taurus", 3, 212.0),
        ("BMW", "X Series", 2, 178.0), # Check space handling
        ("Honda", "Odyssey", 3, 195.0),
        ("Unknown", "Car", None, None)
    ]
    
    for make, model, expected_count, expected_value in test_cases:
        result = manager.get_cat_details(make, model)
        if expected_count is None:
            if result is None:
                print(f"✅ Correctly found no match for {make} {model}")
            else:
                print(f"❌ Unexpected match for {make} {model}: {result}")
        else:
            if result:
                count_match = result['count'] == expected_count
                value_match = result['total_value'] == expected_value
                if count_match and value_match:
                    print(f"✅ Match found for {make} {model}: Count={result['count']}, Value=${result['total_value']}")
                else:
                    print(f"❌ Mismatch for {make} {model}. Expected ({expected_count}, {expected_value}), Got ({result['count']}, {result['total_value']})")
            else:
                print(f"❌ No match found for {make} {model}")

def test_compute_commodities():
    print("\nTesting compute_commodities logic...")
    
    # Create a mock object for streamlit
    mock_st = MagicMock()
    mock_st.session_state = {}
    mock_st.secrets = {}
    mock_st.cache_data = lambda *args, **kwargs: lambda func: func
    
    # Patch the module in sys.modules
    sys.modules['streamlit'] = mock_st
    
    try:
        import app
        # Re-inject the constants that might be missing due to mock
        app.PRICE_PER_LB = {
            "ELV": 0.118, "AL_ENGINE": 0.3525, "FE_ENGINE": 0.2325, "HARNESS": 1.88,
            "FE_RAD": 0.565, "BREAKAGE": 0.26, "ALT": 0.88, "STARTER": 0.73,
            "AC_COMP": 0.55, "FUSE_BOX": 0.82, "BATTERY": 0.36, "AL_RIMS": 1.24,
            "CATS": 92.25, "TIRES": 4.5, "ECM": 1.32
        }
        app.ENGINE_WEIGHT_PERCENT = 0.139
        app.BATTERY_RECOVERY_FACTOR = 0.8
        app.CATS_PER_CAR = 1.36
        app.UNKNOWN_ENGINE_SPLIT_AL_PCT = 0.5
        app.RIMS_AL_WEIGHT_LBS = 40.0
        app.BATTERY_BASELINE_WEIGHT_LBS = 35.0
        app.HARNESS_WEIGHT_LBS = 23.0
        app.FE_RADIATOR_WEIGHT_LBS = 20.5
        app.BREAKAGE_WEIGHT_LBS = 5.0
        app.ALTERNATOR_WEIGHT_LBS = 12.0
        app.STARTER_WEIGHT_LBS = 5.5
        app.AC_COMPRESSOR_WEIGHT_LBS = 13.5
        app.FUSE_BOX_WEIGHT_LBS = 3.5
        
        # Test standard calculation
        print("1. Standard Calculation (No override)")
        commodities = app.compute_commodities(
            cars=1, 
            curb_weight=3000, 
            aluminum_engine=False, 
            aluminum_rims=False, 
            catalytic_converters=1, 
            cat_value_override=None
        )
        
        cat_item = next(c for c in commodities if c['key'] == 'CATS')
        print(f"   Standard Cat Value: ${cat_item['sale_value']:.2f} (Unit: ${cat_item['unit_price']:.2f})")
        
        # Test override calculation
        print("2. Override Calculation")
        override_value = 212.0
        commodities_override = app.compute_commodities(
            cars=1, 
            curb_weight=3000, 
            aluminum_engine=False, 
            aluminum_rims=False, 
            catalytic_converters=3, 
            cat_value_override=override_value
        )
        
        cat_item_override = next(c for c in commodities_override if c['key'] == 'CATS')
        print(f"   Override Cat Value: ${cat_item_override['sale_value']:.2f} (Unit: ${cat_item_override['unit_price']:.2f})")
        
        if abs(cat_item_override['sale_value'] - override_value) < 0.01:
            print("✅ Override value applied correctly")
        else:
            print(f"❌ Override value mismatch. Expected {override_value}, Got {cat_item_override['sale_value']}")

        if cat_item_override['label'] == "Catalytic Converters (Price List)":
            print("✅ Label updated correctly")
        else:
            print(f"❌ Label mismatch. Got '{cat_item_override['label']}'")
            
    except ImportError as e:
        print(f"❌ Failed to import app: {e}")
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    test_cat_prices()
    test_compute_commodities()
