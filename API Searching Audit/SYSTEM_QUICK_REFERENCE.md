# System Quick Reference Guide

## Flow Diagram

````
┌─────────────────────────────────────────────────────────────────┐
│                    USER INPUT                                    │
│              (Year, Make, Model)                                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              STEP 1: CHECK DATABASE CACHE                        │
│  • Look up vehicle_key in 'vehicles' table                      │
│  • If found: Return cached data (< 50ms)                        │
│  • If not found: Continue to API call                           │
└────────────────────┬────────────────────────────────────────────┘
                     │ (cache miss)
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              STEP 2: BUILD PROMPT                                │
│  • Insert vehicle info into template                            │
│  • Request 4 fields: curb_weight, aluminum_engine,              │
│    aluminum_rims, catalytic_converters                          │
│  • Request JSON format with citations                           │
│  • Length: ~1,150 characters                                    │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│         STEP 3: CALL GOOGLE GEMINI API                          │
│  • Model: gemini-2.0-flash-exp                                  │
│  • Tools: Google Search Grounding enabled                       │
│  • Temperature: 0 (deterministic)                               │
│  • Duration: 12-17 seconds                                      │
│                                                                  │
│  Google performs:                                                │
│  1. Query generation (1-2s)                                     │
│  2. Web search (8-12s)                                          │
│  3. Content extraction (3-5s)                                   │
│  4. Analysis (5-8s)                                             │
│  5. Response generation (1-2s)                                  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              STEP 4: PARSE RESPONSE                              │
│  • Strip markdown wrappers (```json)                            │
│  • Parse JSON                                                    │
│  • Validate structure (4 fields required)                       │
│  • Log any missing fields                                       │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│        STEP 5: VALIDATE & NORMALIZE                              │
│                                                                  │
│  curb_weight:                                                    │
│    • Convert to float                                            │
│    • Validate range: 1,500 - 10,000 lbs                         │
│    • Handle multiple values (use median)                        │
│                                                                  │
│  aluminum_engine:                                                │
│    • Convert to boolean                                          │
│    • Handle strings ("true", "yes", "1")                        │
│    • Set to None if status is "not_found" or "conflicting"      │
│                                                                  │
│  aluminum_rims:                                                  │
│    • Same as aluminum_engine                                     │
│                                                                  │
│  catalytic_converters:                                           │
│    • Convert to integer                                          │
│    • Validate range: 0 - 10                                      │
│    • Set to None if status is "conflicting"                     │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│           STEP 6: CALCULATE CONFIDENCE                           │
│                                                                  │
│  Scoring Rules:                                                  │
│  • not_found → 0.0                                               │
│  • conflicting → 0.4                                             │
│  • found + OEM source → 0.95                                     │
│  • found + 2+ secondary sources → 0.85                           │
│  • found + 1 secondary source → 0.70                             │
│  • found + weak evidence → 0.60                                  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│           STEP 7: STORE IN DATABASE                              │
│                                                                  │
│  Tables Updated:                                                 │
│  1. runs: Run metadata (timing, status)                         │
│  2. vehicles: Basic vehicle info                                │
│  3. field_values: Resolved values with confidence               │
│  4. evidence: Individual citations (URLs, quotes)               │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RETURN RESULTS                                │
│  • Field values                                                  │
│  • Confidence scores                                             │
│  • Citations (URLs, quotes, source types)                       │
│  • Run ID for tracking                                           │
└─────────────────────────────────────────────────────────────────┘
````

## Data Flow Example: 1995 Toyota Supra

### Input

```
Year: 1995
Make: Toyota
Model: Supra
```

### Prompt Sent (1,155 characters)

```
Find specs for 1995 Toyota Supra. Return JSON ONLY.
[Full prompt with field definitions and JSON schema]
```

### API Response (3,697 characters)

```json
{
	"curb_weight": {
		"value": 3215,
		"unit": "lbs",
		"status": "found",
		"citations": [
			{
				"url": "...",
				"quote": "Curb Weight. 3,215 lbs.",
				"source_type": "secondary"
			},
			{ "url": "...", "quote": "3210 lbs", "source_type": "secondary" }
		]
	},
	"aluminum_engine": {
		"value": true,
		"status": "found",
		"citations": [
			{
				"url": "...",
				"quote": "With a cast iron block, aluminum cylinder heads...",
				"source_type": "secondary"
			}
		]
	},
	"aluminum_rims": {
		"value": true,
		"status": "found",
		"citations": [
			{
				"url": "...",
				"quote": "Toyota Supra 17x9. 5 OEM Alloy Rim...",
				"source_type": "secondary"
			},
			{
				"url": "...",
				"quote": "All pictures will specify if the 1995 Toyota Supra Wheels are Aluminum Alloy...",
				"source_type": "secondary"
			}
		]
	},
	"catalytic_converters": {
		"value": 2,
		"status": "conflicting",
		"citations": [
			{
				"url": "...",
				"quote": "The average price for a 1995 Toyota Supra Catalytic Converter...",
				"source_type": "secondary"
			},
			{
				"url": "...",
				"quote": "The catalytic converter in these vehicles is of a three way type...",
				"source_type": "oem"
			}
		]
	}
}
```

### Validated & Normalized

```python
{
  "curb_weight": {
    "value": 3215.0,      # float, validated range
    "unit": "lbs",
    "status": "found",
    "confidence": 0.85,   # 2 secondary sources
    "citations": [...]
  },
  "aluminum_engine": {
    "value": True,        # boolean
    "status": "found",
    "confidence": 0.70,   # 1 secondary source
    "citations": [...]
  },
  "aluminum_rims": {
    "value": True,        # boolean
    "status": "found",
    "confidence": 0.85,   # 2 secondary sources
    "citations": [...]
  },
  "catalytic_converters": {
    "value": None,        # None because status is "conflicting"
    "status": "conflicting",
    "confidence": 0.40,   # conflicting status
    "citations": [...]
  }
}
```

### Database Records Created

- **1 run record**: `run_id`, `total_ms: 12280`, `status: complete`
- **1 vehicle record**: `1995_toyota_supra`, `1995`, `Toyota`, `Supra`
- **4 field_value records**: One for each field
- **7 evidence records**: One for each citation

## Key Metrics

| Metric                  | Value                                                                 |
| ----------------------- | --------------------------------------------------------------------- |
| **Prompt Length**       | ~1,150 characters                                                     |
| **API Call Duration**   | 12-17 seconds                                                         |
| **Response Length**     | 3,500-4,700 characters                                                |
| **Fields Resolved**     | 4 (curb_weight, aluminum_engine, aluminum_rims, catalytic_converters) |
| **Citations per Field** | 1-4 citations                                                         |
| **Confidence Range**    | 0.0 - 0.95                                                            |
| **Database Records**    | 1 run + 1 vehicle + 4 field_values + 7-11 evidence                    |

## Confidence Score Reference

| Scenario             | Confidence | Example                    |
| -------------------- | ---------- | -------------------------- |
| Not found            | 0.0        | No data available          |
| Conflicting sources  | 0.4        | Sources disagree on value  |
| Found, weak evidence | 0.6        | Found but limited proof    |
| 1 secondary source   | 0.7        | Single reliable source     |
| 2+ secondary sources | 0.85       | Multiple agreeing sources  |
| OEM source           | 0.95       | Official manufacturer data |

## Field Validation Rules

### Curb Weight

- **Type**: Float
- **Range**: 1,500 - 10,000 lbs
- **Multiple Values**: Use median
- **Unit**: Always "lbs"

### Aluminum Engine

- **Type**: Boolean (True/False/None)
- **Requirement**: Must explicitly mention "aluminum"
- **None if**: Status is "not_found" or "conflicting"

### Aluminum Rims

- **Type**: Boolean (True/False/None)
- **Accepts**: "aluminum" or "alloy"
- **None if**: Status is "not_found" or "conflicting"

### Catalytic Converters

- **Type**: Integer (0-10)
- **Range**: 0 - 10
- **None if**: Status is "conflicting"

## Common Issues & Solutions

### Issue: Conflicting Sources

**Example**: Catalytic converters for 1995 Toyota Supra

- **Problem**: Sources disagree on count
- **Solution**: Set status to "conflicting", value to None, confidence to 0.40
- **Refinement**: Could add logic to use majority vote or prioritize OEM sources

### Issue: Missing OEM Sources

**Problem**: Most sources are "secondary" (not OEM)

- **Current**: Confidence maxes at 0.85 for secondary sources
- **Refinement**: Add prompt instructions to prioritize OEM sources

### Issue: Markdown Wrappers

**Problem**: API returns JSON wrapped in ```json code blocks

- **Solution**: Strip wrappers before parsing
- **Status**: Handled automatically

### Issue: Multiple Weight Values

**Problem**: Different sources report different weights

- **Solution**: Use median value if multiple weights found
- **Example**: [3210, 3215, 3220] → 3215 (median)

## Refinement Opportunities

1. **Prompt Enhancement**

   - Add more specific instructions for edge cases
   - Clarify "base trim" vs "most common" for curb weight
   - Request OEM sources more explicitly

2. **Confidence Scoring**

   - Factor in quote relevance
   - Consider value agreement across sources
   - Weight recent sources higher

3. **Conflict Resolution**

   - Use majority vote for conflicting sources
   - Prioritize OEM sources in conflicts
   - Provide multiple values with probabilities

4. **Source Quality**

   - Validate source URLs before storing
   - Check for duplicate citations
   - Rate source reliability

5. **Error Handling**
   - More robust JSON parsing
   - Partial parsing if some fields fail
   - Better error messages for debugging
