# Logging Guide - Comprehensive Diagnostics

## Overview

The system now includes extensive logging at multiple levels to help diagnose issues. All logs are written to the console and can be captured for analysis.

## Logging Levels

The system uses Python's standard logging levels:

| Level     | When to Use                           | What You'll See                                              |
| --------- | ------------------------------------- | ------------------------------------------------------------ |
| `DEBUG`   | Development, detailed troubleshooting | All internal operations, data transformations, DB operations |
| `INFO`    | Normal operation, monitoring          | Key events, successful operations, progress updates          |
| `WARNING` | Potential issues                      | Data validation failures, retries, missing optional data     |
| `ERROR`   | Failures                              | API errors, parsing failures, exceptions                     |

**Default Level**: `INFO` (shows important events without overwhelming detail)

## Configuring Log Level

### Option 1: Environment Variable (Recommended)

Set before running the app:

```bash
# Windows PowerShell
$env:LOG_LEVEL = "DEBUG"
streamlit run app.py

# Windows CMD
set LOG_LEVEL=DEBUG
streamlit run app.py

# Linux/Mac
export LOG_LEVEL=DEBUG
streamlit run app.py
```

### Option 2: Modify Code Directly

Edit the top of `single_call_gemini_resolver.py`:

```python
# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG, INFO, WARNING, or ERROR
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

And `vehicle_data.py`:

```python
# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Change level here
```

## What Gets Logged

### 1. Vehicle Resolution Process (`vehicle_data.py`)

**INFO Level:**

```
🔍 Processing vehicle request: 2016 Toyota Camry
✓ Vehicle resolution completed successfully for 2016 Toyota Camry
✓ All fields found for 2016 Toyota Camry
✓ Returning output for 2016 Toyota Camry (run_id: abc123)
```

**DEBUG Level:**

```
Resolution run_id: abc123, latency: 1234.56ms
Field 'curb_weight': status=found, value=3310, confidence=0.95
Field 'aluminum_engine': status=found, value=True, confidence=0.95
Citation counts: {'curb_weight': 1, 'aluminum_engine': 1, ...}
```

**WARNING Level:**

```
⚠️ Missing fields for 2016 Toyota Camry: ['catalytic_converters']
```

**ERROR Level:**

```
❌ Vehicle resolution failed for 2016 Toyota Camry: 503 UNAVAILABLE
[Full stack trace included]
```

### 2. Gemini API Calls (`single_call_gemini_resolver.py`)

**INFO Level:**

```
======================================================================
🚗 RESOLVING: 2016 Toyota Camry
======================================================================
Vehicle Key: 2016_toyota_camry
Run ID: abc123
✓ Prompt built in 0.02ms
🌐 Calling Gemini API with Search Grounding...
Model: gemini-2.5-flash
✓ API call completed in 1234.56ms
```

**With Retries:**

```
⚠️ Retryable error on attempt 1: 503 UNAVAILABLE. The model is overloaded.
🔄 Retry attempt 2/3 after 2s delay...
⚠️ Retryable error on attempt 2: 503 UNAVAILABLE. The model is overloaded.
🔄 Retry attempt 3/3 after 4s delay...
✓ API call completed in 6008.97ms
```

**ERROR Level:**

```
❌ API call failed after 1234.56ms: 503 UNAVAILABLE
❌ All 3 retry attempts failed
```

### 3. JSON Response Parsing

**INFO Level:**

```
📦 Parsing JSON response...
Response text length: 1234 characters
✓ JSON parsed in 0.50ms
Fields in response: ['curb_weight', 'aluminum_engine', 'aluminum_rims', 'catalytic_converters']
```

**DEBUG Level:**

````
Raw response (first 1000 chars):
{"curb_weight": {"value": 3310, ...}}
Stripped ```json markdown wrapper
✓ Removed markdown code block wrappers
curb_weight: status=found, value=3310
aluminum_engine: status=found, value=True
````

**WARNING Level:**

```
⚠️ Field 'catalytic_converters' missing from response!
```

**ERROR Level:**

```
❌ JSON parsing failed after 0.50ms: Expecting ',' delimiter: line 2 column 4 (char 45)
JSON error position: line 2, column 4
Response text (cleaned, first 500 chars): ...
Full response text length: 1234 characters
```

### 4. Field Validation & Normalization

**DEBUG Level:**

```
Starting field validation and normalization...
curb_weight: normalized 3310.5 -> 3310.0
✓ Field validation and normalization complete
```

**WARNING Level:**

```
⚠️ Weight 500 lbs outside valid range (1500-10000), rejecting
⚠️ Failed to normalize weight value 'invalid': could not convert string to float
⚠️ Count 15 outside valid range (0-10), rejecting
⚠️ Unrecognized boolean string value: 'maybe'
⚠️ Invalid boolean type: dict
```

### 5. Database Operations

**DEBUG Level:**

```
Persisting to database: vehicle_key=2016_toyota_camry, run_id=abc123
Inserting run record: abc123, latency=1234.56ms
✓ Run record inserted
Upserting vehicle record: 2016 Toyota Camry
✓ Vehicle record upserted
Inserting 4 field values...
  Upserting field 'curb_weight': value=3310.0, status=found
  Inserting 1 citation(s) for 'curb_weight'
Committing transaction...
✓ Database transaction committed successfully
```

### 6. Performance Metrics (Always Shown)

```
✅ RESOLUTION COMPLETE
Total Time: 1234.56ms (1.23s)
  - Prompt: 0.02ms
  - API Call: 1200.00ms (97.2%)
  - Parsing: 0.50ms
  - Validation: 0.15ms
  - Database: 23.45ms
```

## Capturing Logs to File

### Method 1: Redirect Console Output

```bash
# Capture both stdout and stderr
streamlit run app.py > logs.txt 2>&1

# Or append to existing log file
streamlit run app.py >> logs.txt 2>&1
```

### Method 2: Add File Handler (Code Modification)

Add to `single_call_gemini_resolver.py` after the `logging.basicConfig()` call:

```python
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add file handler
file_handler = logging.FileHandler('ruby_estimator.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logging.getLogger().addHandler(file_handler)
```

## Common Diagnostic Scenarios

### Scenario 1: Vehicle Search Fails

**Enable DEBUG level and look for:**

1. **API Request Details:**

   - Was the prompt correct?
   - Did the API call complete?
   - How many retries occurred?

2. **Response Issues:**

   - Was JSON valid?
   - Were all fields present in response?
   - Did any fields fail validation?

3. **Data Issues:**
   - Which fields had status "not_found"?
   - Were values outside valid ranges?

**Key Log Lines:**

```
🚗 RESOLVING: [your vehicle]
✓ Prompt built in X ms
Prompt length: X characters
🌐 Calling Gemini API...
✓ API call completed in X ms
Field 'curb_weight': status=not_found, value=None
```

### Scenario 2: Curb Weight Not Found

**Look for:**

1. **API Response:**

   ```
   curb_weight: status=not_found, value=None
   ```

2. **Validation Issues:**

   ```
   ⚠️ Weight X lbs outside valid range (1500-10000), rejecting
   ```

3. **Missing Citations:**
   ```
   Citation counts: {'curb_weight': 0, ...}
   ```

### Scenario 3: API Overload (503 Errors)

**Look for:**

```
⚠️ Retryable error on attempt 1: 503 UNAVAILABLE
🔄 Retry attempt 2/3 after 2s delay...
⚠️ Retryable error on attempt 2: 503 UNAVAILABLE
🔄 Retry attempt 3/3 after 4s delay...
```

**If succeeds:**

```
✓ API call completed in 6008.97ms
```

**If all retries fail:**

```
❌ All 3 retry attempts failed
❌ Vehicle resolution failed for [vehicle]: Gemini API call failed after 3 attempts
```

### Scenario 4: Database Issues

**Look for:**

```
Persisting to database: vehicle_key=X, run_id=X
✓ Run record inserted
✓ Vehicle record upserted
✓ Database transaction committed successfully
```

**If fails, you'll see SQLAlchemy errors with stack traces**

## Log Analysis Tips

### 1. Filter by Vehicle

```bash
# Linux/Mac
grep "2016 Toyota Camry" logs.txt

# Windows PowerShell
Select-String -Path logs.txt -Pattern "2016 Toyota Camry"
```

### 2. Filter by Run ID

Every resolution has a unique `run_id`. Track all operations for a single run:

```bash
# Find the run_id first
grep "Run ID:" logs.txt

# Then filter by that ID
grep "abc123" logs.txt
```

### 3. Find Errors Only

```bash
# Linux/Mac
grep "ERROR" logs.txt

# Windows PowerShell
Select-String -Path logs.txt -Pattern "ERROR"
```

### 4. Find Warnings

```bash
# Linux/Mac
grep "WARNING" logs.txt

# Windows PowerShell
Select-String -Path logs.txt -Pattern "WARNING"
```

### 5. Track API Performance

```bash
# Find API call times
grep "API call completed" logs.txt

# Find retries
grep "Retry attempt" logs.txt
```

## Performance Monitoring

### Normal Operation Benchmarks

- **Prompt Building**: < 1ms
- **API Call (no search)**: 500-1500ms
- **API Call (with search)**: 1500-5000ms
- **JSON Parsing**: < 5ms
- **Validation**: < 1ms
- **Database Write**: 10-50ms

### Performance Issues

**If API calls take > 10 seconds:**

- Check network connectivity
- Verify API key is valid
- Check if Gemini API is experiencing issues

**If retries are frequent:**

- API might be overloaded (normal during peak hours)
- Consider rate limiting your requests
- Wait a few minutes between batches

**If database writes take > 1 second:**

- Check database file size (SQLite)
- Consider database maintenance (VACUUM)
- Check disk I/O performance

## Troubleshooting Checklist

When diagnosing an issue:

1. ✅ **Enable DEBUG logging**
2. ✅ **Capture logs to file**
3. ✅ **Note the run_id from the logs**
4. ✅ **Check API call status** (success/fail/retry)
5. ✅ **Check JSON parsing** (valid/invalid)
6. ✅ **Check field statuses** (found/not_found/conflicting)
7. ✅ **Check validation warnings** (out of range, type errors)
8. ✅ **Check database commit** (success/fail)
9. ✅ **Review performance metrics** (bottlenecks)
10. ✅ **Search logs for specific run_id** (complete trace)

## Support Information

When reporting issues, include:

1. **Log Level Used**: DEBUG/INFO
2. **Run ID**: From logs (unique per resolution)
3. **Vehicle**: Year, Make, Model
4. **Relevant Log Excerpts**: Full error messages with timestamps
5. **Performance Metrics**: From "RESOLUTION COMPLETE" section
6. **Environment**: Windows/Linux, Python version, Streamlit version

Example support snippet:

```
Run ID: abc123def456
Vehicle: 2016 Toyota Camry
Issue: Curb weight not found despite API success

Relevant logs:
2025-10-29 09:11:26 - single_call_gemini_resolver - INFO - ✓ API call completed in 1234.56ms
2025-10-29 09:11:26 - single_call_gemini_resolver - DEBUG - Field 'curb_weight': status=not_found, value=None
2025-10-29 09:11:26 - vehicle_data - WARNING - ⚠️ Missing fields for 2016 Toyota Camry: ['curb_weight']
```

This provides everything needed to diagnose the issue!


