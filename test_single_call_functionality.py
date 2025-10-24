#!/usr/bin/env python3
"""
Test script to verify SingleCallVehicleResolver functionality in vehicle_data.py
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_single_call_resolver_direct():
    """Test SingleCallVehicleResolver directly."""
    try:
        from single_call_resolver import SingleCallVehicleResolver
        
        # Create resolver instance
        resolver = SingleCallVehicleResolver()
        
        # Test with a well-known vehicle (2020 Toyota Camry)
        print("Testing SingleCallVehicleResolver with 2020 Toyota Camry...")
        
        # Note: This will make an actual API call if API key is configured
        result = resolver.resolve_all_specifications(2020, "Toyota", "Camry")
        
        print(f"Result type: {type(result)}")
        print(f"Curb weight: {result.curb_weight_lbs}")
        print(f"Aluminum engine: {result.aluminum_engine}")
        print(f"Aluminum rims: {result.aluminum_rims}")
        print(f"Catalytic converters: {result.catalytic_converters}")
        print(f"Confidence scores: {result.confidence_scores}")
        print(f"Warnings: {result.warnings}")
        
        # Check if we have sufficient confidence
        has_confidence = resolver.has_sufficient_confidence(result)
        print(f"Has sufficient confidence: {has_confidence}")
        
        print("✅ SingleCallVehicleResolver direct test completed!")
        return True
        
    except Exception as e:
        print(f"❌ SingleCallVehicleResolver direct test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_process_vehicle_with_single_call():
    """Test process_vehicle function with SingleCallVehicleResolver integration."""
    try:
        import vehicle_data
        
        print("Testing process_vehicle with SingleCallVehicleResolver integration...")
        
        # Test with a well-known vehicle
        result = vehicle_data.process_vehicle(2020, "Toyota", "Camry")
        
        print(f"Process vehicle result: {result}")
        
        if result:
            print(f"Curb weight: {result.get('curb_weight_lbs')}")
            print(f"Aluminum engine: {result.get('aluminum_engine')}")
            print(f"Aluminum rims: {result.get('aluminum_rims')}")
            print(f"Catalytic converters: {result.get('catalytic_converters')}")
        
        print("✅ process_vehicle integration test completed!")
        return True
        
    except Exception as e:
        print(f"❌ process_vehicle integration test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_api_functions():
    """Test individual API functions with SingleCallVehicleResolver integration."""
    try:
        import vehicle_data
        
        print("Testing individual API functions...")
        
        # Test curb weight function
        print("Testing get_curb_weight_from_api...")
        weight = vehicle_data.get_curb_weight_from_api(2020, "Toyota", "Camry")
        print(f"Curb weight result: {weight}")
        
        # Test aluminum engine function
        print("Testing get_aluminum_engine_from_api...")
        engine = vehicle_data.get_aluminum_engine_from_api(2020, "Toyota", "Camry")
        print(f"Aluminum engine result: {engine}")
        
        # Test aluminum rims function
        print("Testing get_aluminum_rims_from_api...")
        rims = vehicle_data.get_aluminum_rims_from_api(2020, "Toyota", "Camry")
        print(f"Aluminum rims result: {rims}")
        
        # Test catalytic converter function
        print("Testing get_catalytic_converter_count_from_api...")
        cats = vehicle_data.get_catalytic_converter_count_from_api(2020, "Toyota", "Camry")
        print(f"Catalytic converters result: {cats}")
        
        print("✅ Individual API functions test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Individual API functions test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Running SingleCallVehicleResolver functionality tests...")
    print("=" * 60)
    
    # Check if API key is configured
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "YOUR_GEMINI_API_KEY":
        print("⚠️  Warning: GEMINI_API_KEY not configured - tests will use fallback methods")
    else:
        print("✅ GEMINI_API_KEY is configured")
    
    tests = [
        test_single_call_resolver_direct,
        test_process_vehicle_with_single_call,
        test_individual_api_functions
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
        print("🎉 All functionality tests completed!")
        sys.exit(0)
    else:
        print("❌ Some tests had issues!")
        sys.exit(1)