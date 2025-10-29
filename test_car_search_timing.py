"""Test script to measure search time for 4 different cars."""

import time
import logging
import sys
from single_call_gemini_resolver import SingleCallGeminiResolver

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)
logger = logging.getLogger(__name__)

def test_car_searches():
    """Test search times for 4 different vehicles."""
    
    # Test vehicles (mix of common and less common cars)
    test_vehicles = [
        {"year": 2015, "make": "Honda", "model": "Civic"},
        {"year": 2018, "make": "Toyota", "model": "Camry"},
        {"year": 2020, "make": "Ford", "model": "F-150"},
        {"year": 2017, "make": "Chevrolet", "model": "Silverado"},
    ]
    
    print("\n" + "="*80)
    print("🚗 VEHICLE SEARCH TIMING TEST")
    print("="*80)
    print(f"\nTesting {len(test_vehicles)} vehicles:")
    for i, vehicle in enumerate(test_vehicles, 1):
        print(f"  {i}. {vehicle['year']} {vehicle['make']} {vehicle['model']}")
    print("\n" + "="*80 + "\n")
    
    # Initialize resolver
    try:
        resolver = SingleCallGeminiResolver()
        logger.info("✓ Resolver initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize resolver: {e}")
        return
    
    # Test each vehicle
    results = []
    
    for i, vehicle in enumerate(test_vehicles, 1):
        year = vehicle["year"]
        make = vehicle["make"]
        model = vehicle["model"]
        
        print(f"\n{'='*80}")
        print(f"TEST {i}/{len(test_vehicles)}: {year} {make} {model}")
        print('='*80)
        
        start_time = time.time()
        
        try:
            resolution = resolver.resolve_vehicle(year, make, model)
            elapsed_time = time.time() - start_time
            
            results.append({
                "vehicle": f"{year} {make} {model}",
                "time_seconds": elapsed_time,
                "success": True,
                "cached": resolution.latency_ms < 100,  # Cached if < 100ms
            })
            
            print(f"\n✅ SUCCESS")
            print(f"   Time: {elapsed_time:.2f}s ({elapsed_time*1000:.0f}ms)")
            print(f"   Cached: {'Yes' if results[-1]['cached'] else 'No'}")
            print(f"   Curb Weight: {resolution.fields.get('curb_weight', {}).get('value')} lbs")
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"❌ Failed to resolve vehicle: {e}")
            results.append({
                "vehicle": f"{year} {make} {model}",
                "time_seconds": elapsed_time,
                "success": False,
                "cached": False,
                "error": str(e)
            })
            print(f"\n❌ FAILED")
            print(f"   Time: {elapsed_time:.2f}s")
            print(f"   Error: {e}")
    
    # Print summary
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    
    successful_results = [r for r in results if r["success"]]
    failed_results = [r for r in results if not r["success"]]
    
    print(f"\nTotal Tests: {len(results)}")
    print(f"Successful: {len(successful_results)}")
    print(f"Failed: {len(failed_results)}")
    
    if successful_results:
        print("\n" + "-"*80)
        print("INDIVIDUAL TIMES:")
        print("-"*80)
        for result in successful_results:
            cached_tag = " [CACHED]" if result["cached"] else ""
            print(f"  • {result['vehicle']:<30} {result['time_seconds']:>6.2f}s{cached_tag}")
        
        times = [r["time_seconds"] for r in successful_results]
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print("\n" + "-"*80)
        print("TIME STATISTICS:")
        print("-"*80)
        print(f"  Average Time:  {avg_time:.2f}s ({avg_time*1000:.0f}ms)")
        print(f"  Minimum Time:  {min_time:.2f}s ({min_time*1000:.0f}ms)")
        print(f"  Maximum Time:  {max_time:.2f}s ({max_time*1000:.0f}ms)")
    
    if failed_results:
        print("\n" + "-"*80)
        print("FAILED TESTS:")
        print("-"*80)
        for result in failed_results:
            print(f"  ❌ {result['vehicle']}")
            print(f"     Error: {result.get('error', 'Unknown error')}")
    
    print("\n" + "="*80)
    print("✅ TEST COMPLETE")
    print("="*80 + "\n")
    
    return results

if __name__ == "__main__":
    test_car_searches()

