# Railway Secrets Fix Guide

## Problem

You're getting this error on Railway:

```
No secrets files found. Valid paths for a secrets.toml file are: /root/.streamlit/secrets.toml, /app/.streamlit/secrets.toml
```

## Solution

The issue has been fixed by:

1. **Created `.streamlit/secrets.toml`** - A minimal secrets file that prevents the error
2. **Updated error handling** - The app now gracefully handles missing secrets
3. **Added startup script** - `railway_startup.py` checks environment variables before starting

## Railway Environment Variables

Make sure to set these environment variables in your Railway project:

### Required for Database

- `DATABASE_URL` - Your PostgreSQL connection string
- OR individual variables:
  - `PGHOST`
  - `PGPORT` (default: 5432)
  - `PGDATABASE`
  - `PGUSER`
  - `PGPASSWORD`

### Optional

- `GEMINI_API_KEY` - For vehicle search functionality
- `PASSWORD_HASH` - For password protection (SHA-256 hash of your password)

## How to Set Environment Variables on Railway

1. Go to your Railway project dashboard
2. Click on your service
3. Go to the "Variables" tab
4. Add each environment variable:
   - Key: `DATABASE_URL`
   - Value: `postgresql://username:password@host:port/database`

## Testing the Fix

1. Deploy the updated code to Railway
2. Check the logs for the environment check output
3. The app should start without the secrets error

## Local Development

For local development, you can still use a `secrets.toml` file in `.streamlit/` with your actual values:

```toml
GEMINI_API_KEY = "your_actual_api_key"
password_hash = "your_password_hash"
```

This file should be in your `.gitignore` to avoid committing secrets.
