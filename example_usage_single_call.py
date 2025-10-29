"""Example usage of single-call Gemini resolver."""

import os
from single_call_gemini_resolver import single_call_resolver


def example_basic_usage():
    """Basic example: resolve a single vehicle."""
    print("=" * 70)
    print("EXAMPLE 1: Basic Vehicle Resolution")
    print("=" * 70)
    
    # Resolve vehicle
    result = single_call_resolver.resolve_vehicle(
        year=2020,
        make="Toyota",
        model="Camry"
    )
    
    # Access basic info
    print(f"\n✅ Resolved: {result.year} {result.make} {result.model}")
    print(f"   Vehicle Key: {result.vehicle_key}")
    print(f"   Run ID: {result.run_id}")
    print(f"   Latency: {result.latency_ms:.0f}ms")
    
    # Access field values
    print(f"\n📊 Field Values:")
    print(f"   Curb Weight: {result.fields['curb_weight']['value']} lbs")
    print(f"   Aluminum Engine: {result.fields['aluminum_engine']['value']}")
    print(f"   Aluminum Rims: {result.fields['aluminum_rims']['value']}")
    print(f"   Catalytic Converters: {result.fields['catalytic_converters']['value']}")


def example_confidence_and_citations():
    """Example: access confidence scores and citations."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Confidence & Citations")
    print("=" * 70)
    
    result = single_call_resolver.resolve_vehicle(2020, "Honda", "Civic")
    
    for field_name, field_data in result.fields.items():
        confidence = field_data['confidence']
        status = field_data['status']
        citations = field_data['citations']
        
        print(f"\n  {field_name}:")
        print(f"    Status: {status}")
        print(f"    Confidence: {confidence:.2f}")
        print(f"    Citations: {len(citations)}")
        
        for i, citation in enumerate(citations, 1):
            source_type = citation['source_type'].upper()
            url = citation['url'][:60] + "..." if len(citation['url']) > 60 else citation['url']
            quote = citation['quote'][:80] + "..." if len(citation['quote']) > 80 else citation['quote']
            
            print(f"      [{i}] {source_type}")
            print(f"          URL: {url}")
            print(f"          Quote: \"{quote}\"")


def example_error_handling():
    """Example: handle errors gracefully."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Error Handling")
    print("=" * 70)
    
    try:
        # This should work
        result = single_call_resolver.resolve_vehicle(2020, "Ford", "F-150")
        print(f"✅ Successfully resolved {result.vehicle_key}")
        
        # Check for fields that weren't found
        not_found = [
            field for field, data in result.fields.items()
            if data['status'] == 'not_found'
        ]
        if not_found:
            print(f"⚠️  Some fields not found: {', '.join(not_found)}")
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
    except RuntimeError as e:
        print(f"❌ API or parsing error: {e}")


def example_high_confidence_fields():
    """Example: filter fields by confidence threshold."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: High-Confidence Fields")
    print("=" * 70)
    
    result = single_call_resolver.resolve_vehicle(2019, "Tesla", "Model 3")
    
    threshold = 0.80
    high_confidence = {
        field: data
        for field, data in result.fields.items()
        if data['confidence'] >= threshold
    }
    
    print(f"\n   Fields with confidence >= {threshold}:")
    for field, data in high_confidence.items():
        print(f"     • {field}: {data['value']} (confidence: {data['confidence']:.2f})")


def example_streamlit_integration():
    """Example: use via Streamlit integration layer."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Streamlit Integration")
    print("=" * 70)
    
    from vehicle_data import process_vehicle
    
    result = process_vehicle(2020, "Toyota", "Camry")
    
    print(f"\n   Curb Weight: {result['curb_weight_lbs']} lbs")
    print(f"   Aluminum Engine: {result['aluminum_engine']}")
    print(f"   Confidence Scores:")
    for field, score in result['confidence_scores'].items():
        print(f"     • {field}: {score:.2f}")


def example_database_query():
    """Example: query persisted data from database."""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Database Queries")
    print("=" * 70)
    
    from database_config import create_database_engine
    from sqlalchemy import text
    
    # First, resolve a vehicle to ensure data exists
    result = single_call_resolver.resolve_vehicle(2020, "Toyota", "Camry")
    vehicle_key = result.vehicle_key
    
    # Query field values
    engine = create_database_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT field, value_json FROM field_values WHERE vehicle_key = :key"),
            {"key": vehicle_key}
        ).fetchall()
        
        print(f"\n   Fields stored for {vehicle_key}:")
        for field, value_json in rows:
            print(f"     • {field}: {value_json}")
        
        # Query evidence/citations
        evidence_rows = conn.execute(
            text(
                "SELECT field, quote, source_url FROM evidence "
                "WHERE vehicle_key = :key AND run_id = :run_id"
            ),
            {"key": vehicle_key, "run_id": result.run_id}
        ).fetchall()
        
        print(f"\n   Evidence stored for {vehicle_key}:")
        for field, quote, url in evidence_rows[:3]:  # Show first 3 only
            print(f"     • {field}")
            print(f"       Quote: \"{quote[:60]}...\"")
            print(f"       URL: {url[:60]}...")


if __name__ == "__main__":
    # Check API key is set
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "YOUR_GEMINI_API_KEY":
        print("❌ GEMINI_API_KEY not set. Please set it in your environment:")
        print("   export GEMINI_API_KEY='your-key-here'")
        exit(1)
    
    print("\n🚀 Single-Call Gemini Resolver - Example Usage\n")
    
    # Run examples
    example_basic_usage()
    example_confidence_and_citations()
    example_error_handling()
    example_high_confidence_fields()
    example_streamlit_integration()
    example_database_query()
    
    print("\n" + "=" * 70)
    print("✅ All examples completed successfully!")
    print("=" * 70)

