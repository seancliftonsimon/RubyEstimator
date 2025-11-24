
import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.getcwd())

from single_call_gemini_resolver import SingleCallGeminiResolver

# Configure logging - force utf-8 or simple formatting
logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Safe print function
def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', 'replace').decode('ascii'))

def test_resolver():
    resolver = SingleCallGeminiResolver()
    
    safe_print("\n--- TESTING REAL VEHICLE (2015 Honda Civic) ---")
    try:
        result = resolver.resolve_vehicle(2015, "Honda", "Civic")
        safe_print(f"Result: {result.fields}")
        
        # Check if we got sensible values
        curb_weight = result.fields.get("curb_weight", {}).get("value")
        cats = result.fields.get("catalytic_converters", {}).get("value")
        
        if curb_weight and 2000 < curb_weight < 4000:
            safe_print(f"✅ Curb weight {curb_weight} seems sensible")
        else:
            safe_print(f"⚠️ Curb weight {curb_weight} might be off")
            
        if cats is not None:
            safe_print(f"✅ Catalytic converters: {cats}")
        else:
            safe_print("⚠️ Catalytic converters not found")
            
    except Exception as e:
        safe_print(f"❌ Error resolving real vehicle: {e}")

    safe_print("\n--- TESTING FAKE VEHICLE (2025 Foobar Bazmobile) ---")
    try:
        result = resolver.resolve_vehicle(2025, "Foobar", "Bazmobile")
        safe_print(f"Result: {result.fields}")
        
        # Check if it was flagged as not found
        all_not_found = all(
            f.get("status") == "not_found" 
            for f in result.fields.values()
        )
        
        if all_not_found:
            safe_print("✅ Correctly identified as non-existent (all fields not_found)")
        else:
            safe_print("❌ Failed to identify as non-existent")
            
    except Exception as e:
        safe_print(f"❌ Error resolving fake vehicle: {e}")

if __name__ == "__main__":
    test_resolver()
