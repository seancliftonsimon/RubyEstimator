"""
Test module for SingleCallVehicleResolver.

This module contains basic tests to verify the SingleCallVehicleResolver
class and VehicleSpecificationBundle dataclass work correctly.
"""

import json
from single_call_resolver import SingleCallVehicleResolver, VehicleSpecificationBundle


def test_vehicle_specification_bundle():
    """Test VehicleSpecificationBundle dataclass creation and basic functionality."""
    print("Testing VehicleSpecificationBundle...")
    
    # Test empty bundle
    bundle = VehicleSpecificationBundle()
    assert bundle.curb_weight_lbs is None
    assert bundle.aluminum_engine is None
    assert bundle.aluminum_rims is None
    assert bundle.catalytic_converters is None
    assert bundle.confidence_scores == {}
    assert bundle.source_citations == {}
    assert bundle.resolution_method == "single_call_resolution"
    assert bundle.warnings == []
    
    # Test bundle with data
    bundle = VehicleSpecificationBundle(
        curb_weight_lbs=3500.0,
        aluminum_engine=True,
        aluminum_rims=True,
        catalytic_converters=2,
        confidence_scores={"curb_weight": 0.9, "engine_material": 0.8},
        source_citations={"curb_weight": ["kbb.com", "edmunds.com"]},
        warnings=["Test warning"]
    )
    
    assert bundle.curb_weight_lbs == 3500.0
    assert bundle.aluminum_engine is True
    assert bundle.aluminum_rims is True
    assert bundle.catalytic_converters == 2
    assert bundle.confidence_scores["curb_weight"] == 0.9
    assert bundle.source_citations["curb_weight"] == ["kbb.com", "edmunds.com"]
    assert "Test warning" in bundle.warnings
    
    print("✅ VehicleSpecificationBundle tests passed")


def test_single_call_resolver_initialization():
    """Test SingleCallVehicleResolver initialization."""
    print("Testing SingleCallVehicleResolver initialization...")
    
    # Test with no API key (should handle gracefully)
    resolver = SingleCallVehicleResolver(api_key="")
    # Note: Client might still be created even with empty key, but should handle errors gracefully
    assert resolver.confidence_threshold == 0.7
    
    # Test with custom confidence threshold
    resolver = SingleCallVehicleResolver(api_key="", confidence_threshold=0.8)
    assert resolver.confidence_threshold == 0.8
    
    # Test with invalid API key placeholder
    resolver = SingleCallVehicleResolver(api_key="YOUR_GEMINI_API_KEY")
    assert resolver.client is None
    
    print("✅ SingleCallVehicleResolver initialization tests passed")


def test_prompt_generation():
    """Test comprehensive prompt generation."""
    print("Testing prompt generation...")
    
    resolver = SingleCallVehicleResolver(api_key="")
    prompt = resolver._create_comprehensive_prompt(2020, "Toyota", "Camry")
    
    # Check that prompt contains expected elements
    assert "2020 Toyota Camry" in prompt
    assert "curb_weight_lbs" in prompt
    assert "aluminum_engine" in prompt
    assert "aluminum_rims" in prompt
    assert "catalytic_converters" in prompt
    assert "confidence_scores" in prompt
    assert "sources" in prompt
    assert "JSON" in prompt
    
    # Check for enhanced prompt features
    assert "SOURCE PRIORITIZATION" in prompt
    assert "manufacturer websites" in prompt
    assert "KBB.com" in prompt
    assert "Edmunds.com" in prompt
    assert "FIELD-SPECIFIC SEARCH INSTRUCTIONS" in prompt
    assert "CURB WEIGHT" in prompt
    assert "ALUMINUM ENGINE BLOCK" in prompt
    assert "ALUMINUM RIMS/WHEELS" in prompt
    assert "CATALYTIC CONVERTERS" in prompt
    assert "VALIDATION REQUIREMENTS" in prompt
    assert "data_consistency_notes" in prompt
    
    print("✅ Prompt generation tests passed")


def test_json_parsing():
    """Test JSON response parsing."""
    print("Testing JSON response parsing...")
    
    resolver = SingleCallVehicleResolver(api_key="")
    
    # Test valid JSON response
    valid_response = '''
    Here is the information for the 2020 Toyota Camry:
    {
      "curb_weight_lbs": 3340,
      "aluminum_engine": true,
      "aluminum_rims": true,
      "catalytic_converters": 2,
      "confidence_scores": {
        "curb_weight": 0.9,
        "engine_material": 0.8,
        "rim_material": 0.7,
        "catalytic_converters": 0.6
      },
      "sources": {
        "curb_weight": ["toyota.com", "kbb.com"],
        "engine_material": ["edmunds.com"],
        "rim_material": ["autotrader.com"],
        "catalytic_converters": ["parts catalog"]
      }
    }
    Additional text after JSON.
    '''
    
    bundle = resolver._parse_structured_response(valid_response, 2020, "Toyota", "Camry")
    
    assert bundle.curb_weight_lbs == 3340
    assert bundle.aluminum_engine is True
    assert bundle.aluminum_rims is True
    assert bundle.catalytic_converters == 2
    assert bundle.confidence_scores["curb_weight"] == 0.9
    assert bundle.confidence_scores["engine_material"] == 0.8
    assert "toyota.com" in bundle.source_citations["curb_weight"]
    assert "kbb.com" in bundle.source_citations["curb_weight"]
    
    # Test invalid JSON response
    invalid_response = "This is not a JSON response at all."
    bundle = resolver._parse_structured_response(invalid_response, 2020, "Toyota", "Camry")
    
    assert bundle.curb_weight_lbs is None
    assert len(bundle.warnings) > 0
    assert "No JSON structure found" in bundle.warnings[0]
    
    # Test malformed JSON
    malformed_response = '{"curb_weight_lbs": 3340, "aluminum_engine": true'  # Missing closing brace
    bundle = resolver._parse_structured_response(malformed_response, 2020, "Toyota", "Camry")
    
    assert bundle.curb_weight_lbs is None
    assert len(bundle.warnings) > 0
    # The regex won't match incomplete JSON, so it will report "No JSON structure found"
    assert "No JSON structure found" in bundle.warnings[0] or "Failed to parse JSON" in bundle.warnings[0]
    
    print("✅ JSON parsing tests passed")


def test_data_validation():
    """Test data validation and range checking."""
    print("Testing data validation...")
    
    resolver = SingleCallVehicleResolver(api_key="")
    
    # Test out-of-range values
    invalid_response = '''
    {
      "curb_weight_lbs": 50000,
      "aluminum_engine": true,
      "aluminum_rims": false,
      "catalytic_converters": 20,
      "confidence_scores": {
        "curb_weight": 0.9,
        "engine_material": 0.8
      }
    }
    '''
    
    bundle = resolver._parse_structured_response(invalid_response, 2020, "Toyota", "Camry")
    
    # Should reject out-of-range values
    assert bundle.curb_weight_lbs is None  # 50000 is too high
    assert bundle.catalytic_converters is None  # 20 is too high
    assert bundle.aluminum_engine is True  # Valid boolean should be kept
    assert bundle.aluminum_rims is False  # Valid boolean should be kept
    assert len(bundle.warnings) >= 2  # Should have warnings for out-of-range values
    
    print("✅ Data validation tests passed")


def test_confidence_checking():
    """Test confidence threshold checking."""
    print("Testing confidence checking...")
    
    # Test with high confidence
    resolver = SingleCallVehicleResolver(api_key="", confidence_threshold=0.7)
    bundle = VehicleSpecificationBundle(
        curb_weight_lbs=3500.0,
        confidence_scores={"curb_weight": 0.9}
    )
    
    assert resolver.has_sufficient_confidence(bundle) is True
    
    # Test with low confidence
    bundle = VehicleSpecificationBundle(
        curb_weight_lbs=3500.0,
        confidence_scores={"curb_weight": 0.5}
    )
    
    assert resolver.has_sufficient_confidence(bundle) is False
    
    # Test with no curb weight
    bundle = VehicleSpecificationBundle(
        aluminum_engine=True,
        confidence_scores={"engine_material": 0.9}
    )
    
    assert resolver.has_sufficient_confidence(bundle) is False
    
    print("✅ Confidence checking tests passed")


def test_enhanced_validation():
    """Test enhanced validation and consistency checking."""
    print("Testing enhanced validation...")
    
    resolver = SingleCallVehicleResolver(api_key="")
    
    # Test response with data consistency notes
    response_with_notes = '''
    {
      "curb_weight_lbs": 3340,
      "aluminum_engine": true,
      "aluminum_rims": true,
      "catalytic_converters": 2,
      "confidence_scores": {
        "curb_weight": 0.9,
        "engine_material": 0.8,
        "rim_material": 0.7,
        "catalytic_converters": 0.6
      },
      "sources": {
        "curb_weight": ["toyota.com", "kbb.com"],
        "engine_material": ["edmunds.com"],
        "rim_material": ["autotrader.com"],
        "catalytic_converters": ["parts catalog"]
      },
      "data_consistency_notes": "All specifications align with typical mid-size sedan configuration"
    }
    '''
    
    bundle = resolver._parse_structured_response(response_with_notes, 2020, "Toyota", "Camry")
    
    # Should include the consistency note as a warning
    consistency_warnings = [w for w in bundle.warnings if "AI consistency note" in w]
    assert len(consistency_warnings) > 0
    assert "All specifications align" in consistency_warnings[0]
    
    # Test enhanced weight range validation
    extreme_weight_response = '''
    {
      "curb_weight_lbs": 1200,
      "aluminum_engine": false,
      "confidence_scores": {"curb_weight": 0.9, "engine_material": 0.8}
    }
    '''
    
    bundle = resolver._parse_structured_response(extreme_weight_response, 2020, "Toyota", "Camry")
    assert bundle.curb_weight_lbs is None  # Should reject weight below 1500
    weight_warnings = [w for w in bundle.warnings if "outside reasonable range" in w]
    assert len(weight_warnings) > 0
    
    # Test confidence score validation
    missing_confidence_response = '''
    {
      "curb_weight_lbs": 3340,
      "aluminum_engine": true,
      "confidence_scores": {
        "curb_weight": 0.9
      }
    }
    '''
    
    bundle = resolver._parse_structured_response(missing_confidence_response, 2020, "Toyota", "Camry")
    confidence_warnings = [w for w in bundle.warnings if "Missing confidence score" in w]
    assert len(confidence_warnings) > 0
    
    print("✅ Enhanced validation tests passed")


def run_all_tests():
    """Run all tests."""
    print("Running SingleCallVehicleResolver tests...\n")
    
    try:
        test_vehicle_specification_bundle()
        test_single_call_resolver_initialization()
        test_prompt_generation()
        test_json_parsing()
        test_data_validation()
        test_confidence_checking()
        test_enhanced_validation()
        
        print("\n🎉 All tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    run_all_tests()