"""Test script for single-call Gemini resolver with Search Grounding."""

from single_call_gemini_resolver import single_call_resolver


def test_resolve_vehicle():
    """Test resolving a common vehicle."""
    print("Testing single-call Gemini resolver with Search Grounding...")
    print("=" * 70)
    
    # Test with a well-known vehicle
    year = 2020
    make = "Toyota"
    model = "Camry"
    
    print(f"\n🔍 Resolving: {year} {make} {model}\n")
    
    try:
        result = single_call_resolver.resolve_vehicle(year, make, model)
        
        print(f"✅ Resolution successful!")
        print(f"   Vehicle Key: {result.vehicle_key}")
        print(f"   Run ID: {result.run_id}")
        print(f"   Latency: {result.latency_ms:.0f}ms")
        print(f"\n📊 Field Results:")
        print("=" * 70)
        
        for field_name, field_data in result.fields.items():
            value = field_data.get("value")
            status = field_data.get("status")
            confidence = field_data.get("confidence", 0.0)
            citations = field_data.get("citations", [])
            
            print(f"\n  {field_name}:")
            print(f"    Value: {value}")
            print(f"    Status: {status}")
            print(f"    Confidence: {confidence:.2f}")
            print(f"    Citations: {len(citations)} source(s)")
            
            for i, citation in enumerate(citations, 1):
                print(f"      [{i}] {citation.get('source_type', 'unknown').upper()}")
                print(f"          URL: {citation.get('url', 'N/A')[:80]}...")
                print(f"          Quote: \"{citation.get('quote', 'N/A')[:100]}...\"")
        
        print("\n" + "=" * 70)
        print("✅ Test completed successfully!")
        print(f"   Data persisted to database with run_id: {result.run_id}")
        
    except Exception as exc:
        print(f"❌ Test failed: {exc}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_resolve_vehicle()

