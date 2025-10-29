# Error Handling Quick Reference

## What Was Fixed

The generic "Weight Not Found" error has been replaced with specific, actionable error messages.

## New Error Messages

### 1. Search Error (API Failure)

**When you'll see it:** Gemini API is overloaded, down, or unreachable

```
❌ Search Error: Unable to search for vehicle data due to a temporary issue.
Error details: 503 UNAVAILABLE. The model is overloaded.

💡 What to do next:
- Try again in a few moments (API might be overloaded)
- Use the Manual Entry option below if you know the vehicle's curb weight
```

**What happens behind the scenes:**

- System automatically retries 3 times with delays (2s → 4s → 8s)
- Only if all retries fail, you'll see this error

### 2. Curb Weight Not Found (Data Missing)

**When you'll see it:** Search succeeded but couldn't find curb weight

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

**Note:** You'll see any data that WAS found (engine type, rims, converters)

### 3. Vehicle Not Found

**When you'll see it:** Vehicle doesn't exist or year is wrong

```
❌ Vehicle Not Found: 2025 Toyota Nonexistent does not appear to be a real vehicle or was not manufactured in this year. Please check your input.
```

### 4. Success

**When you'll see it:** Everything worked!

```
✅ Vehicle Found! 2016 Toyota Camry
```

## Automatic Retry Behavior

When the Gemini API returns temporary errors (503, rate limits, unavailable):

| Attempt | Delay Before | Total Wait |
| ------- | ------------ | ---------- |
| 1       | 0s           | 0s         |
| 2       | 2s           | 2s         |
| 3       | 4s           | 6s         |

**Total max wait:** ~6 seconds before giving up

**Retryable errors:**

- 503 Service Unavailable
- Rate limit exceeded
- Model overloaded
- API unavailable

**Non-retryable errors** (fail immediately):

- Invalid API key
- Malformed request
- Network errors

## User Actions

### If you see "Search Error"

1. **Wait 30-60 seconds** - API might be temporarily overloaded
2. **Try again** - Click search button again
3. **Use Manual Entry** - If you know the curb weight, enter it directly
4. **Check status** - Visit https://status.google.com/ for API status

### If you see "Curb Weight Not Found"

1. **Try nearby years** - E.g., if 2016 fails, try 2015 or 2017
2. **Check spelling** - Verify make/model names
3. **Use Manual Entry** - Look up curb weight on manufacturer website
4. **Check partial data** - Use any fields that WERE found

## Testing the Fixes

Run the test suite to verify everything works:

```bash
python test_error_handling.py
```

Expected output:

```
✓ API failure test passed
✓ Data not found test passed (with partial data)
✓ Success case test passed
✓ Retry logic test passed (succeeded on 3rd attempt)

✅ All tests passed!
```

## Log Messages

### Normal Operation

```
✓ Prompt built in 0.02ms
✓ API call completed in 1234.56ms
✓ JSON parsed in 0.01ms
✓ Validation completed in 0.15ms
✓ Database write completed in 23.45ms
✅ RESOLUTION COMPLETE
```

### With Retries

```
⚠️ Retryable error on attempt 1: 503 UNAVAILABLE. The model is overloaded.
🔄 Retry attempt 2/3 after 2s delay...
⚠️ Retryable error on attempt 2: 503 UNAVAILABLE. The model is overloaded.
🔄 Retry attempt 3/3 after 4s delay...
✓ API call completed in 6008.97ms
```

## Configuration

Want to adjust retry behavior? Edit `single_call_gemini_resolver.py`:

```python
# Line ~261
max_retries = 3       # Change number of attempts
retry_delay = 2       # Change initial delay (seconds)
```

## Support

If you continue seeing errors after these fixes:

1. Check `CURB_WEIGHT_FIX_SUMMARY.md` for detailed technical info
2. Review application logs for detailed error messages
3. Verify API key is valid in `.streamlit/secrets.toml`
4. Check internet connectivity and firewall settings
