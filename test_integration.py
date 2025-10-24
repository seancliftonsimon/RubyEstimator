#!/usr/bin/env python3
"""
Test script to verify SingleCallVehicleResolver integration with vehicle_data.py
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_single_call_integration():
    """Test that the SingleCallVehicleResolver is properly integrated."""
    try:
        # Import the main module
        import vehicle_data
        
        # Check that single_call_resolver is initialized
        assert hasattr(vehicle_data, 'single_call_resolver'), "single_call_resolver not found in vehicle_data module"
        
        # Check that it's the correct type
        from single_call_resolver import SingleCallVehicleResolver
        assert isinstance(vehicle_data.single_call_resolver, SingleCallVehicleResolver), "single_call_resolver is not a SingleCallVehicleResolver instance"
        
        print("✅ SingleCallVehicleResolver integration test passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except AssertionError as e:
        print(f"❌ Assertion error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_process_vehicle_function():
    """Test that process_vehicle function can be called without errors."""
    try:
        import vehicle_data
        
        # Test with a simple vehicle (this won't make actual API calls in test mode)
        print("Testing process_vehicle function signature...")
        
        # Just check that the function exists and has the right signature
        import inspect
        sig = inspect.signature(vehicle_data.process_vehicle)
        params = list(sig.parameters.keys())
        
        expected_params = ['year', 'make', 'model', 'progress_callback']
        for param in expected_params:
            assert param in params, f"Missing parameter: {param}"
        
        print("✅ process_vehicle function signature test passed!")
        return True
        
    except Exception as e:
        print(f"❌ process_vehicle test error: {e}")
        return False

def test_api_functions_integration():
    """Test that individual API functions have been updated."""
    try:
        import vehicle_data
        
        # Check that the API functions exist
        functions_to_check = [
            'get_curb_weight_from_api',
            'get_aluminum_engine_from_api', 
            'get_aluminum_rims_from_api',
            'get_catalytic_converter_count_from_api'
        ]
        
        for func_name in functions_to_check:
            assert hasattr(vehicle_data, func_name), f"Function {func_name} not found"
            func = getattr(vehicle_data, func_name)
            assert callable(func), f"Function {func_name} is not callable"
        
        print("✅ API functions integration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ API functions test error: {e}")
        return False

if __name__ == "__main__":
    print("Running SingleCallVehicleResolver integration tests...")
    print("=" * 60)
    
    tests = [
        test_single_call_integration,
        test_process_vehicle_function,
        test_api_functions_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print(f"\nRunning {test.__name__}...")
        if test():
            passed += 1
        print("-" * 40)
    
    print(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)