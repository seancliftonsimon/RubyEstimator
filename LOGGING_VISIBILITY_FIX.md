# Logging Visibility Fix

## Problem

After launching the Streamlit app, no logs were visible in the terminal/console.

## Root Cause

Streamlit can suppress or redirect logging output depending on how it's started and the environment.

## Solution Implemented

### 1. Force Logging Configuration

Updated **three key files** to explicitly configure logging with `force=True` and direct stdout output:

#### `app.py` (lines 3-13, 19-21, 36, 43)

```python
import logging
import sys

# Configure logging FIRST (before any other imports)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)
logger = logging.getLogger(__name__)

# Log startup
logger.info("="*70)
logger.info("🚀 Ruby GEM Application Starting...")
logger.info("="*70)
```

#### `single_call_gemini_resolver.py` (lines 20-30)

```python
import sys
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Force output to stdout
    ],
    force=True  # Override any existing configuration
)
logger = logging.getLogger(__name__)
```

#### `vehicle_data.py` (lines 17-26)

```python
import sys
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    force=True
)
logger = logging.getLogger(__name__)
```

## How to See Logs

### Option 1: Run Streamlit Normally (Recommended)

```powershell
streamlit run app.py
```

You should now see:

```
======================================================================
🚀 Ruby GEM Application Starting...
======================================================================
✓ Streamlit page configured
✓ Core modules imported
✓ API key loaded from Streamlit secrets
✓ Gemini client initialized successfully
✅ Database connection successful
```

### Option 2: Redirect to File (For Analysis)

```powershell
streamlit run app.py 2>&1 | Tee-Object -FilePath logs.txt
```

This shows logs in console AND saves them to `logs.txt`.

### Option 3: File Only (Background)

```powershell
streamlit run app.py > logs.txt 2>&1
```

Then monitor the file:

```powershell
Get-Content logs.txt -Wait -Tail 50
```

### Option 4: Enable DEBUG Level

For maximum detail:

```powershell
# Windows PowerShell
$env:LOG_LEVEL = "DEBUG"
streamlit run app.py
```

Or edit `app.py` line 8:

```python
level=logging.DEBUG,  # Change from INFO to DEBUG
```

## What You Should See

### On Startup

```
======================================================================
🚀 Ruby GEM Application Starting...
======================================================================
2025-10-29 09:38:30 - single_call_gemini_resolver - INFO - ✓ API key loaded from Streamlit secrets
2025-10-29 09:38:30 - single_call_gemini_resolver - INFO - Initializing Gemini client...
2025-10-29 09:38:31 - single_call_gemini_resolver - INFO - ✓ Gemini client initialized successfully
2025-10-29 09:38:31 - app - INFO - ✓ Streamlit page configured
2025-10-29 09:38:31 - app - INFO - ✓ Core modules imported
✅ Database connection successful
```

### During Vehicle Search

```
2025-10-29 09:40:15 - vehicle_data - INFO - 🔍 Processing vehicle request: 2016 Toyota Camry
======================================================================
🚗 RESOLVING: 2016 Toyota Camry
======================================================================
Vehicle Key: 2016_toyota_camry
Run ID: abc123def456

📝 Building prompt...
✓ Prompt built in 0.02ms
Prompt length: 2401 characters

🌐 Calling Gemini API with Search Grounding...
Model: gemini-2.5-flash
✓ API call completed in 1234.56ms

📦 Parsing JSON response...
✓ JSON parsed in 0.50ms
Fields in response: ['curb_weight', 'aluminum_engine', 'aluminum_rims', 'catalytic_converters']

✅ Validating and normalizing fields...
✓ Validation completed in 0.15ms
  • curb_weight: 3310.0 (status=found, confidence=0.95, citations=1)
  • aluminum_engine: True (status=found, confidence=0.95, citations=1)
  • aluminum_rims: True (status=found, confidence=0.95, citations=1)
  • catalytic_converters: 2 (status=found, confidence=0.85, citations=1)

💾 Persisting to database...
✓ Database write completed in 23.45ms

======================================================================
✅ RESOLUTION COMPLETE
Total Time: 1234.56ms (1.23s)
  - Prompt: 0.02ms
  - API Call: 1200.00ms (97.2%)
  - Parsing: 0.50ms
  - Validation: 0.15ms
  - Database: 23.45ms
======================================================================

2025-10-29 09:40:16 - vehicle_data - INFO - ✓ All fields found for 2016 Toyota Camry
2025-10-29 09:40:16 - vehicle_data - INFO - ✓ Returning output for 2016 Toyota Camry (run_id: abc123def456)
```

### With Multiple Weights

```
2025-10-29 09:42:30 - single_call_gemini_resolver - INFO - Multiple weights found: [3310.0, 3450.0, 3600.0], selecting minimum: 3310.0 lbs
```

### With Errors/Retries

```
⚠️ Retryable error on attempt 1: 503 UNAVAILABLE. The model is overloaded.
🔄 Retry attempt 2/3 after 2s delay...
⚠️ Retryable error on attempt 2: 503 UNAVAILABLE. The model is overloaded.
🔄 Retry attempt 3/3 after 4s delay...
✓ API call completed in 6008.97ms
```

## Troubleshooting

### Still No Logs?

1. **Check Terminal Type**

   - Use PowerShell or CMD (not Git Bash)
   - Windows Terminal recommended

2. **Verify Python Version**

   ```powershell
   python --version
   ```

   Should be 3.8+

3. **Check if Streamlit is Running**

   ```powershell
   Get-Process | Where-Object {$_.ProcessName -like "*streamlit*"}
   ```

4. **Test Logging Directly**

   ```powershell
   python test_logging.py
   ```

   Should show logs immediately.

5. **Clear Streamlit Cache**

   ```powershell
   streamlit cache clear
   streamlit run app.py
   ```

6. **Try Verbose Mode**
   ```powershell
   streamlit run app.py --logger.level=debug
   ```

### Logs Only Show Streamlit Messages?

If you only see Streamlit's own messages (like "You can now view your Streamlit app...") but not our custom logs:

1. **Ensure `force=True` is set** in all three logging.basicConfig() calls
2. **Check import order** - logging must be configured BEFORE imports
3. **Restart Streamlit completely** - Ctrl+C and restart

### Want More Detail?

Change line 8 in `app.py`:

```python
level=logging.DEBUG,  # Was: logging.INFO
```

This shows ALL operations including:

- Raw API responses
- JSON parsing details
- Database operations
- Field normalization steps

## Log Levels Reference

| Level       | What It Shows                          | When to Use                  |
| ----------- | -------------------------------------- | ---------------------------- |
| **DEBUG**   | Everything - raw data, parsing, DB ops | Development, troubleshooting |
| **INFO**    | Key operations and results             | Normal operation (default)   |
| **WARNING** | Issues that don't stop operation       | Production monitoring        |
| **ERROR**   | Failures and exceptions                | Production alerts            |

## Test Files

Two test files were created to verify logging:

### `test_logging.py`

Quick test of logging configuration:

```powershell
python test_logging.py
```

Should output:

```
2025-10-29 09:38:28 - __main__ - INFO - INFO: This is an info message
2025-10-29 09:38:28 - __main__ - WARNING - WARNING: This is a warning message
2025-10-29 09:38:28 - __main__ - ERROR - ERROR: This is an error message
2025-10-29 09:38:31 - vehicle_data - INFO - ✓ Vehicle data logger working
2025-10-29 09:38:31 - single_call_gemini_resolver - INFO - ✓ Resolver logger working
```

### `test_error_handling.py`

Full integration test with logging:

```powershell
python test_error_handling.py
```

## Files Modified

1. **app.py** - Added logging configuration at startup
2. **single_call_gemini_resolver.py** - Enhanced with forced stdout
3. **vehicle_data.py** - Enhanced with forced stdout
4. **test_logging.py** - New test file
5. **LOGGING_VISIBILITY_FIX.md** - This documentation

## Key Improvements

✅ **Forced stdout**: `handlers=[logging.StreamHandler(sys.stdout)]`
✅ **Override existing config**: `force=True`
✅ **Early configuration**: Logging set up BEFORE any other imports
✅ **Consistent format**: All modules use same format
✅ **Startup messages**: Clear indicators when app launches
✅ **Test scripts**: Verify logging works independently

## Next Steps

1. **Launch the app**: `streamlit run app.py`
2. **Verify startup logs** appear in console
3. **Test a vehicle search** to see detailed logs
4. **Adjust log level** if needed (INFO vs DEBUG)

You should now have full visibility into everything the application is doing!
