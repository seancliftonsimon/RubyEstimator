# Transparency Test Script

## Overview

The `transparency_test.py` script provides **full transparency** into the Google Gemini API interactions. It shows you:

1. **Exact prompts** being sent to the API
2. **API configuration** (model, tools, temperature)
3. **Raw responses** from Google (or error messages)
4. **How responses are parsed** and interpreted
5. **Final results** after validation and normalization

## Purpose

This script helps you understand exactly what is happening when your application queries the Google Gemini API with Search Grounding. You can use it to:

- Debug API interactions
- Refine prompts for better results
- Understand how responses are interpreted
- Verify that the correct data is being extracted

## Usage

### Prerequisites

1. **API Key**: Make sure your `GEMINI_API_KEY` is set in:
   - `.streamlit/secrets.toml` (for Streamlit), OR
   - Environment variable `GEMINI_API_KEY`

2. **Database** (optional): The script will work without a database connection, but it won't be able to check if vehicles exist in the database.

### Running the Script

```bash
# On Windows (PowerShell)
$env:PYTHONIOENCODING='utf-8'; python transparency_test.py

# On Linux/Mac
PYTHONIOENCODING=utf-8 python transparency_test.py
```

### What It Does

The script runs **two test examples** with vehicles that are likely NOT in your database:

1. **2023 Rivian R1T**
2. **2024 Lucid Air**

For each vehicle, it will:

1. ✅ Check if the vehicle exists in the database
2. ✅ Build and display the exact prompt
3. ✅ Show the API configuration
4. ✅ Make the API call (takes 15-40 seconds)
5. ✅ Display the raw response from Google
6. ✅ Show how the response is parsed
7. ✅ Display the final interpreted results

## Output Format

### Prompt Display

```
================================================================================
FULL PROMPT CONTENT:
================================================================================
Find specs for 2023 Rivian R1T. Return JSON ONLY.

FIND 4 FIELDS:
1. curb_weight (lbs, determine the most likely and sensible value...)
2. aluminum_engine (true/false, needs explicit "aluminum")
3. aluminum_rims (true/false, "aluminum" or "alloy")
4. catalytic_converters (count, integer, determine the most likely...)

SOURCES: Use any available sources (mark "oem" for manufacturer sites...)
...
```

### API Configuration

```
Model: gemini-2.0-flash-exp
Config: {
  "tools": [
    {
      "google_search": {}
    }
  ],
  "temperature": 0
}
```

### Raw Response

Shows the complete, unmodified response from Google Gemini API, including any markdown wrappers.

### Parsed Results

Shows the JSON structure after parsing, and the final interpreted values with:
- Field values
- Status (found/not_found/conflicting)
- Confidence scores
- Citations (URLs and quotes)

## Customizing Test Vehicles

To test different vehicles, edit the `test_vehicles` list in the `main()` function:

```python
test_vehicles = [
    (2023, "Rivian", "R1T"),
    (2024, "Lucid", "Air")
]
```

## Understanding the Output

### Prompt Structure

The prompt asks Gemini to:
1. Find 4 specific fields for the vehicle
2. Use Google Search Grounding to find real-time web data
3. Return structured JSON with citations
4. Mark sources as "oem" (manufacturer) or "secondary" (other sites)

### Response Interpretation

The script shows:
- **Raw response**: Exactly what Google returns
- **Parsed JSON**: After removing markdown wrappers
- **Validated fields**: After normalization and validation
- **Confidence scores**: Calculated based on source quality

### Citation Sources

Each field includes citations with:
- **URL**: Source website
- **Quote**: Relevant excerpt from the source
- **Source Type**: "oem" (manufacturer) or "secondary" (other)

## Troubleshooting

### API Key Expired

If you see:
```
Error: API key expired. Please renew the API key.
```

1. Get a new API key from https://aistudio.google.com/app/apikey
2. Update `.streamlit/secrets.toml` or environment variable
3. Run the script again

### Database Connection Error

If you see database connection errors, the script will still work - it just won't be able to check if vehicles exist in the database. This is fine for testing purposes.

### Encoding Issues (Windows)

If you see encoding errors, make sure to set the environment variable:
```powershell
$env:PYTHONIOENCODING='utf-8'
```

## Example Output

When successful, you'll see output like:

```
================================================================================
📥 RAW RESPONSE FROM GOOGLE GEMINI API
================================================================================
API Call Duration: 23456.78ms (23.46 seconds)
Response Length: 1234 characters

================================================================================
FULL RAW RESPONSE:
================================================================================
{
  "curb_weight": {
    "value": 7150,
    "unit": "lbs",
    "status": "found",
    "citations": [
      {
        "url": "https://rivian.com/support/article/r1t-specifications",
        "quote": "Curb weight: 7,150 lbs",
        "source_type": "oem"
      }
    ]
  },
  ...
}
```

## Next Steps

After running the script and seeing the transparency output:

1. **Review the prompts**: Are they clear and specific enough?
2. **Check the responses**: Are the citations accurate and relevant?
3. **Verify the interpretation**: Are the values being extracted correctly?
4. **Refine if needed**: Adjust prompts in `single_call_gemini_resolver.py` if results need improvement

## Files

- `transparency_test.py`: The main script
- `single_call_gemini_resolver.py`: Contains the prompt building logic (line 173-195)

