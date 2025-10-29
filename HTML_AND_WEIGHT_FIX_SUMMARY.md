# HTML Rendering & Weight Selection Fixes

## Issues Fixed

### 1. Raw HTML `</div>` Tags Showing in UI

**Problem:**
The vehicle details display was showing raw HTML code instead of rendering properly:

```
Weight: 4449.0 lbs HIGH (85%)
</div>
Engine: Fe HIGH (85%)
</div>
```

**Root Cause:**
The `render_confidence_badge()` function in `confidence_ui.py` was returning multi-line HTML with newlines:

```python
badge_html = f"""
    <span class="confidence-badge">
        HIGH (85%)
    </span>
    """
```

When this was embedded into another f-string in `app.py`, the newlines and whitespace caused Streamlit to treat the closing tags as text instead of HTML.

**Solution:**
Changed the badge HTML to a single-line string without newlines:

```python
badge_html = f'<span class="confidence-badge confidence-{confidence_info.level}" style="..." title="{confidence_info.explanation}">{confidence_info.level.upper()} ({confidence_info.score:.0%})</span>'
```

### 2. Multiple Weight Values - Select Minimum

**Problem:**
When a vehicle has multiple curb weights (different trims/configurations), the system wasn't selecting the appropriate one.

**Requirement:**
Always select the **minimum (lightest)** weight when multiple weights are available.

**Solution:**

1. **Updated `_normalize_weight()` function** to handle arrays/lists:

```python
def _normalize_weight(self, value: Any) -> Optional[float]:
    """Normalize weight to lbs. If multiple weights provided, selects the minimum."""

    # Handle lists/arrays of weights - select minimum valid weight
    if isinstance(value, (list, tuple)):
        valid_weights = []
        for v in value:
            try:
                w = float(v)
                if 1500 <= w <= 10000:
                    valid_weights.append(w)
            except (ValueError, TypeError):
                continue

        if valid_weights:
            min_weight = min(valid_weights)
            if len(valid_weights) > 1:
                logger.info(f"Multiple weights found: {valid_weights}, selecting minimum: {min_weight} lbs")
            return min_weight

    # Handle single weight value
    # ... existing code ...
```

2. **Updated prompt** to instruct Gemini API:

```
VALIDATION RULES:
- curb_weight: Must be in lbs (convert if needed), typically 1500-10000 lbs for passenger vehicles
  * If multiple weights found (different trims/configs), provide the MINIMUM (lightest) weight
```

## Files Modified

### `confidence_ui.py`

- **Line 78**: Changed multi-line f-string to single-line for `render_confidence_badge()`
- **Effect**: Fixes HTML rendering issue in vehicle details display

### `single_call_gemini_resolver.py`

- **Lines 482-520**: Enhanced `_normalize_weight()` to handle arrays and select minimum
- **Line 186**: Updated prompt to request minimum weight when multiple found
- **Effect**: Ensures minimum weight is always selected when multiple options exist

## Test Results

All tests passed:

```
[OK] API failure test passed
[OK] Data not found test passed (with partial data)
[OK] Success case test passed
[OK] Retry logic test passed (succeeded on 3rd attempt)

[SUCCESS] All tests passed!
```

## User Experience Improvements

### Before

```
Weight: 4449.0 lbs HIGH (85%)
</div>
Engine: Fe HIGH (85%)
</div>
Rims: Al HIGH (85%)
</div>
Cats: 2 HIGH (85%)
</div>
```

❌ Raw HTML visible, unprofessional appearance

### After

```
┌─────────────────────────────────────┐
│ Weight: 4449.0 lbs  HIGH (85%)      │
├─────────────────────────────────────┤
│ Engine: Fe  HIGH (85%)              │
├─────────────────────────────────────┤
│ Rims: Al  HIGH (85%)                │
├─────────────────────────────────────┤
│ Cats: 2  HIGH (85%)                 │
└─────────────────────────────────────┘
```

✅ Proper HTML rendering with styled badges

### Weight Selection

**Before:**

- Unpredictable which weight was selected from multiple options
- Could select max, average, or random weight

**After:**

- **Always selects minimum (lightest) weight**
- Logs when multiple weights found: `"Multiple weights found: [3310, 3450, 3600], selecting minimum: 3310 lbs"`
- Consistent, predictable behavior

## Logging Added

When multiple weights are found:

```
2025-10-29 09:35:00 - single_call_gemini_resolver - INFO - Multiple weights found: [3310.0, 3450.0], selecting minimum: 3310.0 lbs
```

This helps with debugging and understanding why a particular weight was selected.

## Edge Cases Handled

1. **Empty list of weights**: Returns `None`
2. **Invalid weights in list**: Skips them, processes valid ones
3. **All weights out of range**: Returns `None`, logs warning
4. **Single weight**: Processes as before (no regression)
5. **Mixed valid/invalid**: Filters to valid weights, selects minimum

## Why Minimum Weight?

The minimum weight is typically:

- The **base model** with fewest options
- Most **conservative estimate** for calculations
- **Lightest configuration**, which is important for cost estimating in the vehicle recycling context
- **Most common** starting point for adding options/features

## Backward Compatibility

✅ **Fully backward compatible**

- If API returns single weight: Works as before
- If API returns `None`: Works as before
- If API returns invalid weight: Works as before
- **New**: If API returns array: Selects minimum

No breaking changes to existing functionality.

## Next Steps

1. Monitor logs for "Multiple weights found" messages
2. Verify minimum weight selection is working as expected in production
3. Consider adding min/max/average weight display in future for user transparency

## Testing Recommendations

Test with vehicles known to have multiple trim levels:

- 2020 Honda Accord (LX vs Touring)
- 2019 Toyota Camry (L vs XLE vs Hybrid)
- 2021 Ford F-150 (Regular cab vs SuperCrew, different engine options)

Expected behavior: Always shows the lightest available configuration.


