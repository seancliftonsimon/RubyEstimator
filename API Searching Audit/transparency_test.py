"""Transparency test script - shows exactly what prompts go to Google API and what comes back."""

import os
import sys

# Fix Windows console encoding - must be done before any imports that use logging
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    import io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import logging
import time
from typing import Any, Dict, Optional

from database_config import create_database_engine
from persistence import ensure_schema
from single_call_gemini_resolver import SingleCallGeminiResolver
from sqlalchemy import text

# Configure detailed logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,  # Set to INFO to reduce noise, but we'll print our own detailed output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    force=True
)
logger = logging.getLogger(__name__)


class TransparentResolver(SingleCallGeminiResolver):
    """Resolver that captures and displays all API interactions with full transparency."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.transparency_log = []
    
    def resolve_vehicle(self, year: int, make: str, model: str):
        """Resolve vehicle with full transparency."""
        vehicle_key = f"{year}_{make.lower().replace(' ', '_')}_{model.lower().replace(' ', '_')}"
        
        print("\n" + "="*80)
        print("🔍 TRANSPARENCY TEST - VEHICLE RESOLUTION")
        print("="*80)
        print(f"Vehicle: {year} {make} {model}")
        print(f"Vehicle Key: {vehicle_key}")
        print("="*80 + "\n")
        
        # Check database
        print("📋 STEP 1: Checking database...")
        exists = self._check_db(vehicle_key)
        if exists:
            print(f"⚠️  Vehicle EXISTS in database (will still make API call for transparency)")
        else:
            print(f"✓ Vehicle NOT in database - perfect for testing!")
        print()
        
        # Build and show prompt
        print("📝 STEP 2: Building prompt...")
        prompt = self._build_prompt(year, make, model)
        
        print("\n" + "-"*80)
        print("📤 PROMPT BEING SENT TO GOOGLE GEMINI API")
        print("-"*80)
        print(f"Prompt Length: {len(prompt)} characters")
        print(f"\n{'='*80}")
        print("FULL PROMPT CONTENT:")
        print("="*80)
        print(prompt)
        print("="*80)
        print()
        
        # Show API configuration
        print("-"*80)
        print("⚙️  API CONFIGURATION")
        print("-"*80)
        config = {
            "tools": [{"google_search": {}}],
            "temperature": 0,
        }
        print(f"Model: gemini-2.0-flash-exp")
        print(f"Config: {json.dumps(config, indent=2)}")
        print("-"*80)
        print()
        
        # Make API call with transparency
        print("🌐 STEP 3: Making API call to Google Gemini...")
        print("⏳ This may take 15-40 seconds (Google Search Grounding performs web search)...")
        print()
        
        api_start = time.time()
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt,
                config=config
            )
            api_time = (time.time() - api_start) * 1000
            
            # Show raw response
            raw_response = response.text
            print("\n" + "-"*80)
            print("📥 RAW RESPONSE FROM GOOGLE GEMINI API")
            print("-"*80)
            print(f"API Call Duration: {api_time:.2f}ms ({api_time/1000:.2f} seconds)")
            print(f"Response Length: {len(raw_response)} characters")
            print(f"\n{'='*80}")
            print("FULL RAW RESPONSE:")
            print("="*80)
            print(raw_response)
            print("="*80)
            print()
            
            # Parse response
            print("🔍 STEP 4: Parsing response...")
            response_text = raw_response.strip()
            
            # Check for markdown wrappers
            had_markdown = False
            if response_text.startswith("```json"):
                response_text = response_text[7:]
                had_markdown = True
                print("  → Detected ```json markdown wrapper, removing...")
            elif response_text.startswith("```"):
                response_text = response_text[3:]
                had_markdown = True
                print("  → Detected ``` markdown wrapper, removing...")
            if response_text.endswith("```"):
                response_text = response_text[:-3]
                had_markdown = True
                print("  → Removed closing ``` markdown wrapper")
            response_text = response_text.strip()
            
            if not had_markdown:
                print("  → No markdown wrappers detected")
            print()
            
            # Parse JSON
            print("-"*80)
            print("📦 PARSED JSON RESPONSE")
            print("-"*80)
            try:
                parsed_json = json.loads(response_text)
                print(json.dumps(parsed_json, indent=2))
                print("-"*80)
                print()
            except json.JSONDecodeError as e:
                print(f"❌ JSON Parse Error: {e}")
                print(f"   Line: {e.lineno}, Column: {e.colno}")
                print(f"   Problematic text: {response_text[max(0, e.pos-50):e.pos+50]}")
                raise
            
            # Validate and normalize
            print("✅ STEP 5: Validating and normalizing fields...")
            validated = self._validate_and_normalize(parsed_json)
            print()
            
            # Show final interpretation
            print("-"*80)
            print("🎯 FINAL INTERPRETED RESULTS")
            print("-"*80)
            for field_name, field_data in validated.items():
                print(f"\n{field_name.upper()}:")
                print(f"  Value: {field_data.get('value')}")
                print(f"  Status: {field_data.get('status')}")
                print(f"  Confidence: {field_data.get('confidence', 0.0):.2f}")
                if 'unit' in field_data:
                    print(f"  Unit: {field_data.get('unit')}")
                
                citations = field_data.get('citations', [])
                print(f"  Citations: {len(citations)}")
                for i, citation in enumerate(citations, 1):
                    print(f"    [{i}] {citation.get('source_type', 'unknown').upper()}")
                    url = citation.get('url', 'N/A')
                    print(f"        URL: {url}")
                    quote = citation.get('quote', 'N/A')
                    if len(quote) > 200:
                        quote = quote[:200] + "..."
                    print(f"        Quote: \"{quote}\"")
            
            print("\n" + "-"*80)
            print("✅ RESOLUTION COMPLETE")
            print("-"*80)
            print()
            
            # Create result object (simplified)
            from single_call_gemini_resolver import VehicleResolution
            import uuid
            return VehicleResolution(
                vehicle_key=vehicle_key,
                year=year,
                make=make,
                model=model,
                fields=validated,
                run_id=uuid.uuid4().hex,
                latency_ms=api_time,
                raw_response=parsed_json
            )
            
        except Exception as e:
            api_time = (time.time() - api_start) * 1000
            print(f"\n❌ API CALL FAILED after {api_time:.2f}ms")
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Message: {str(e)}")
            print()
            print("="*80)
            print("⚠️  NOTE: Even though the API call failed, you can see:")
            print("   1. The exact prompt that was sent (shown above)")
            print("   2. The API configuration used")
            print("   3. The error response from Google")
            print("="*80)
            print()
            raise
    
    def _check_db(self, vehicle_key: str) -> bool:
        """Check if vehicle exists in database."""
        try:
            ensure_schema()
            engine = create_database_engine()
            with engine.connect() as conn:
                row = conn.execute(
                    text("SELECT vehicle_key FROM vehicles WHERE vehicle_key = :key"),
                    {"key": vehicle_key}
                ).fetchone()
                return row is not None
        except Exception as e:
            logger.warning(f"Error checking database: {e}")
            return False


def run_test(year: int, make: str, model: str, api_key: Optional[str] = None):
    """Run a single transparency test."""
    resolver = TransparentResolver(api_key)
    return resolver.resolve_vehicle(year, make, model)


def main():
    """Run two transparency tests."""
    print("\n" + "="*80)
    print("🔬 TRANSPARENCY TESTING SCRIPT")
    print("="*80)
    print("This script shows EXACTLY what is sent to Google API and what comes back.")
    print("Running two examples with vehicles likely NOT in the database.")
    print("="*80)
    
    # Test vehicles - using vehicles from 1990-2010 that are likely not in database
    test_vehicles = [
        (1992, "Mazda", "Miata"),
        (1998, "BMW", "M3"),
        (2001, "Audi", "TT"),
        (2005, "Subaru", "WRX"),
        (2008, "Nissan", "GT-R")
    ]
    
    results = []
    
    for i, (year, make, model) in enumerate(test_vehicles, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i} of {len(test_vehicles)}: {year} {make} {model}")
        print(f"{'='*80}")
        
        try:
            result = run_test(year, make, model)
            results.append({
                'vehicle': f"{year} {make} {model}",
                'success': True,
                'latency_ms': result.latency_ms
            })
            print(f"✅ Test {i} completed successfully!")
        except Exception as e:
            results.append({
                'vehicle': f"{year} {make} {model}",
                'success': False,
                'error': str(e)
            })
            print(f"❌ Test {i} failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Wait between tests
        if i < len(test_vehicles):
            print(f"\n{'='*80}")
            print("Waiting 3 seconds before next test...")
            print("="*80)
            time.sleep(3)
    
    # Summary
    print("\n" + "="*80)
    print("📋 TEST SUMMARY")
    print("="*80)
    for i, result in enumerate(results, 1):
        status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
        print(f"\nTest {i}: {result['vehicle']} - {status}")
        if result['success']:
            print(f"   Latency: {result['latency_ms']:.2f}ms")
        else:
            print(f"   Error: {result['error']}")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
