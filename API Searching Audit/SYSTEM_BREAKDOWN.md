# Complete System Breakdown: Vehicle Resolution with Google Gemini API

## Overview

This document provides a complete, step-by-step breakdown of how the vehicle resolution system works, from user input to final database storage. All examples are based on actual API interactions from the transparency tests.

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Step 1: Prompt Construction](#step-1-prompt-construction)
3. [Step 2: API Call Configuration](#step-2-api-call-configuration)
4. [Step 3: Google Search Grounding Process](#step-3-google-search-grounding-process)
5. [Step 4: Response Parsing](#step-4-response-parsing)
6. [Step 5: Validation & Normalization](#step-5-validation--normalization)
7. [Step 6: Confidence Scoring](#step-6-confidence-scoring)
8. [Step 7: Database Persistence](#step-7-database-persistence)
9. [Complete Example Walkthrough](#complete-example-walkthrough)

---

## System Architecture

```
User Input (Year, Make, Model)
    ↓
[1] Check Database Cache
    ↓ (if not found)
[2] Build Prompt
    ↓
[3] Call Google Gemini API with Search Grounding
    ↓
[4] Parse JSON Response
    ↓
[5] Validate & Normalize Fields
    ↓
[6] Calculate Confidence Scores
    ↓
[7] Store in Database
    ↓
Return Results to User
```

---

## Step 1: Prompt Construction

### Location
`single_call_gemini_resolver.py`, lines 173-195

### How It Works

The prompt is built dynamically by inserting the vehicle information into a template. The template is concise (~650 characters) and optimized for speed.

### Actual Prompt Example (1995 Toyota Supra)

```
Find specs for 1995 Toyota Supra. Return JSON ONLY.

FIND 4 FIELDS:
1. curb_weight (lbs, determine the most likely and sensible value based on available data - use base trim if identifiable, or most common value)
2. aluminum_engine (true/false, needs explicit "aluminum")
3. aluminum_rims (true/false, "aluminum" or "alloy")
4. catalytic_converters (count, integer, determine the most likely and sensible number)

SOURCES: Use any available sources (mark "oem" for manufacturer sites, "secondary" for others). Include URL + quote.

STATUS: "found" (has data), "not_found" (no data, value=null), "conflicting" (unclear, value=null)

IMPORTANT: If the vehicle does not appear to exist or cannot be verified, set status to "not_found" for all fields and return null values.

RETURN JSON:
{
  "curb_weight": {"value": 3310, "unit": "lbs", "status": "found", "citations": [{"url": "...", "quote": "...", "source_type": "oem"}]},
  "aluminum_engine": {"value": true, "status": "found", "citations": [...]},
  "aluminum_rims": {"value": true, "status": "found", "citations": [...]},
  "catalytic_converters": {"value": 2, "status": "found", "citations": [...]}
}
```

### Key Design Decisions

1. **Concise Format**: Only 1,155 characters (optimized for speed)
2. **Explicit Instructions**: Clear field definitions and requirements
3. **JSON Schema Example**: Shows expected structure
4. **Source Attribution**: Requests URLs and quotes for citations
5. **Status Handling**: Explicit status values (found/not_found/conflicting)

### Code Implementation

```python
def _build_prompt(self, year: int, make: str, model: str) -> str:
    """Build concise prompt optimized for speed."""
    return f"""Find specs for {year} {make} {model}. Return JSON ONLY.
    
    FIND 4 FIELDS:
    1. curb_weight (lbs, determine the most likely and sensible value...)
    2. aluminum_engine (true/false, needs explicit "aluminum")
    3. aluminum_rims (true/false, "aluminum" or "alloy")
    4. catalytic_converters (count, integer, determine the most likely...)
    
    SOURCES: Use any available sources (mark "oem" for manufacturer sites...)
    STATUS: "found" (has data), "not_found" (no data, value=null), "conflicting"...
    
    RETURN JSON:
    {{
      "curb_weight": {{"value": 3310, "unit": "lbs", "status": "found", "citations": [...]}},
      ...
    }}"""
```

---

## Step 2: API Call Configuration

### Location
`single_call_gemini_resolver.py`, lines 239-265

### Configuration Details

```python
config = {
    "tools": [{"google_search": {}}],  # Enable Google Search Grounding
    "temperature": 0,                   # Deterministic responses
}

response = self.client.models.generate_content(
    model="gemini-2.0-flash-exp",      # Fast experimental model
    contents=prompt,                    # The prompt from Step 1
    config=config                       # Search Grounding enabled
)
```

### What Each Setting Does

1. **`tools: [{"google_search": {}}]`**
   - Enables Google Search Grounding
   - Allows Gemini to search the web in real-time
   - Provides citations from actual web pages

2. **`temperature: 0`**
   - Makes responses deterministic
   - Reduces variability in JSON structure
   - Improves consistency

3. **`model: "gemini-2.0-flash-exp"`**
   - Fast experimental model
   - Optimized for speed with Search Grounding
   - ~12-17 seconds per call (vs ~35-40s for standard models)

### API Call Timing

- **1995 Toyota Supra**: 12.28 seconds
- **2003 Honda S2000**: 16.82 seconds

The variation depends on:
- Number of web pages to search
- Complexity of information extraction
- Network latency

---

## Step 3: Google Search Grounding Process

### What Happens Behind the Scenes

When you call the API with `google_search` enabled, Google performs these steps:

1. **Query Generation** (1-2 seconds)
   - Gemini analyzes your prompt
   - Generates optimized search queries
   - Example: "1995 Toyota Supra curb weight specifications"

2. **Web Search** (8-12 seconds)
   - Google searches for relevant pages
   - Ranks results by relevance
   - Selects top sources (typically 3-10 pages)

3. **Content Extraction** (3-5 seconds)
   - Fetches content from selected pages
   - Extracts relevant text snippets
   - Identifies key information

4. **Analysis** (5-8 seconds)
   - Gemini analyzes extracted content
   - Cross-references multiple sources
   - Determines most accurate values

5. **Response Generation** (1-2 seconds)
   - Formats JSON response
   - Includes citations with URLs and quotes
   - Marks source types (OEM vs secondary)

### Actual Search Results Example

For **1995 Toyota Supra**, Google found:

**Curb Weight Citations:**
- Source 1: "Curb Weight. 3,215 lbs." (secondary source)
- Source 2: "3210 lbs" (secondary source)

**Aluminum Engine Citation:**
- Source: "With a cast iron block, aluminum cylinder heads, and forged internals, the 2JZ used a sequential turbo setup..." (secondary source)

**Aluminum Rims Citations:**
- Source 1: "Toyota Supra 17x9. 5 OEM Alloy Rim 1994-1998" (secondary source)
- Source 2: "All pictures will specify if the 1995 Toyota Supra Wheels are Aluminum Alloy..." (secondary source)

### Citation URLs

Google provides redirect URLs that look like:
```
https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF5G3OiyPZ_FwXIyxYcdH9m1Rmfwuv9Q5gbqA32sX2ag93RV4hg8FqOtjLKnHMNSyEGRYkcDnSuuVpjSJ7MFdsKxy8mEI1SdhpWOLLBu1vyVkXXI29nvojgtDB1R_wWIo9oaYSIY4uaydsNeNXzIZOU8V5VGg==
```

These are Google's internal redirect URLs that point to the actual source pages. When clicked, they redirect to the original website.

---

## Step 4: Response Parsing

### Location
`single_call_gemini_resolver.py`, lines 295-347

### Raw Response Format

Google returns the JSON wrapped in markdown code blocks:

```json
```json
{
  "curb_weight": {
    "value": 3215,
    "unit": "lbs",
    "status": "found",
    "citations": [...]
  },
  ...
}
```
```

### Parsing Process

1. **Strip Markdown Wrappers**
   ```python
   if response_text.startswith("```json"):
       response_text = response_text[7:]  # Remove ```json
   if response_text.endswith("```"):
       response_text = response_text[:-3]  # Remove closing ```
   ```

2. **Parse JSON**
   ```python
   result = json.loads(response_text)
   ```

3. **Validate Structure**
   - Check for required fields
   - Verify field types
   - Log any missing fields

### Actual Parsed Response (1995 Toyota Supra)

```json
{
  "curb_weight": {
    "value": 3215,
    "unit": "lbs",
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/...",
        "quote": "Curb Weight. 3,215 lbs.",
        "source_type": "secondary"
      },
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/...",
        "quote": "3210 lbs",
        "source_type": "secondary"
      }
    ]
  },
  "aluminum_engine": {
    "value": true,
    "status": "found",
    "citations": [
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/...",
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
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/...",
        "quote": "Toyota Supra 17x9. 5 OEM Alloy Rim 1994-1998",
        "source_type": "secondary"
      },
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/...",
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
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/...",
        "quote": "The average price for a 1995 Toyota Supra Catalytic Converter...",
        "source_type": "secondary"
      },
      {
        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/...",
        "quote": "What is the general description of the catalytic converter on Toyota Supra? A: The catalytic converter in these vehicles is of a three way type...",
        "source_type": "oem"
      }
    ]
  }
}
```

---

## Step 5: Validation & Normalization

### Location
`single_call_gemini_resolver.py`, lines 406-509

### Process Overview

Each field goes through validation and normalization to ensure:
- Correct data types
- Reasonable value ranges
- Consistency between status and value

### Field-Specific Validation

#### 1. Curb Weight

**Normalization Rules:**
- Convert to float
- Validate range: 1,500 - 10,000 lbs
- Handle multiple values (use median if list provided)

**Example (1995 Toyota Supra):**
```python
Input: 3215 (from API)
Validation: 1500 <= 3215 <= 10000 ✓
Output: 3215.0 (float)
```

**Example with Multiple Values:**
```python
Input: [3210, 3215, 3220]  # If API returns multiple weights
Process: Sort → [3210, 3215, 3220] → Median = 3215
Output: 3215.0
```

#### 2. Aluminum Engine

**Normalization Rules:**
- Convert to boolean
- Handle string representations ("true", "yes", "1" → True)
- If status is "not_found" or "conflicting", set to None

**Example (1995 Toyota Supra):**
```python
Input: true (from API)
Status: "found"
Validation: Boolean conversion ✓
Output: True
```

**Edge Case:**
```python
Input: true (from API)
Status: "conflicting"  # Inconsistent!
Normalization: Set to None (status takes precedence)
Output: None
```

#### 3. Aluminum Rims

**Normalization Rules:**
- Same as aluminum_engine
- Accepts "aluminum" or "alloy" in source quotes

**Example (1995 Toyota Supra):**
```python
Input: true (from API)
Status: "found"
Citations: ["OEM Alloy Rim", "Aluminum Alloy"]
Validation: Boolean conversion ✓
Output: True
```

#### 4. Catalytic Converters

**Normalization Rules:**
- Convert to integer
- Validate range: 0 - 10
- If status is "conflicting", set to None

**Example (1995 Toyota Supra):**
```python
Input: 2 (from API)
Status: "conflicting"  # Sources disagree
Normalization: Set to None (conflicting status)
Output: None
```

**Example (2003 Honda S2000):**
```python
Input: 1 (from API)
Status: "found"
Validation: 0 <= 1 <= 10 ✓
Output: 1
```

### Status-Value Consistency Check

The system enforces that if status indicates no data, the value must be None:

```python
if status in ("not_found", "conflicting"):
    normalized_value = None
    if raw_value is not None:
        logger.debug(f"status='{status}' but value provided, setting to None")
```

---

## Step 6: Confidence Scoring

### Location
`single_call_gemini_resolver.py`, lines 595-622

### Scoring Algorithm

Confidence scores range from 0.0 to 0.95 and are calculated based on:

1. **Status**
   - `not_found`: 0.0
   - `conflicting`: 0.4
   - `found`: Continue to source analysis

2. **Source Quality** (if status is "found")
   - **OEM source**: 0.95 (highest confidence)
   - **2+ secondary sources agreeing**: 0.85
   - **1 secondary source**: 0.70
   - **Found but weak evidence**: 0.60

### Actual Examples

#### Example 1: 1995 Toyota Supra - Curb Weight

```python
Status: "found"
Citations: 2 secondary sources
  - Source 1: "Curb Weight. 3,215 lbs."
  - Source 2: "3210 lbs"
  
Calculation:
  - Status is "found" ✓
  - 2 secondary sources ✓
  - No OEM sources
  - Confidence: 0.85 (2+ secondary sources agreeing)
```

#### Example 2: 1995 Toyota Supra - Aluminum Engine

```python
Status: "found"
Citations: 1 secondary source
  - Source: "With a cast iron block, aluminum cylinder heads..."
  
Calculation:
  - Status is "found" ✓
  - 1 secondary source
  - Confidence: 0.70 (1 secondary source)
```

#### Example 3: 2003 Honda S2000 - Aluminum Engine

```python
Status: "found"
Citations: 4 secondary sources
  - Source 1: "Block Material, Aluminum Alloy..."
  - Source 2: "Aluminum Alloy w/ Fibre Reinforced..."
  - Source 3: "The engine was made of aluminum."
  - Source 4: "Cylinder block material, Aluminum..."
  
Calculation:
  - Status is "found" ✓
  - 4 secondary sources (2+ agreeing) ✓
  - Confidence: 0.85 (2+ secondary sources agreeing)
```

#### Example 4: 1995 Toyota Supra - Catalytic Converters

```python
Status: "conflicting"
Citations: 2 sources (1 OEM, 1 secondary)
  - Source 1: "The average price for a 1995 Toyota Supra Catalytic Converter..."
  - Source 2: "The catalytic converter in these vehicles is of a three way type..." (OEM)
  
Calculation:
  - Status is "conflicting"
  - Confidence: 0.40 (conflicting status, regardless of sources)
  - Value set to None (conflicting status)
```

### Code Implementation

```python
def _calculate_confidence(self, field_data: Dict[str, Any]) -> float:
    status = field_data.get("status", "not_found")
    citations = field_data.get("citations", [])
    
    if status == "not_found":
        return 0.0
    
    if status == "conflicting":
        return 0.4
    
    # Status is "found"
    if not citations:
        return 0.5
    
    # Check for OEM sources
    has_oem = any(c.get("source_type") == "oem" for c in citations)
    if has_oem:
        return 0.95
    
    # Count secondary sources
    secondary_count = sum(1 for c in citations if c.get("source_type") == "secondary")
    if secondary_count >= 2:
        return 0.85
    elif secondary_count == 1:
        return 0.70
    
    return 0.60
```

---

## Step 7: Database Persistence

### Location
`single_call_gemini_resolver.py`, lines 749-897

### Database Schema

The system uses 4 main tables:

1. **`vehicles`**: Basic vehicle info
2. **`field_values`**: Resolved field values with confidence
3. **`evidence`**: Individual citations/evidence
4. **`runs`**: Run metadata (timing, status)

### Persistence Process

#### 1. Insert Run Record

```sql
INSERT INTO runs (run_id, started_at, finished_at, total_ms, status)
VALUES ('abc123...', '2025-11-06 10:13:47', '2025-11-06 10:13:59', 12280, 'complete')
```

#### 2. Upsert Vehicle Record

```sql
INSERT INTO vehicles (vehicle_key, year, make, model, created_at, updated_at)
VALUES ('1995_toyota_supra', 1995, 'Toyota', 'Supra', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT(vehicle_key) DO UPDATE SET
    year = excluded.year,
    make = excluded.make,
    model = excluded.model,
    updated_at = CURRENT_TIMESTAMP
```

#### 3. Insert Field Values

For each field (curb_weight, aluminum_engine, aluminum_rims, catalytic_converters):

```sql
INSERT INTO field_values (vehicle_key, field, value_json, updated_at)
VALUES (
    '1995_toyota_supra',
    'curb_weight',
    '{"value": 3215.0, "unit": "lbs", "status": "found", "confidence": 0.85, "source_name": "gemini_search_grounding", "method": "single_call_gemini"}',
    CURRENT_TIMESTAMP
)
ON CONFLICT(vehicle_key, field) DO UPDATE SET
    value_json = excluded.value_json,
    updated_at = CURRENT_TIMESTAMP
```

#### 4. Insert Evidence (Citations)

For each citation in each field:

```sql
INSERT INTO evidence (
    run_id, vehicle_key, field, value_json, quote, source_url, source_hash, fetched_at
) VALUES (
    'abc123...',
    '1995_toyota_supra',
    'curb_weight',
    '{"value": 3215.0, "unit": "lbs", "source_type": "secondary", "confidence": 0.85}',
    'Curb Weight. 3,215 lbs.',
    'https://vertexaisearch.cloud.google.com/grounding-api-redirect/...',
    'md5_hash_of_url_quote',
    CURRENT_TIMESTAMP
)
ON CONFLICT (run_id, field) DO UPDATE SET
    value_json = EXCLUDED.value_json,
    quote = EXCLUDED.quote,
    source_url = EXCLUDED.source_url,
    source_hash = EXCLUDED.source_hash,
    fetched_at = EXCLUDED.fetched_at
```

### Complete Example: 1995 Toyota Supra

**Run Record:**
- `run_id`: `abc123def456...`
- `total_ms`: 12280
- `status`: `complete`

**Vehicle Record:**
- `vehicle_key`: `1995_toyota_supra`
- `year`: 1995
- `make`: `Toyota`
- `model`: `Supra`

**Field Values (4 records):**
1. `curb_weight`: `{"value": 3215.0, "unit": "lbs", "status": "found", "confidence": 0.85, ...}`
2. `aluminum_engine`: `{"value": true, "status": "found", "confidence": 0.70, ...}`
3. `aluminum_rims`: `{"value": true, "status": "found", "confidence": 0.85, ...}`
4. `catalytic_converters`: `{"value": null, "status": "conflicting", "confidence": 0.40, ...}`

**Evidence Records (7 total):**
- 2 citations for `curb_weight`
- 1 citation for `aluminum_engine`
- 2 citations for `aluminum_rims`
- 2 citations for `catalytic_converters`

---

## Complete Example Walkthrough

### Input: 2003 Honda S2000

#### Step 1: Prompt Construction
```
Find specs for 2003 Honda S2000. Return JSON ONLY.
[Full prompt as shown earlier]
```
**Length**: 1,154 characters

#### Step 2: API Call
```python
Model: gemini-2.0-flash-exp
Config: {"tools": [{"google_search": {}}], "temperature": 0}
Duration: 16.82 seconds
```

#### Step 3: Google Search Grounding
Google searches for:
- "2003 Honda S2000 curb weight"
- "2003 Honda S2000 aluminum engine"
- "2003 Honda S2000 aluminum rims"
- "2003 Honda S2000 catalytic converter"

Finds and extracts from multiple sources.

#### Step 4: Raw Response
```json
```json
{
  "curb_weight": {
    "value": 2809,
    "unit": "lbs",
    "status": "found",
    "citations": [
      {"url": "...", "quote": "Curb Weight. 2809 pounds.", "source_type": "secondary"},
      {"url": "...", "quote": "Base Curb Weight (lbs) 2809.", "source_type": "secondary"},
      {"url": "...", "quote": "2,809 lbs.", "source_type": "secondary"}
    ]
  },
  "aluminum_engine": {
    "value": true,
    "status": "found",
    "citations": [
      {"url": "...", "quote": "Block Material, Aluminum Alloy w/Fiber-Reinforced...", "source_type": "secondary"},
      {"url": "...", "quote": "Aluminum Alloy w/ Fibre Reinforced...", "source_type": "secondary"},
      {"url": "...", "quote": "The engine was made of aluminum.", "source_type": "secondary"},
      {"url": "...", "quote": "Cylinder block material, Aluminum...", "source_type": "secondary"}
    ]
  },
  "aluminum_rims": {
    "value": true,
    "status": "found",
    "citations": [
      {"url": "...", "quote": "Alloy Wheels. Standard.", "source_type": "secondary"},
      {"url": "...", "quote": "Front, 16\" x 6.5\" Aluminum Alloy...", "source_type": "secondary"},
      {"url": "...", "quote": "Honda S2000 Disk, Aluminum Wheel...", "source_type": "secondary"}
    ]
  },
  "catalytic_converters": {
    "value": 1,
    "status": "found",
    "citations": [
      {"url": "...", "quote": "Low Back Pressure, Metal-Honeycomb Catalytic Converter...", "source_type": "secondary"}
    ]
  }
}
```
```

#### Step 5: Parsing
- Strip markdown: Remove ```json wrappers
- Parse JSON: Convert to Python dict
- Validate: Check all 4 fields present

#### Step 6: Validation & Normalization

**Curb Weight:**
- Input: `2809`
- Validation: `1500 <= 2809 <= 10000` ✓
- Output: `2809.0` (float)

**Aluminum Engine:**
- Input: `true`
- Status: `"found"`
- Output: `True` (boolean)

**Aluminum Rims:**
- Input: `true`
- Status: `"found"`
- Output: `True` (boolean)

**Catalytic Converters:**
- Input: `1`
- Status: `"found"`
- Validation: `0 <= 1 <= 10` ✓
- Output: `1` (integer)

#### Step 7: Confidence Scoring

**Curb Weight:**
- Status: `"found"`
- Citations: 3 secondary sources
- Confidence: **0.85** (2+ secondary sources agreeing)

**Aluminum Engine:**
- Status: `"found"`
- Citations: 4 secondary sources
- Confidence: **0.85** (2+ secondary sources agreeing)

**Aluminum Rims:**
- Status: `"found"`
- Citations: 3 secondary sources
- Confidence: **0.85** (2+ secondary sources agreeing)

**Catalytic Converters:**
- Status: `"found"`
- Citations: 1 secondary source
- Confidence: **0.70** (1 secondary source)

#### Step 8: Database Persistence

**Run Record:**
- `run_id`: `xyz789...`
- `total_ms`: 16820
- `status`: `complete`

**Vehicle Record:**
- `vehicle_key`: `2003_honda_s2000`
- `year`: 2003
- `make`: `Honda`
- `model`: `S2000`

**Field Values:**
- `curb_weight`: `{"value": 2809.0, "unit": "lbs", "status": "found", "confidence": 0.85}`
- `aluminum_engine`: `{"value": true, "status": "found", "confidence": 0.85}`
- `aluminum_rims`: `{"value": true, "status": "found", "confidence": 0.85}`
- `catalytic_converters`: `{"value": 1, "status": "found", "confidence": 0.70}`

**Evidence Records:**
- 3 citations for `curb_weight`
- 4 citations for `aluminum_engine`
- 3 citations for `aluminum_rims`
- 1 citation for `catalytic_converters`
- **Total: 11 evidence records**

#### Final Output

```python
{
    "vehicle_key": "2003_honda_s2000",
    "year": 2003,
    "make": "Honda",
    "model": "S2000",
    "fields": {
        "curb_weight": {
            "value": 2809.0,
            "unit": "lbs",
            "status": "found",
            "confidence": 0.85,
            "citations": [...]
        },
        "aluminum_engine": {
            "value": True,
            "status": "found",
            "confidence": 0.85,
            "citations": [...]
        },
        "aluminum_rims": {
            "value": True,
            "status": "found",
            "confidence": 0.85,
            "citations": [...]
        },
        "catalytic_converters": {
            "value": 1,
            "status": "found",
            "confidence": 0.70,
            "citations": [...]
        }
    },
    "run_id": "xyz789...",
    "latency_ms": 16820.0
}
```

---

## Key Insights for Refinement

### 1. Prompt Optimization

**Current Approach:**
- Concise (~1,150 characters)
- Explicit field definitions
- JSON schema example

**Potential Improvements:**
- Add more specific instructions for edge cases
- Clarify "base trim" vs "most common" for curb weight
- Specify how to handle conflicting sources

### 2. Source Quality

**Current Behavior:**
- Google Search Grounding finds sources automatically
- Most sources are "secondary" (not OEM)
- OEM sources are rare but highly valued (0.95 confidence)

**Potential Improvements:**
- Add instructions to prioritize OEM sources
- Request specific source types in prompt
- Validate source URLs before storing

### 3. Confidence Scoring

**Current Algorithm:**
- Simple rule-based system
- Based on source count and type
- Doesn't consider quote quality or agreement level

**Potential Improvements:**
- Factor in quote relevance
- Consider value agreement across sources
- Weight recent sources higher

### 4. Conflict Resolution

**Current Behavior:**
- Sets value to None if status is "conflicting"
- Confidence drops to 0.40

**Potential Improvements:**
- Try to resolve conflicts by source quality
- Use majority vote if sources disagree
- Provide multiple values with probabilities

### 5. Response Parsing

**Current Behavior:**
- Handles markdown wrappers
- Basic JSON validation
- Logs missing fields

**Potential Improvements:**
- More robust error recovery
- Partial parsing if some fields fail
- Better error messages for debugging

---

## Summary

The system works by:

1. **Building a concise, explicit prompt** that requests structured JSON
2. **Calling Google Gemini with Search Grounding** to search the web in real-time
3. **Parsing the JSON response** and handling markdown wrappers
4. **Validating and normalizing** each field to ensure data quality
5. **Calculating confidence scores** based on source quality and agreement
6. **Storing everything in the database** for future reference

The entire process takes **12-17 seconds** per vehicle and provides:
- Accurate field values
- Source citations with URLs and quotes
- Confidence scores for data quality assessment
- Complete audit trail in the database

This transparency allows you to refine the process by:
- Adjusting prompts for better results
- Understanding how Google finds sources
- Improving confidence scoring algorithms
- Handling edge cases more effectively

