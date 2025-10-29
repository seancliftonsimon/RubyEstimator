# Curb Weight Error Handling - Fix Summary

## Problem Diagnosed

The "Weight Not Found: Could not determine the curb weight. The result has been stored as 'Inconclusive' to prevent repeated searches." error was appearing in two distinct scenarios:

1. **API Failures (503 errors)**: When the Gemini API was overloaded or unavailable
2. **Data Not Found**: When the API succeeded but couldn't find curb weight data

Both scenarios resulted in the same generic error message, confusing users about the actual cause.

## Root Cause

In `app.py` (lines 2638-2682), the error handling logic had three branches:

```python
if vehicle_data is None:
    # Case 1: Vehicle doesn't exist
elif vehicle_data and vehicle_data['curb_weight_lbs']:
    # Case 2: Success - curb weight found
else:
    # Case 3: Caught BOTH API failures AND data not found
    # Showed generic "Weight Not Found" message
```

When either:

- API call failed (returning `curb_weight_lbs: None`)
- API succeeded but curb weight wasn't found (also `None`)

Both fell through to the `else` block, showing the same unhelpful error.

## Solutions Implemented

### 1. Enhanced Error Handling in `app.py`

**Added new condition for API errors:**

```python
elif 'error' in vehicle_data and vehicle_data['error']:
    # API call failed (503, timeout, etc.)
    st.error("Search Error: Unable to search for vehicle data")
    st.error(f"Error details: {error_msg}")
    st.info("Try again in a few moments or use Manual Entry")
```

**Improved "data not found" handling:**

```python
else:
    # API succeeded but curb weight not found
    st.warning("Curb Weight Not Found: Search completed but could not find reliable data")

    # Show partial results if available
    if has_partial_data:
        st.info("Found partial data:")
        # Display aluminum_engine, aluminum_rims, catalytic_converters if found

    st.info("Try a different model year or use Manual Entry")
```

### 2. Automatic Retry Logic in `single_call_gemini_resolver.py`

**Added exponential backoff retry for 503 errors:**

- Max 3 retry attempts
- Initial delay: 2 seconds
- Exponential backoff: 2s → 4s → 8s
- Only retries for: 503, rate limit, "overloaded", "unavailable" errors

```python
max_retries = 3
retry_delay = 2  # seconds

for attempt in range(max_retries):
    try:
        if attempt > 0:
            logger.info(f"Retry attempt {attempt + 1}/{max_retries}")
            time.sleep(retry_delay)
            retry_delay *= 2  # Exponential backoff

        response = self.client.models.generate_content(...)
        break  # Success
    except Exception as exc:
        if is_retryable and attempt < max_retries - 1:
            logger.warning(f"Retryable error: {exc}")
            continue  # Retry
        else:
            raise  # Non-retryable or last attempt
```

### 3. Improved Prompt Instructions

**Enhanced the Gemini prompt to be more explicit:**

- Clarified that ALL fields must be returned even when data isn't found
- Specified to set `value: null` and `status: "not_found"` for missing data
- Added instruction to never omit fields or return partial JSON

```
**CRITICAL INSTRUCTIONS:**
- ALWAYS return valid JSON for ALL 4 fields, even if data is not found
- If a field cannot be found, set status to "not_found" and value to null
- Never omit fields or return partial JSON
```

## User Experience Improvements

### Before

❌ Generic "Weight Not Found" for all failures
❌ No guidance on next steps
❌ No indication if it's an API issue or data issue
❌ Immediate failure on 503 errors

### After

✅ **API Failure**: Clear "Search Error" message with error details
✅ **Data Not Found**: Helpful "Curb Weight Not Found" with partial results shown
✅ **Actionable guidance**: "Try again in a few moments" or "Try different year"
✅ **Manual Entry suggestion**: Always points users to Manual Entry option
✅ **Automatic retries**: 503 errors retry up to 3 times with backoff

## Example Scenarios

### Scenario 1: API Overload (503)

**Before**: "Weight Not Found: Could not determine the curb weight..."

**After**:

```
❌ Search Error: Unable to search for vehicle data due to a temporary issue.
Error details: 503 UNAVAILABLE. The model is overloaded.

💡 What to do next:
- Try again in a few moments (API might be overloaded)
- Use the Manual Entry option below if you know the vehicle's curb weight
```

Plus: Automatic retry attempts logged in console

### Scenario 2: Data Not Found (API succeeded)

**Before**: "Weight Not Found: Could not determine the curb weight..."

**After**:

```
⚠️ Curb Weight Not Found: The search completed but could not find reliable curb weight data for this vehicle.

ℹ️ Found partial data:
✓ Aluminum Engine: true
✓ Aluminum Rims: true
✓ Cat Converters: 2

💡 What to do next:
- Try a different model year (curb weight data may be available for nearby years)
- Use the Manual Entry option below if you know the vehicle's curb weight
```

## Testing Recommendations

1. **Test API Failure**: Temporarily use invalid API key → should see "Search Error"
2. **Test Data Not Found**: Search for obscure vehicle → should see "Curb Weight Not Found"
3. **Test Partial Data**: Verify partial results display when available
4. **Test Retry Logic**: Monitor logs during 503 errors → should see retry attempts
5. **Test Success Case**: Common vehicle → should work normally

## Files Modified

- `app.py` - Enhanced error handling logic (lines 2638-2711)
- `single_call_gemini_resolver.py` - Added retry logic and improved prompt (lines 168-304)
- `CURB_WEIGHT_FIX_SUMMARY.md` - This documentation (new file)

## Next Steps

1. Test the application with various scenarios
2. Monitor logs for retry behavior during API overload
3. Gather user feedback on new error messages
4. Consider adding user-configurable retry settings in Admin UI


