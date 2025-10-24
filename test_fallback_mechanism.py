#!/usr/bin/env python3
"""
Test script to verify the fallback mechanism from SingleCallVehicleResolver to multi-call system
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_fallback_when_single_call_fails():
    """Test that the system falls back to multi-call when single-call fails."""
    try:
        import vehicle_data
        from single_call_resolver import SingleCallVehicleResolver, VehicleSpecificationBundle
        
        # Create a mock resolver that always fails
        class FailingSingleCallResolver(SingleCallVehicleResolver):
            def resolve_all_specifications(self, year, make, model):
                # Return a bundle with no data and low confidence
                return VehicleSpecificationBundle(
                    warnings=["Mock failure for testing"]
                )
        
        # Replace the resolver temporarily
        original_resolver = vehicle_data.single_call_resolver
        vehicle_data.single_call_resolver = FailingSingleCallResolver()
        
        print("Testing fallback mechanism with failing single-call resolver...")
        
        # This should fall back to the multi-call system
        result = vehicle_data.process_vehicle(2020, "Toyota", "Camry")
        
        print(f"Fallback result: {result}")
        
        # Restore original resolver
        vehicle_data.single_call_resolver = original_resolver
        
        print("✅ Fallback mechanism test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Fallback mechanism test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_function_fallback():
    """Test that individual API functions fall back correctly."""
    try:
        import vehicle_data
        from single_call_resolver import SingleCallVehicleResolver, VehicleSpecificationBundle
        
        # Create a mock resolver that always fails
        class FailingSingleCallResolver(SingleCallVehicleResolver):
            def resolve_all_specifications(self, year, make, model):
                return VehicleSpecificationBundle(
                    warnings=["Mock failure for testing"]
                )
        
        # Replace the resolver temporarily
        original_resolver = vehicle_data.single_call_resolver
        vehicle_data.single_call_resolver = FailingSingleCallResolver()
        
        print("Testing individual function fallback...")
        
        # Test each function - they should fall back to multi-call resolvers
        weight = vehicle_data.get_curb_weight_from_api(2020, "Toyota", "Camry")
        print(f"Weight fallback result: {weight}")
        
        engine = vehicle_data.get_aluminum_engine_from_api(2020, "Toyota", "Camry")
        print(f"Engine fallback result: {engine}")
        
        rims = vehicle_data.get_aluminum_rims_from_api(2020, "Toyota", "Camry")
        print(f"Rims fallback result: {rims}")
        
        cats = vehicle_data.get_catalytic_converter_count_from_api(2020, "Toyota", "Camry")
        print(f"Cats fallback result: {cats}")
        
        # Restore original resolver
        vehicle_data.single_call_resolver = original_resolver
        
        print("✅ Individual function fallback test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Individual function fallback test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_confidence_threshold_fallback():
    """Test that low confidence results trigger fallback."""
    try:
        import vehicle_data
        from single_call_resolver import SingleCallVehicleResolver, VehicleSpecificationBundle
        
        # Create a mock resolver that returns low confidence results
        class LowConfidenceResolver(SingleCallVehicleResolver):
            def resolve_all_specifications(self, year, make, model):
                return VehicleSpecificationBundle(
                    curb_weight_lbs=3000.0,
                    aluminum_engine=True,
                    aluminum_rims=True,
                    catalytic_converters=2,
                    confidence_scores={
                        'curb_weight': 0.3,  # Below threshold
                        'engine_material': 0.3,
                        'rim_material': 0.3,
                        'catalytic_converters': 0.3
                    }
                )
            
            def has_sufficient_confidence(self, bundle):
                return False  # Always return False to trigger fallback
        
        # Replace the resolver temporarily
        original_resolver = vehicle_data.single_call_resolver
        vehicle_data.single_call_resolver = LowConfidenceResolver()
        
        print("Testing confidence threshold fallback...")
        
        # This should fall back due to low confidence
        result = vehicle_data.process_vehicle(2020, "Toyota", "Camry")
        
        print(f"Low confidence fallback result: {result}")
        
        # Restore original resolver
        vehicle_data.single_call_resolver = original_resolver
        
        print("✅ Confidence threshold fallback test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Confidence threshold fallback test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Running fallback mechanism tests...")
    print("=" * 60)
    
    tests = [
        test_fallback_when_single_call_fails,
        test_individual_function_fallback,
        test_confidence_threshold_fallback
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
        print("🎉 All fallback tests completed!")
        sys.exit(0)
    else:
        print("❌ Some fallback tests had issues!")
        sys.exit(1)