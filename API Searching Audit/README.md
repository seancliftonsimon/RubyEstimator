# API Searching Audit

This folder contains all documentation and tools for auditing and understanding the Google Gemini API search process used in the vehicle resolution system.

## Contents

### Documentation Files

1. **SYSTEM_BREAKDOWN.md** - Complete detailed breakdown of the entire system
   - Step-by-step explanation of all 7 stages
   - Concrete examples from actual API calls
   - Code references with line numbers
   - Confidence scoring algorithm details
   - Database schema and persistence details

2. **SYSTEM_QUICK_REFERENCE.md** - Quick reference guide
   - Visual flow diagram
   - Data flow examples
   - Key metrics table
   - Confidence score reference
   - Field validation rules
   - Common issues & solutions

3. **TRANSPARENCY_TEST_README.md** - Documentation for the transparency test script
   - Usage instructions
   - Output format explanation
   - Troubleshooting guide

4. **PAST_EXAMPLES.md** - Complete input/output examples
   - 5 real examples from actual API calls
   - Full prompts sent to API
   - Complete raw responses received
   - Parsed and validated results
   - All citations with URLs and quotes

### Script Files

1. **transparency_test.py** - Interactive transparency testing script
   - Shows exact prompts being sent
   - Displays raw API responses
   - Shows how responses are parsed
   - Displays final interpreted results
   - Run with: `python transparency_test.py`

2. **capture_examples.py** - Script to capture examples for documentation
   - Runs multiple examples
   - Captures complete input/output
   - Saves to PAST_EXAMPLES.md
   - Run with: `python capture_examples.py`

## Usage

### Running Transparency Tests

From the project root directory:

```bash
# Windows PowerShell
$env:PYTHONIOENCODING='utf-8'; python "API Searching Audit/transparency_test.py"

# Linux/Mac
PYTHONIOENCODING=utf-8 python "API Searching Audit/transparency_test.py"
```

### Capturing New Examples

From the project root directory:

```bash
# Windows PowerShell
$env:PYTHONIOENCODING='utf-8'; python "API Searching Audit/capture_examples.py"

# Linux/Mac
PYTHONIOENCODING=utf-8 python "API Searching Audit/capture_examples.py"
```

## Key Insights

### System Flow
1. Check database cache
2. Build prompt (~1,150 characters)
3. Call Google Gemini API with Search Grounding (12-17 seconds)
4. Parse JSON response
5. Validate & normalize fields
6. Calculate confidence scores
7. Store in database

### Key Metrics
- **Prompt Length**: ~1,150 characters
- **API Call Duration**: 12-17 seconds
- **Response Length**: 3,500-4,700 characters
- **Fields Resolved**: 4 (curb_weight, aluminum_engine, aluminum_rims, catalytic_converters)
- **Citations per Field**: 1-4 citations
- **Confidence Range**: 0.0 - 0.95

### Confidence Scoring
- **0.0**: Not found
- **0.4**: Conflicting sources
- **0.6**: Found, weak evidence
- **0.7**: 1 secondary source
- **0.85**: 2+ secondary sources
- **0.95**: OEM source

## Files Created

All files in this folder were created during the API searching audit process to provide full transparency into:
- What prompts are sent to Google API
- What responses are received
- How responses are interpreted
- How confidence scores are calculated
- How data is validated and stored

## Notes

- Scripts import from the parent directory, so they should be run from the project root
- All examples use real API calls with actual vehicles
- The PAST_EXAMPLES.md file contains complete, unmodified API responses
- All timestamps and latencies are from actual API calls

