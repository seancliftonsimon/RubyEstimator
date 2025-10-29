# 🔍 Neon Database Logging Guide

## Overview

Comprehensive logging has been added to track all database operations with your Neon PostgreSQL database (or SQLite fallback). The logs will help you verify that:

1. ✅ The correct database URL is being used
2. ✅ Database connections are successful
3. ✅ Tables are being created/validated
4. ✅ Vehicle data is being read from cache
5. ✅ New vehicle data is being written to the database

---

## 📊 What Was Added

### 1. **database_config.py** - Connection & Engine Logging

**New Logging:**
- 🔗 Database URL detection (shows which connection string is being used)
- ⚙️  Database engine creation
- 📡 Connection test attempts and results
- 🔒 Password masking for security (passwords shown as `****`)

**Example Logs:**
```
🔗 Using DATABASE_URL: postgresql://user:****@ep-cool-name.us-east-2.aws.neon.tech/neondb
⚙️  Creating database engine for PostgreSQL (Neon)
✓ Database engine created successfully
🔍 Testing database connection...
📡 Attempting to connect to database...
✓ Database connection test successful! Query returned: (1,)
```

---

### 2. **persistence.py** - Schema Management Logging

**New Logging:**
- 📋 Schema validation/creation start
- 🗄️  Database type detection (PostgreSQL vs SQLite)
- ✓ Individual table creation confirmations
- 💾 Transaction commit status

**Example Logs:**
```
📋 Ensuring database schema exists...
🗄️  Creating schema for PostgreSQL database
  ✓ vehicles table ready
  ✓ field_values table ready
  ✓ runs table ready
  ✓ evidence table ready
✓ PostgreSQL (Neon) schema validated/created successfully
✓ Schema commit completed
```

---

### 3. **single_call_gemini_resolver.py** - Data Read/Write Logging

**New Logging for READS (Cache Lookups):**
- 🔍 Cache lookup attempts
- 📖 Reading from specific tables (`vehicles`, `field_values`)
- ✓ Successful cache hits
- ❌ Cache misses (will fetch fresh data)

**Example Read Logs:**
```
🔍 Checking database cache for vehicle_key: 2015_honda_civic
📖 Reading from 'vehicles' table for key: 2015_honda_civic
✓ Found cached vehicle: 2015 Honda Civic (last updated: 2025-10-29 12:34:56)
📖 Reading from 'field_values' table for key: 2015_honda_civic
✓ Retrieved 4 field values from cache
✅ Successfully loaded complete vehicle data from cache for 2015 Honda Civic
```

**New Logging for WRITES (Persisting New Data):**
- 💾 Data persistence start
- ✍️  Writing to specific tables (`runs`, `vehicles`, `field_values`, `evidence`)
- 📝 Individual field details
- ✅ Successful completion with summary

**Example Write Logs:**
```
💾 Persisting to database: 2020 Toyota Camry (vehicle_key=2020_toyota_camry, run_id=abc123...)
✍️  Writing to 'runs' table: run_id=abc123, latency=2456.78ms
  ✓ Run record inserted into 'runs' table
✍️  Writing to 'vehicles' table: 2020 Toyota Camry
  ✓ Vehicle record upserted into 'vehicles' table
  ✍️  Writing 4 field values to 'field_values' table...
    • curb_weight: 3310 (status=found, confidence=0.85)
    • aluminum_engine: True (status=found, confidence=0.9)
    • aluminum_rims: True (status=found, confidence=0.8)
    • catalytic_converters: 1 (status=found, confidence=0.85)
  ✓ All field values written to 'field_values' table
  ✍️  Writing 8 citation(s) to 'evidence' table for field 'curb_weight'
💾 Committing transaction to database...
✅ Database write complete! Successfully persisted 2020 Toyota Camry with 4 fields
  Total evidence citations stored: 24
```

---

## 🧪 Testing the Logging

### Option 1: Run the Test Script

A dedicated test script has been created to verify all logging functionality:

```bash
python test_database_logging.py
```

This will:
1. Test database connection
2. Test schema creation
3. Test database reads (cache lookups)
4. Test database writes (new data)

**Look for these emojis in the output:**
- 🔗 = Database URL/connection info
- ⚙️  = Engine creation
- 📋 = Schema operations
- 🔍 = Cache lookups (READ)
- 💾 = Data persistence (WRITE)
- ✓/✅ = Success
- ❌ = Errors

---

### Option 2: Run Your Streamlit App

Start your app normally:

```bash
streamlit run app.py
```

Then **check the terminal/console output** (not the browser) for the detailed logs. Every time you:
- Start the app → See database connection and schema logs
- Search for a vehicle → See cache lookup logs
- Process a new vehicle → See database write logs

---

## 🔧 Viewing Logs in Production (Streamlit Cloud)

When deployed to Streamlit Cloud:

1. Go to your app's dashboard on https://share.streamlit.io
2. Click on your app
3. Click **"Manage app"** 
4. Click **"Logs"** tab
5. All the database logging will appear here in real-time

---

## 📝 Log Levels

The logging uses different levels:

- **INFO** - Key operations (connections, reads, writes, successes)
- **DEBUG** - Detailed operations (individual field writes, SQL queries)
- **WARNING** - Non-critical issues (cache misses, incomplete data)
- **ERROR** - Critical failures (connection failures, exceptions)

Current configuration shows **INFO and above** by default. To see DEBUG logs, change this in `app.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    ...
)
```

---

## 🎯 What to Look For

### ✅ Signs Everything is Working with Neon:

1. **Database URL shows Neon:**
   ```
   🔗 Using DATABASE_URL: postgresql://user:****@ep-*.neon.tech/neondb
   ```

2. **PostgreSQL-specific features:**
   ```
   Creating PostgreSQL tables (if not exist) with JSONB support...
   ```

3. **Successful connections:**
   ```
   ✓ Database connection test successful!
   ```

4. **Data being written:**
   ```
   ✅ Database write complete! Successfully persisted...
   ```

### ⚠️ Signs There Might Be Issues:

1. **Falls back to SQLite:**
   ```
   🔗 Using SQLite database: C:\...\rubyestimator_local.db
   ```
   → Your DATABASE_URL environment variable may not be set

2. **Connection failures:**
   ```
   ❌ Database connection test failed: ...
   ```
   → Check your Neon connection string

3. **Schema creation errors:**
   ```
   ❌ Failed to create database engine: ...
   ```
   → Neon database may be unreachable

---

## 🔒 Security Note

Passwords in database URLs are automatically masked in logs:
```
postgresql://user:****@host/db
```

Your actual password is never written to the logs for security.

---

## 💡 Tips

1. **First run** will show more logs (schema creation)
2. **Subsequent runs** with cached data will show cache hit logs
3. **New vehicle lookups** will show full write operation logs
4. **Keep the terminal visible** when running locally to see all logs
5. **In production**, always check the Streamlit Cloud logs dashboard

---

## 📞 Troubleshooting

**Q: I don't see any database logs**
- Check that logging is configured in `app.py` (it should be)
- Make sure you're looking at the terminal/console, not the browser
- Try running `python test_database_logging.py` directly

**Q: Logs show SQLite instead of Neon**
- Your `DATABASE_URL` environment variable isn't set
- Check `.env` file locally or Streamlit secrets in production
- Run `python -c "import os; print(os.getenv('DATABASE_URL'))"`

**Q: Too many logs / too verbose**
- Change `level=logging.INFO` to only show important logs
- Use `level=logging.WARNING` to only show warnings/errors
- Use `level=logging.DEBUG` to see everything (useful for troubleshooting)

---

## 📚 Related Files

- `database_config.py` - Connection management
- `persistence.py` - Schema management  
- `single_call_gemini_resolver.py` - Data caching and persistence
- `vehicle_data.py` - High-level vehicle processing
- `test_database_logging.py` - Logging verification script

---

## ✅ Summary

You now have comprehensive logging for:
- ✅ Database connection attempts
- ✅ Database type detection (Neon vs SQLite)
- ✅ Schema creation/validation
- ✅ Cache lookups (read operations)
- ✅ Data persistence (write operations)
- ✅ Success/failure indicators
- ✅ Detailed operation tracking

Run the test script or your app and watch the logs to verify everything is working with your Neon database!

