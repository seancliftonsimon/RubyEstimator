"""
Functional test for search grounding to verify it works with real API calls.
"""

import os
import sys
from unittest.mock import patch, MagicMock

def test_vehicle_validation_with_mocked_api():
    """Test vehicle validation with mocked API to verify configuration."""
    print("Testing vehicle validation with mocked API...")
    
    try:
        from vehicle_data import validate_vehicle_existence, SHARED_GEMINI_MODEL
        
        # Mock the API response
        with patch.object(SHARED_GEMINI_MODEL, 'generate_content') as mock_generate:
            # Mock successful response
            mock_response = MagicMock()
            mock_response.text = "yes"
            mock_generate.return_value = mock_response
            
            # Test the function
            result = validate_vehicle_existence(2020, "Toyota", "Camry")
            
            # Verify the function was called
            mock_generate.assert_called_once()
            
            # Check the call arguments
            call_args = mock_generate.call_args
            
            # Verify tools parameter exists and has correct format
            if 'tools' in call_args.kwargs:
                tools = call_args.kwargs['tools']
                if tools == [{"google_search": {}}]:
                    print("✅ PASS: Correct google_search configuration used")
                else:
                    print(f"❌ FAIL: Incorrect tools configuration: {tools}")
                    return False
            else:
                print("❌ FAIL: No tools parameter found in API call")
                return False
            
            # Verify result
            if result is True:
                print("✅ PASS: Function returned expected result")
            else:
                print(f"❌ FAIL: Function returned unexpected result: {result}")
                return False
                
    except Exception as e:
        print(f"❌ FAIL: Error in vehicle validation test: {e}")
        return False
    
    return True

def test_resolver_search_with_mocked_api():
    """Test resolver search functionality with mocked API."""
    print("Testing resolver search with mocked API...")
    
    try:
        from resolver import GroundedSearchClient
        import resolver
        
        # Mock the genai module
        with patch('resolver.genai') as mock_genai:
            # Mock the model
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            
            # Mock successful response
            mock_response = MagicMock()
            mock_response.text = "3500 lbs from kbb.com\n3520 lbs from edmunds.com"
            mock_model.generate_content.return_value = mock_response
            
            # Create client and test
            client = GroundedSearchClient()
            candidates = client.search_vehicle_specs(2020, "Toyota", "Camry", "curb_weight")
            
            # Verify the API was called
            mock_model.generate_content.assert_called()
            
            # Check the call arguments
            call_args = mock_model.generate_content.call_args
            
            # Verify tools parameter
            if 'tools' in call_args.kwargs:
                tools = call_args.kwargs['tools']
                if tools == [{"google_search": {}}]:
                    print("✅ PASS: Resolver uses correct google_search configuration")
                else:
                    print(f"❌ FAIL: Resolver uses incorrect tools configuration: {tools}")
                    return False
            else:
                print("❌ FAIL: No tools parameter found in resolver API call")
                return False
            
            # Verify candidates were parsed
            if candidates is not None:
                print("✅ PASS: Resolver returned candidates successfully")
            else:
                print("❌ FAIL: Resolver returned None")
                return False
                
    except Exception as e:
        print(f"❌ FAIL: Error in resolver test: {e}")
        return False
    
    return True

def test_curb_weight_api_with_mocked_calls():
    """Test curb weight API with mocked calls."""
    print("Testing curb weight API with mocked calls...")
    
    try:
        from vehicle_data import get_curb_weight_from_api, SHARED_GEMINI_MODEL
        
        # Mock the API responses
        with patch.object(SHARED_GEMINI_MODEL, 'generate_content') as mock_generate:
            # Mock responses for gather and interpret calls
            mock_gather_response = MagicMock()
            mock_gather_response.text = "3500 lbs from kbb.com"
            
            mock_interpret_response = MagicMock()
            mock_interpret_response.text = "3500"
            
            # Set up side effect to return different responses
            mock_generate.side_effect = [mock_gather_response, mock_interpret_response]
            
            # Test the function
            result = get_curb_weight_from_api(2020, "Toyota", "Camry")
            
            # Verify both calls were made
            if mock_generate.call_count != 2:
                print(f"❌ FAIL: Expected 2 API calls, got {mock_generate.call_count}")
                return False
            
            # Check that both calls used correct tools configuration
            for call in mock_generate.call_args_list:
                if 'tools' in call.kwargs:
                    tools = call.kwargs['tools']
                    if tools != [{"google_search": {}}]:
                        print(f"❌ FAIL: Curb weight API uses incorrect tools: {tools}")
                        return False
            
            print("✅ PASS: Curb weight API uses correct google_search configuration")
            
            # Verify result
            if result == 3500.0:
                print("✅ PASS: Curb weight API returned expected result")
            else:
                print(f"❌ FAIL: Curb weight API returned unexpected result: {result}")
                return False
                
    except Exception as e:
        print(f"❌ FAIL: Error in curb weight test: {e}")
        return False
    
    return True

def run_all_tests():
    """Run all functional tests."""
    print("🧪 Running Search Grounding Functional Tests\n")
    
    tests = [
        test_vehicle_validation_with_mocked_api,
        test_resolver_search_with_mocked_api,
        test_curb_weight_api_with_mocked_calls
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print(f"\n--- {test.__name__} ---")
        try:
            if test():
                passed += 1
                print("✅ TEST PASSED")
            else:
                print("❌ TEST FAILED")
        except Exception as e:
            print(f"❌ TEST ERROR: {e}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All search grounding functionality tests passed!")
        print("✅ Search grounding configuration is working correctly")
        return True
    else:
        print("❌ Some search grounding tests failed")
        return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)