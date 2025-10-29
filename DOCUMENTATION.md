# Ruby GEM Vehicle Resolution System - Complete Documentation

**Single-Call Gemini 2.5 Flash + Google Search Grounding**

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [System Overview](#system-overview)
3. [API Key Setup](#api-key-setup)
4. [Usage Examples](#usage-examples)
5. [Response Format](#response-format)
6. [Database Schema](#database-schema)
7. [Confidence Scoring](#confidence-scoring)
8. [Performance & Cost](#performance--cost)
9. [Deployment Guide](#deployment-guide)
10. [Troubleshooting](#troubleshooting)
11. [API Reference](#api-reference)

---

## Quick Start

### 1. Set API Key

Create `.streamlit/secrets.toml`:

```toml
[api]
GEMINI_API_KEY = "your-key-from-https://aistudio.google.com/app/apikey"
```

Or use environment variable:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

### 2. Test It

```bash
python test_single_call_gemini.py
```

### 3. Run Streamlit App

```bash
streamlit run app.py
```

---

## System Overview

### Architecture

```
Input (year/make/model)
  ↓
Prompt with source rules
  ↓
Gemini 2.5 Flash + Google Search Grounding
  ↓
Strict JSON response (responseSchema enforced)
  ↓
Validation & normalization
  ↓
Database persistence (4 tables)
```

### Key Features

- ✅ **Single request per vehicle** - One API call using `gemini-2.5-flash`
- ✅ **Google Search Grounding** - Real-time web search with automatic citations
- ✅ **Strict JSON only** - `responseMimeType: "application/json"`, no prose
- ✅ **Source rules in prompt** - OEM preferred, 2 agreeing secondaries fallback
- ✅ **Direct citations** - URLs and quotes from grounding metadata
- ✅ **No caching** - Always fresh data
- ✅ **Full logging** - Track timing bottlenecks and API calls

### Design Philosophy

> **"Keep it simple. One call, one result, direct to database."**

---

## API Key Setup

### Option 1: Streamlit Secrets (Recommended)

Copy the template:

```bash
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml`:

```toml
[api]
GEMINI_API_KEY = "your-actual-api-key"
```

### Option 2: Environment Variable

```bash
export GEMINI_API_KEY="your-api-key"
```

### Get API Key

Visit: https://aistudio.google.com/app/apikey

---

## Usage Examples

### Basic Python Usage

```python
from single_call_gemini_resolver import single_call_resolver

# Resolve a vehicle
result = single_call_resolver.resolve_vehicle(
    year=2020,
    make="Toyota",
    model="Camry"
)

# Access results
print(f"Vehicle: {result.vehicle_key}")
print(f"Latency: {result.latency_ms}ms")

# Get field values
weight = result.fields["curb_weight"]["value"]  # e.g., 3310
confidence = result.fields["curb_weight"]["confidence"]  # e.g., 0.95
status = result.fields["curb_weight"]["status"]  # "found"

print(f"Weight: {weight} lbs (confidence: {confidence:.2f})")
```

### Access Citations

```python
for citation in result.fields["curb_weight"]["citations"]:
    print(f"[{citation['source_type'].upper()}] {citation['url']}")
    print(f"  \"{citation['quote']}\"")
```

### Via Streamlit Integration

```python
from vehicle_data import process_vehicle

result = process_vehicle(2020, "Toyota", "Camry")

weight = result["curb_weight_lbs"]
confidence = result["confidence_scores"]["curb_weight"]
citations = result["citations"]["curb_weight"]
```

### Filter by Confidence

```python
high_confidence = {
    field: data["value"]
    for field, data in result.fields.items()
    if data["confidence"] >= 0.80
}
```

---

## Response Format

### JSON Structure

```json
{
  "curb_weight": {
    "value": 3310,
    "unit": "lbs",
    "status": "found",
    "citations": [
      {
        "url": "https://www.toyota.com/camry/2020/specifications/",
        "quote": "Curb Weight: 3,310 lbs",
        "source_type": "oem"
      }
    ]
  },
  "aluminum_engine": {
    "value": true,
    "status": "found",
    "citations": [...]
  },
  "aluminum_rims": {
    "value": true,
    "status": "found",
    "citations": [...]
  },
  "catalytic_converters": {
    "value": 2,
    "status": "found",
    "citations": [...]
  }
}
```

### Field Types

| Field                  | Type    | Unit  | Example  | Validation                   |
| ---------------------- | ------- | ----- | -------- | ---------------------------- |
| `curb_weight`          | `float` | lbs   | `3310.0` | 1500-10000                   |
| `aluminum_engine`      | `bool`  | -     | `true`   | Requires "aluminum" in quote |
| `aluminum_rims`        | `bool`  | -     | `true`   | Requires "aluminum"/"alloy"  |
| `catalytic_converters` | `int`   | count | `2`      | 0-10                         |

### Status Values

| Status        | Meaning                             | Typical Confidence |
| ------------- | ----------------------------------- | ------------------ |
| `found`       | Reliable value found with citations | 0.60 - 0.95        |
| `not_found`   | No reliable information found       | 0.00               |
| `conflicting` | Multiple conflicting values         | 0.40               |

### Source Types

| Type        | Description                                 | Preference                               |
| ----------- | ------------------------------------------- | ---------------------------------------- |
| `oem`       | Official manufacturer source                | **Primary** (confidence: 0.95)           |
| `secondary` | Reliable automotive database (KBB, Edmunds) | Fallback (2+ required, confidence: 0.85) |

---

## Database Schema

### Tables Overview

1. **`vehicles`**: Basic vehicle info (year, make, model, timestamps)
2. **`field_values`**: Resolved values with confidence scores
3. **`evidence`**: Individual citations from grounding metadata
4. **`runs`**: Run metadata (timing, status)

### Evidence Table (Key Feature)

Every citation creates one evidence row:

```sql
CREATE TABLE evidence (
    run_id TEXT NOT NULL,
    vehicle_key TEXT NOT NULL,
    field TEXT NOT NULL,
    value_json TEXT NOT NULL,
    quote TEXT,              -- Direct quote from source
    source_url TEXT,         -- URL from grounding metadata
    source_hash TEXT,        -- MD5 for deduplication
    fetched_at TIMESTAMP,
    PRIMARY KEY (run_id, field)
)
```

**Example row:**

```
run_id: abc123...
vehicle_key: 2020_toyota_camry
field: curb_weight
quote: "Curb Weight: 3,310 lbs"
source_url: https://www.toyota.com/camry/2020/specs/
```

### Query Examples

```sql
-- Recent resolutions
SELECT vehicle_key, updated_at, COUNT(*) as fields_resolved
FROM field_values
GROUP BY vehicle_key, updated_at
ORDER BY updated_at DESC
LIMIT 10;

-- Average confidence by field
SELECT field,
       AVG(CAST(json_extract(value_json, '$.confidence') AS REAL)) as avg_confidence
FROM field_values
GROUP BY field;

-- Evidence source breakdown
SELECT field,
       COUNT(*) as citation_count,
       COUNT(DISTINCT source_url) as unique_sources
FROM evidence
GROUP BY field;
```

---

## Confidence Scoring

### Calculation Rules

| Scenario              | Confidence | Explanation                |
| --------------------- | ---------- | -------------------------- |
| OEM source found      | **0.95**   | Official manufacturer data |
| 2+ secondary agreeing | **0.85**   | Multiple reliable sources  |
| 1 secondary           | **0.70**   | Single reliable source     |
| Found, weak evidence  | **0.60**   | Found but limited proof    |
| Conflicting           | **0.40**   | Sources disagree           |
| Not found             | **0.00**   | No information available   |

### Validation Rules

#### Curb Weight

- **Unit**: Must be in lbs
- **Range**: 1,500 - 10,000 lbs
- **Type**: Float

#### Aluminum Engine

- **Type**: Boolean (`true`/`false`)
- **Requirement**: Explicit "aluminum" wording

#### Aluminum Rims

- **Type**: Boolean (`true`/`false`)
- **Requirement**: "aluminum" or "alloy" wording

#### Catalytic Converters

- **Type**: Integer
- **Range**: 0-10 (typically 1-4)

---

## Performance & Cost

### Performance Metrics

| Metric         | Typical Value         | Target |
| -------------- | --------------------- | ------ |
| Total Latency  | 3-8 seconds           | <10s   |
| API Call       | ~4s (60-80% of total) | -      |
| Parsing        | <10ms                 | -      |
| Validation     | <20ms                 | -      |
| Database Write | <100ms                | -      |
| API Calls      | 1 per vehicle         | 1      |
| Token Usage    | ~1300 tokens          | <2000  |

### Cost Estimate

**Gemini 2.5 Flash Pricing (October 2024):**

| Tier     | Tokens             | Cost per Vehicle |
| -------- | ------------------ | ---------------- |
| **Free** | 1M/day, 15 req/min | $0               |
| **Paid** | Unlimited          | ~$0.002-0.005    |

**Monthly costs (paid tier):**

- 100 vehicles: $0.20-0.50
- 1,000 vehicles: $2-5
- 10,000 vehicles: $20-50

**Free tier limits:**

- 15 requests/minute
- 1,500 requests/day
- 1M tokens/day

---

## Deployment Guide

### Production Environment Variables

```bash
# Required
GEMINI_API_KEY=your-production-api-key

# Optional - PostgreSQL (recommended for production)
DATABASE_URL=postgresql://user:pass@host:port/db

# Or individual settings
PGHOST=your-db-host
PGPORT=5432
PGDATABASE=rubyestimator
PGUSER=your-db-user
PGPASSWORD=your-db-password
```

### Deployment Checklist

- [ ] ✅ API key set (`.streamlit/secrets.toml` or env var)
- [ ] ✅ Run test: `python test_single_call_gemini.py`
- [ ] ✅ Verify 3+ test vehicles resolve with confidence > 0.7
- [ ] ✅ Check database contains evidence rows
- [ ] ✅ Test Streamlit app displays results correctly
- [ ] ✅ Monitor logs for timing breakdowns
- [ ] ✅ Set up database backups (if using PostgreSQL)

### Health Checks

```bash
# Test API connectivity
python -c "from single_call_gemini_resolver import single_call_resolver; print('OK')"

# Check database
python -c "from database_config import test_database_connection; print(test_database_connection())"

# Quick vehicle test
python test_single_call_gemini.py
```

---

## Troubleshooting

### Common Issues

#### "GEMINI_API_KEY not set"

**Solution:**

```bash
# Check if key is set
python -c "import os; print(os.getenv('GEMINI_API_KEY', 'NOT SET'))"

# Set via Streamlit secrets
echo '[api]' > .streamlit/secrets.toml
echo 'GEMINI_API_KEY = "your-key"' >> .streamlit/secrets.toml

# Or environment variable
export GEMINI_API_KEY="your-key"
```

#### API Call Fails

**Check:**

- API key valid at https://aistudio.google.com/
- Not hitting rate limits (15 req/min on free tier)
- Network connectivity
- Logs show detailed error message

#### Fields Returning `null`

**Check `status` field:**

- `not_found`: Model couldn't find information
- `conflicting`: Multiple contradictory sources
- `found`: Check validation (value out of range?)

#### Low Confidence Scores

**Solutions:**

- Try more common vehicles (better indexed online)
- Check if OEM sources exist for that vehicle
- Review citations to see what was found
- Some vehicles may have limited online data

#### Slow Performance

**Check logs for timing breakdown:**

```
Total Time: 8523ms
  - API Call: 7200ms (84.5%)  ← Most time here
  - Parsing: 8ms
  - Validation: 15ms
  - Database: 100ms
```

Most time is in the Gemini API call with Search Grounding - this is normal.

### Logging

The system logs detailed information at each step:

```
======================================================================
🚗 RESOLVING: 2020 Toyota Camry
======================================================================
Vehicle Key: 2020_toyota_camry
Run ID: abc123...

📝 Building prompt...
✓ Prompt built in 2.15ms
Prompt length: 1245 characters

🌐 Calling Gemini API with Search Grounding...
Model: gemini-2.5-flash
✓ API call completed in 4523.45ms

📦 Parsing JSON response...
Response text length: 2145 characters
✓ JSON parsed in 3.12ms
Fields in response: ['curb_weight', 'aluminum_engine', ...]

✅ Validating and normalizing fields...
✓ Validation completed in 12.45ms
  • curb_weight: 3310 (status=found, confidence=0.95, citations=1)
  • aluminum_engine: True (status=found, confidence=0.95, citations=1)
  ...

💾 Persisting to database...
✓ Database write completed in 87.23ms

======================================================================
✅ RESOLUTION COMPLETE
Total Time: 4628.40ms (4.63s)
  - Prompt: 2.15ms
  - API Call: 4523.45ms (97.7%)
  - Parsing: 3.12ms
  - Validation: 12.45ms
  - Database: 87.23ms
======================================================================
```

---

## API Reference

### SingleCallGeminiResolver

#### Class Initialization

```python
from single_call_gemini_resolver import single_call_resolver

# Use global instance (recommended)
resolver = single_call_resolver

# Or create custom instance
from single_call_gemini_resolver import SingleCallGeminiResolver
resolver = SingleCallGeminiResolver(api_key="custom-key")
```

#### resolve_vehicle()

```python
result = resolver.resolve_vehicle(
    year: int,      # e.g., 2020
    make: str,      # e.g., "Toyota"
    model: str      # e.g., "Camry"
) -> VehicleResolution
```

**Returns:** `VehicleResolution` object with:

- `vehicle_key: str` - Unique identifier
- `year: int` - Input year
- `make: str` - Input make
- `model: str` - Input model
- `fields: Dict[str, Any]` - Resolved field data
- `run_id: str` - Unique run identifier
- `latency_ms: float` - Total resolution time
- `raw_response: Dict[str, Any]` - Original Gemini response

### Integration via vehicle_data.py

```python
from vehicle_data import process_vehicle

result = process_vehicle(
    year: int,
    make: str,
    model: str,
    progress_callback = None  # Optional callback function
) -> Dict[str, Any]
```

**Returns:** Dictionary with:

- `vehicle_key: str`
- `curb_weight_lbs: float` or `None`
- `aluminum_engine: bool` or `None`
- `aluminum_rims: bool` or `None`
- `catalytic_converters: int` or `None`
- `confidence_scores: Dict[str, float]`
- `source_attribution: Dict[str, str]`
- `citations: Dict[str, List[Dict]]`
- `warnings: List[str]`
- `missing_fields: Dict[str, str]`
- `timings: Dict[str, float]`
- `run_id: str`

---

## Comparison with Previous System

| Feature         | Previous (Multi-pass) | New (Single-call)         |
| --------------- | --------------------- | ------------------------- |
| API Calls       | 3-10+ per vehicle     | **1 per vehicle**         |
| Latency         | 10-30 seconds         | **3-8 seconds**           |
| Caching         | Complex cache layer   | **None**                  |
| Evidence        | Synthetic/assembled   | **Direct from grounding** |
| Code Complexity | ~2000 LOC             | **~400 LOC**              |
| Source Rules    | Implicit in logic     | **Explicit in prompt**    |

---

## Limitations

1. **No caching**: Every lookup hits API (by design for fresh data)
2. **Single attempt**: No retries or fallbacks
3. **Gemini-dependent**: Requires valid API key and quota
4. **English-only**: Optimized for English-language sources
5. **Rate limits**: Subject to Gemini API limits (15 req/min free tier)
6. **Sequential**: One vehicle at a time (no batching)

---

## Support & Resources

### Documentation

- This file: `DOCUMENTATION.md`
- Test script: `test_single_call_gemini.py`
- Examples: `example_usage_single_call.py`
- Code: `single_call_gemini_resolver.py`

### External Links

- **Gemini API Docs**: https://ai.google.dev/gemini-api/docs
- **Search Grounding**: https://ai.google.dev/gemini-api/docs/models/gemini-v2#search-tool
- **Get API Key**: https://aistudio.google.com/app/apikey
- **Python SDK**: https://googleapis.github.io/python-genai/

---

**System Version**: 1.0.0  
**Last Updated**: October 29, 2025  
**Status**: ✅ Production Ready
