"""Test error handling for curb weight resolution."""

import json
from unittest.mock import Mock, patch
from single_call_gemini_resolver import SingleCallGeminiResolver
from vehicle_data import process_vehicle


def test_api_failure_returns_error_dict():
    """Test that API failures return a dict with 'error' key."""
    with patch('single_call_gemini_resolver.single_call_resolver.resolve_vehicle') as mock_resolve:
        # Simulate API failure
        mock_resolve.side_effect = RuntimeError("503 UNAVAILABLE. The model is overloaded.")
        
        result = process_vehicle(2016, "Toyota", "Camry")
        
        # Should return dict with error key
        assert result is not None
        assert 'error' in result
        assert 'curb_weight_lbs' in result
        assert result['curb_weight_lbs'] is None
        assert '503' in result['error'] or 'overloaded' in result['error'].lower()
        print("[OK] API failure test passed")


def test_data_not_found_returns_none_values():
    """Test that when data isn't found, value is None but no error key."""
    mock_resolution = Mock()
    mock_resolution.fields = {
        'curb_weight': {
            'value': None,
            'status': 'not_found',
            'citations': [],
            'confidence': 0.0
        },
        'aluminum_engine': {
            'value': True,
            'status': 'found',
            'citations': [{'url': 'test.com', 'quote': 'aluminum', 'source_type': 'oem'}],
            'confidence': 0.95
        },
        'aluminum_rims': {
            'value': True,
            'status': 'found',
            'citations': [{'url': 'test.com', 'quote': 'alloy', 'source_type': 'oem'}],
            'confidence': 0.95
        },
        'catalytic_converters': {
            'value': 2,
            'status': 'found',
            'citations': [{'url': 'test.com', 'quote': 'dual cats', 'source_type': 'secondary'}],
            'confidence': 0.85
        }
    }
    mock_resolution.vehicle_key = "2016_toyota_camry"
    mock_resolution.latency_ms = 1500.0
    mock_resolution.run_id = "test123"
    
    with patch('single_call_gemini_resolver.single_call_resolver.resolve_vehicle') as mock_resolve:
        mock_resolve.return_value = mock_resolution
        
        result = process_vehicle(2016, "Toyota", "Camry")
        
        # Should return dict WITHOUT error key (API succeeded)
        assert result is not None
        assert 'error' not in result or not result.get('error')
        assert result['curb_weight_lbs'] is None  # Not found
        assert result['aluminum_engine'] is True  # Found
        assert result['aluminum_rims'] is True  # Found
        assert result['catalytic_converters'] == 2  # Found
        print("[OK] Data not found test passed (with partial data)")


def test_success_case():
    """Test that successful resolution returns all data."""
    mock_resolution = Mock()
    mock_resolution.fields = {
        'curb_weight': {
            'value': 3310.0,
            'unit': 'lbs',
            'status': 'found',
            'citations': [{'url': 'toyota.com', 'quote': 'Curb Weight: 3,310 lbs', 'source_type': 'oem'}],
            'confidence': 0.95
        },
        'aluminum_engine': {
            'value': True,
            'status': 'found',
            'citations': [{'url': 'toyota.com', 'quote': 'aluminum engine block', 'source_type': 'oem'}],
            'confidence': 0.95
        },
        'aluminum_rims': {
            'value': True,
            'status': 'found',
            'citations': [{'url': 'toyota.com', 'quote': '17-inch alloy wheels', 'source_type': 'oem'}],
            'confidence': 0.95
        },
        'catalytic_converters': {
            'value': 2,
            'status': 'found',
            'citations': [{'url': 'test.com', 'quote': 'dual catalytic converters', 'source_type': 'secondary'}],
            'confidence': 0.85
        }
    }
    mock_resolution.vehicle_key = "2016_toyota_camry"
    mock_resolution.latency_ms = 1500.0
    mock_resolution.run_id = "test123"
    
    with patch('single_call_gemini_resolver.single_call_resolver.resolve_vehicle') as mock_resolve:
        mock_resolve.return_value = mock_resolution
        
        result = process_vehicle(2016, "Toyota", "Camry")
        
        # Should return complete dict
        assert result is not None
        assert 'error' not in result or not result.get('error')
        assert result['curb_weight_lbs'] == 3310.0
        assert result['aluminum_engine'] is True
        assert result['aluminum_rims'] is True
        assert result['catalytic_converters'] == 2
        assert 'confidence_scores' in result
        assert 'citations' in result
        print("[OK] Success case test passed")


def test_retry_logic_with_503():
    """Test that 503 errors trigger retry logic."""
    with patch('single_call_gemini_resolver.SingleCallGeminiResolver._initialize_client') as mock_init:
        mock_client = Mock()
        mock_init.return_value = mock_client
        
        # First two attempts fail with 503, third succeeds
        mock_response = Mock()
        mock_response.text = json.dumps({
            "curb_weight": {"value": 3310, "unit": "lbs", "status": "found", "citations": []},
            "aluminum_engine": {"value": True, "status": "found", "citations": []},
            "aluminum_rims": {"value": True, "status": "found", "citations": []},
            "catalytic_converters": {"value": 2, "status": "found", "citations": []}
        })
        
        mock_client.models.generate_content.side_effect = [
            Exception("503 UNAVAILABLE. The model is overloaded."),
            Exception("503 UNAVAILABLE. The model is overloaded."),
            mock_response  # Third attempt succeeds
        ]
        
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            resolver = SingleCallGeminiResolver(api_key='test_key')
            
            # Should succeed after retries (won't raise exception)
            result = resolver.resolve_vehicle(2016, "Toyota", "Camry")
            
            assert result is not None
            assert result.fields['curb_weight']['value'] == 3310
            # Verify it tried 3 times
            assert mock_client.models.generate_content.call_count == 3
            print("[OK] Retry logic test passed (succeeded on 3rd attempt)")


def test_status_value_consistency_fix():
    """Test that inconsistent status/value combinations are fixed during validation."""
    from single_call_gemini_resolver import SingleCallGeminiResolver

    resolver = SingleCallGeminiResolver(api_key='test')

    # Test data with inconsistent status/value combinations (like the bug we fixed)
    inconsistent_result = {
        "curb_weight": {"value": 3230.0, "status": "not_found", "citations": [], "confidence": 0.7},  # Should be None
        "aluminum_engine": {"value": False, "status": "not_found", "citations": [], "confidence": 0.0},  # Should be None
        "aluminum_rims": {"value": True, "status": "found", "citations": [{"url": "test.com"}], "confidence": 0.7},  # Should stay True
        "catalytic_converters": {"value": 2, "status": "conflicting", "citations": [{"url": "test1.com"}, {"url": "test2.com"}], "confidence": 0.4}  # Should be None
    }

    validated = resolver._validate_and_normalize(inconsistent_result)

    # Check that not_found/conflicting statuses result in None values
    assert validated["curb_weight"]["value"] is None, f"curb_weight should be None for status='not_found', got {validated['curb_weight']['value']}"
    assert validated["curb_weight"]["status"] == "not_found"

    assert validated["aluminum_engine"]["value"] is None, f"aluminum_engine should be None for status='not_found', got {validated['aluminum_engine']['value']}"
    assert validated["aluminum_engine"]["status"] == "not_found"

    assert validated["aluminum_rims"]["value"] is True, f"aluminum_rims should stay True for status='found', got {validated['aluminum_rims']['value']}"
    assert validated["aluminum_rims"]["status"] == "found"

    assert validated["catalytic_converters"]["value"] is None, f"catalytic_converters should be None for status='conflicting', got {validated['catalytic_converters']['value']}"
    assert validated["catalytic_converters"]["status"] == "conflicting"

    print("[OK] Status/value consistency fix test passed")


if __name__ == "__main__":
    print("Running error handling tests...\n")
    
    try:
        test_api_failure_returns_error_dict()
        test_data_not_found_returns_none_values()
        test_success_case()
        test_retry_logic_with_503()
        test_status_value_consistency_fix()
        
        print("\n[SUCCESS] All tests passed!")
    except AssertionError as e:
        print(f"\n[FAILED] Test failed: {e}")
    except Exception as e:
        print(f"\n[ERROR] Error running tests: {e}")

