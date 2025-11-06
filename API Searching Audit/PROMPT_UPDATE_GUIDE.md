# Prompt Update Guide

## Main File: `single_call_gemini_resolver.py`

This is the **primary file** responsible for:
- Building the prompts sent to Google Gemini API
- Making the API calls with Search Grounding
- Configuring the API settings (model, temperature, tools)

---

## Key Sections to Update

### 1. Prompt Building (Lines 173-195)

**Location**: `_build_prompt()` method

**Current Prompt Template**:
```python
def _build_prompt(self, year: int, make: str, model: str) -> str:
    """Build concise prompt optimized for speed."""
    return f"""Find specs for {year} {make} {model}. Return JSON ONLY.

FIND 4 FIELDS:
1. curb_weight (lbs, determine the most likely and sensible value based on available data - use base trim if identifiable, or most common value)
2. aluminum_engine (true/false, needs explicit "aluminum")
3. aluminum_rims (true/false, "aluminum" or "alloy")
4. catalytic_converters (count, integer, determine the most likely and sensible number)

SOURCES: Use any available sources (mark "oem" for manufacturer sites, "secondary" for others). Include URL + quote.

STATUS: "found" (has data), "not_found" (no data, value=null), "conflicting" (unclear, value=null)

IMPORTANT: If the vehicle does not appear to exist or cannot be verified, set status to "not_found" for all fields and return null values.

RETURN JSON:
{{
  "curb_weight": {{"value": 3310, "unit": "lbs", "status": "found", "citations": [{{"url": "...", "quote": "...", "source_type": "oem"}}]}},
  "aluminum_engine": {{"value": true, "status": "found", "citations": [...]}},
  "aluminum_rims": {{"value": true, "status": "found", "citations": [...]}},
  "catalytic_converters": {{"value": 2, "status": "found", "citations": [...]}}
}}"""
```

**What to Update Here**:
- Field definitions and instructions
- Source requirements (OEM vs secondary)
- JSON schema example
- Status handling instructions
- Any additional instructions for better results

---

### 2. API Configuration (Lines 239-247)

**Location**: Inside `resolve_vehicle()` method

**Current Configuration**:
```python
config = {
    "tools": [{"google_search": {}}],
    "temperature": 0,
    # Paid account optimizations:
    # - Higher limits allow more aggressive requests
    # - Faster model with experimental features
}
logger.info(f"Model: gemini-2.0-flash-exp")
logger.info(f"Config: {json.dumps(config, indent=2)}")
```

**What to Update Here**:
- Model name (currently `gemini-2.0-flash-exp`)
- Temperature setting (currently `0` for deterministic)
- Search Grounding tools configuration
- Any additional API parameters

---

### 3. API Call (Lines 261-265)

**Location**: Inside `resolve_vehicle()` method, inside retry loop

**Current API Call**:
```python
response = self.client.models.generate_content(
    model="gemini-2.0-flash-exp",  # Faster experimental model
    contents=prompt,
    config=config
)
```

**What to Update Here**:
- Model name (if different from config)
- Additional parameters to the API call
- Response handling

---

## Complete Method Flow

### `resolve_vehicle()` Method (Lines 197-404)

This is the main method that orchestrates everything:

1. **Lines 199-209**: Initialize and generate IDs
2. **Lines 211-222**: Check database cache
3. **Lines 224-231**: Build prompt (calls `_build_prompt()`)
4. **Lines 233-293**: Make API call with retry logic
5. **Lines 295-347**: Parse JSON response
6. **Lines 349-354**: Validate and normalize fields
7. **Lines 367-380**: Persist to database
8. **Lines 395-404**: Return results

---

## Quick Reference: What Each Section Does

| Section | Lines | Purpose |
|---------|-------|---------|
| `_build_prompt()` | 173-195 | Creates the prompt text sent to API |
| API Config | 239-247 | Sets up API parameters (model, tools, temperature) |
| API Call | 261-265 | Actually calls the Google Gemini API |
| Response Parsing | 295-347 | Parses and validates the JSON response |
| Validation | 349-354 | Normalizes and validates field values |
| Confidence Scoring | 595-622 | Calculates confidence scores based on sources |

---

## Example: How to Update the Prompt

### Current Prompt Structure:
```
Find specs for {year} {make} {model}. Return JSON ONLY.

FIND 4 FIELDS:
1. curb_weight (...)
2. aluminum_engine (...)
3. aluminum_rims (...)
4. catalytic_converters (...)

SOURCES: Use any available sources...
STATUS: "found" (has data)...
RETURN JSON: {...}
```

### Potential Improvements:

1. **Prioritize OEM Sources**:
   ```
   SOURCES: Prioritize manufacturer/OEM websites. Mark as "oem" for official manufacturer sites, "secondary" for others. Always include URL + quote.
   ```

2. **More Specific Field Instructions**:
   ```
   1. curb_weight (lbs, use base/entry-level trim weight if multiple trims exist, otherwise use most common value. Must be between 1,500-10,000 lbs)
   ```

3. **Better Conflict Resolution**:
   ```
   STATUS: "found" (has clear data), "not_found" (no data available), "conflicting" (sources disagree - if conflicting, prioritize OEM sources or use majority vote)
   ```

4. **Additional Context**:
   ```
   IMPORTANT: 
   - For curb_weight: Use base trim if identifiable, otherwise most common value
   - For aluminum_engine: Must explicitly mention "aluminum" in the source
   - For aluminum_rims: Accept "aluminum" or "alloy" as equivalent
   - For catalytic_converters: Count the actual number, typically 1-4 for most vehicles
   ```

---

## Testing Your Changes

After updating the prompt:

1. **Run Transparency Test**:
   ```bash
   python "API Searching Audit/transparency_test.py"
   ```

2. **Check the Output**:
   - Verify the new prompt is being sent correctly
   - Check if API responses improve
   - Review confidence scores and citations

3. **Compare Results**:
   - Use `PAST_EXAMPLES.md` as baseline
   - Run new examples and compare
   - Look for improvements in:
     - OEM source detection
     - Field accuracy
     - Citation quality
     - Confidence scores

---

## File Location

**Full Path**: `single_call_gemini_resolver.py` (in project root)

**Key Methods**:
- `_build_prompt()` - Lines 173-195
- `resolve_vehicle()` - Lines 197-404
- `_validate_and_normalize()` - Lines 406-509
- `_calculate_confidence()` - Lines 595-622

---

## Related Files

While `single_call_gemini_resolver.py` is the main file, these files also interact with it:

- **`vehicle_data.py`**: Calls the resolver and processes results for the UI
- **`persistence.py`**: Handles database schema (used by resolver)
- **`database_config.py`**: Database connection (used by resolver)

But for **prompt updates and API configuration**, you only need to modify `single_call_gemini_resolver.py`.

---

## Tips for Updating

1. **Keep it Concise**: Current prompt is ~1,150 characters. Longer prompts = slower API calls
2. **Be Explicit**: Clear instructions = better results
3. **Test Incrementally**: Make small changes and test each one
4. **Use Examples**: The JSON schema example helps guide the AI
5. **Prioritize OEM**: Add explicit instructions to find manufacturer sources first

---

## Next Steps

1. Open `single_call_gemini_resolver.py`
2. Navigate to line 173 (`_build_prompt()` method)
3. Update the prompt template as needed
4. Test with `transparency_test.py`
5. Compare results with `PAST_EXAMPLES.md`

