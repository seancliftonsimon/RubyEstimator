"""Capture 5 examples with full input/output for documentation."""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List

# Fix Windows console encoding
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    import io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from single_call_gemini_resolver import SingleCallGeminiResolver
from database_config import create_database_engine
from persistence import ensure_schema
from sqlalchemy import text


class ExampleCapture:
    """Capture complete examples with input and output."""
    
    def __init__(self):
        self.resolver = SingleCallGeminiResolver()
        self.examples = []
    
    def capture_example(self, year: int, make: str, model: str) -> Dict[str, Any]:
        """Capture a complete example with all details."""
        vehicle_key = f"{year}_{make.lower().replace(' ', '_')}_{model.lower().replace(' ', '_')}"
        
        example = {
            'input': {
                'year': year,
                'make': make,
                'model': model,
                'vehicle_key': vehicle_key
            },
            'timestamp': datetime.now().isoformat(),
            'database_check': None,
            'prompt': None,
            'api_config': None,
            'raw_response': None,
            'parsed_response': None,
            'validated_response': None,
            'error': None,
            'latency_ms': None
        }
        
        print(f"\n{'='*80}")
        print(f"CAPTURING EXAMPLE: {year} {make} {model}")
        print(f"{'='*80}\n")
        
        # Check database
        try:
            ensure_schema()
            engine = create_database_engine()
            with engine.connect() as conn:
                row = conn.execute(
                    text("SELECT vehicle_key FROM vehicles WHERE vehicle_key = :key"),
                    {"key": vehicle_key}
                ).fetchone()
                example['database_check'] = {
                    'exists': row is not None,
                    'message': 'Vehicle exists in database' if row else 'Vehicle NOT in database'
                }
        except Exception as e:
            example['database_check'] = {
                'exists': False,
                'message': f'Database check failed: {str(e)}'
            }
        
        # Build prompt
        prompt = self.resolver._build_prompt(year, make, model)
        example['prompt'] = {
            'content': prompt,
            'length': len(prompt)
        }
        
        # API config
        example['api_config'] = {
            'model': 'gemini-2.0-flash-exp',
            'tools': [{'google_search': {}}],
            'temperature': 0
        }
        
        # Make API call
        print(f"Making API call for {year} {make} {model}...")
        api_start = time.time()
        
        try:
            response = self.resolver.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt,
                config={
                    "tools": [{"google_search": {}}],
                    "temperature": 0,
                }
            )
            api_time = (time.time() - api_start) * 1000
            example['latency_ms'] = api_time
            
            # Capture raw response
            raw_response = response.text
            example['raw_response'] = {
                'content': raw_response,
                'length': len(raw_response),
                'duration_ms': api_time
            }
            
            # Parse response
            response_text = raw_response.strip()
            had_markdown = False
            
            if response_text.startswith("```json"):
                response_text = response_text[7:]
                had_markdown = True
            elif response_text.startswith("```"):
                response_text = response_text[3:]
                had_markdown = True
            if response_text.endswith("```"):
                response_text = response_text[:-3]
                had_markdown = True
            response_text = response_text.strip()
            
            # Parse JSON
            parsed_json = json.loads(response_text)
            example['parsed_response'] = {
                'content': parsed_json,
                'had_markdown': had_markdown
            }
            
            # Validate and normalize
            validated = self.resolver._validate_and_normalize(parsed_json)
            example['validated_response'] = validated
            
            print(f"✅ Successfully captured {year} {make} {model}")
            
        except Exception as e:
            api_time = (time.time() - api_start) * 1000
            example['error'] = {
                'type': type(e).__name__,
                'message': str(e),
                'duration_ms': api_time
            }
            print(f"❌ Error capturing {year} {make} {model}: {e}")
        
        return example
    
    def save_to_markdown(self, filename: str = "PAST_EXAMPLES.md"):
        """Save all examples to a markdown file."""
        md_content = f"""# Past Examples - Vehicle Resolution System

This document contains complete input/output examples from the vehicle resolution system.
Each example shows the exact prompt sent to Google Gemini API and the complete response received.

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Examples**: {len(self.examples)}

---

"""
        
        for i, example in enumerate(self.examples, 1):
            md_content += f"""## Example {i}: {example['input']['year']} {example['input']['make']} {example['input']['model']}

### Input

- **Year**: {example['input']['year']}
- **Make**: {example['input']['make']}
- **Model**: {example['input']['model']}
- **Vehicle Key**: `{example['input']['vehicle_key']}`
- **Timestamp**: {example['timestamp']}

### Database Check

{example['database_check']['message']}

### Prompt Sent to API

**Length**: {example['prompt']['length']} characters

```
{example['prompt']['content']}
```

### API Configuration

```json
{json.dumps(example['api_config'], indent=2)}
```

"""
            
            if example.get('error'):
                md_content += f"""### Error

**Type**: {example['error']['type']}
**Message**: {example['error']['message']}
**Duration**: {example['error']['duration_ms']:.2f}ms

"""
            else:
                md_content += f"""### Raw API Response

**Duration**: {example['raw_response']['duration_ms']:.2f}ms ({example['raw_response']['duration_ms']/1000:.2f} seconds)
**Length**: {example['raw_response']['length']} characters
**Markdown Wrapper**: {'Yes' if example['parsed_response']['had_markdown'] else 'No'}

```
{example['raw_response']['content']}
```

### Parsed JSON Response

```json
{json.dumps(example['parsed_response']['content'], indent=2)}
```

### Validated & Normalized Results

"""
                
                for field_name, field_data in example['validated_response'].items():
                    md_content += f"""#### {field_name.upper()}

- **Value**: `{field_data.get('value')}`
- **Status**: `{field_data.get('status')}`
- **Confidence**: `{field_data.get('confidence', 0.0):.2f}`
"""
                    if 'unit' in field_data:
                        md_content += f"- **Unit**: `{field_data.get('unit')}`\n"
                    
                    citations = field_data.get('citations', [])
                    md_content += f"- **Citations**: {len(citations)}\n\n"
                    
                    for j, citation in enumerate(citations, 1):
                        md_content += f"""  **Citation {j}** ({citation.get('source_type', 'unknown').upper()}):
  - **URL**: {citation.get('url', 'N/A')}
  - **Quote**: "{citation.get('quote', 'N/A')[:200]}{'...' if len(citation.get('quote', '')) > 200 else ''}"
  
"""
                
                md_content += f"""### Summary

- **Total Latency**: {example['latency_ms']:.2f}ms ({example['latency_ms']/1000:.2f} seconds)
- **Fields Resolved**: {len(example['validated_response'])}
- **Total Citations**: {sum(len(f.get('citations', [])) for f in example['validated_response'].values())}

"""
            
            md_content += "---\n\n"
        
        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"\n✅ Saved {len(self.examples)} examples to {filename}")


def main():
    """Run 5 examples and save to markdown."""
    print("\n" + "="*80)
    print("CAPTURING 5 EXAMPLES FOR DOCUMENTATION")
    print("="*80)
    
    # Test vehicles from 1990-2010
    test_vehicles = [
        (1992, "Mazda", "Miata"),
        (1998, "BMW", "M3"),
        (2001, "Audi", "TT"),
        (2005, "Subaru", "WRX"),
        (2008, "Nissan", "GT-R")
    ]
    
    capture = ExampleCapture()
    
    for i, (year, make, model) in enumerate(test_vehicles, 1):
        print(f"\n{'='*80}")
        print(f"EXAMPLE {i} of {len(test_vehicles)}: {year} {make} {model}")
        print(f"{'='*80}")
        
        example = capture.capture_example(year, make, model)
        capture.examples.append(example)
        
        # Wait between examples
        if i < len(test_vehicles):
            print(f"\nWaiting 3 seconds before next example...")
            time.sleep(3)
    
    # Save to markdown
    capture.save_to_markdown("PAST_EXAMPLES.md")
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    for i, example in enumerate(capture.examples, 1):
        status = "✅ SUCCESS" if not example.get('error') else "❌ FAILED"
        latency = f"{example['latency_ms']:.2f}ms" if example.get('latency_ms') else "N/A"
        print(f"Example {i}: {example['input']['year']} {example['input']['make']} {example['input']['model']} - {status} ({latency})")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

