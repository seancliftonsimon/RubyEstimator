# Railway Environment Variables Setup

## Problem: "No secrets files found"

This error occurs because the app is trying to read from a local `secrets.toml` file, but Railway doesn't use local secrets files. Instead, Railway uses environment variables.

## Solution: Set Environment Variables in Railway

### Step 1: Add Required Environment Variables

Go to your Railway app dashboard and add these environment variables:

1. **Go to your app's dashboard** in Railway
2. **Click "Variables" tab**
3. **Add these variables:**

#### Required Variables:

**Database Connection:**

- **Name**: `DATABASE_URL`
- **Value**: `${{ Postgres.DATABASE_URL }}`

**API Key:**

- **Name**: `GEMINI_API_KEY`
- **Value**: `AIzaSyDhOpIAllne17hVDZI2ADXuUcSeE0cPYvY` (or your actual API key)

#### Optional Variables:

**Password Protection (if desired):**

- **Name**: `PASSWORD_HASH`
- **Value**: (generate using `python generate_password.py`)

### Step 2: Verify Variables

After adding the variables, you should see:

- `DATABASE_URL` with the PostgreSQL connection string
- `GEMINI_API_KEY` with your API key
- Any other variables you added

### Step 3: Redeploy

1. **Save the variables** in Railway
2. **Your app will automatically redeploy**
3. **Check the logs** for successful connection messages

## Expected Log Output

After successful setup, you should see:

```
=== DATABASE SETUP ===
DATABASE_URL: postgresql://username:password@host:port/database
PGHOST: host
PGPORT: 5432
PGDATABASE: database
PGUSER: username
PGPASSWORD: Set
Database connection: Database connection successful
✅ Database tables created successfully
```

## Troubleshooting

### Still Getting Secrets Error?

1. **Check that all variables are set** in Railway dashboard
2. **Verify variable names** are exactly as shown above
3. **Ensure app has redeployed** after adding variables
4. **Check logs** for specific error messages

### Database Connection Issues?

1. **Verify `DATABASE_URL`** is set to `${{ Postgres.DATABASE_URL }}`
2. **Check database is running** in Railway dashboard
3. **Ensure both services** are in the same project

### API Key Issues?

1. **Verify `GEMINI_API_KEY`** is set correctly
2. **Check API key is valid** and has sufficient quota
3. **Test API key** in Google AI Studio

## Local Development

For local development, you can still use `secrets.toml`:

1. **Create `.streamlit/secrets.toml`** file
2. **Add your variables:**
   ```toml
   GEMINI_API_KEY = "your_api_key_here"
   DATABASE_URL = "postgresql://localhost/rubyestimator"
   PASSWORD_HASH = "your_password_hash_here"
   ```

## Security Notes

- **Environment variables** in Railway are encrypted
- **Database credentials** are automatically managed
- **No local secrets files** needed in production
- **API keys** are securely stored in Railway
