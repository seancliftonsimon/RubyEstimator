# PostgreSQL Database Setup Guide

## Overview

This guide will help you set up a PostgreSQL database in Railway and connect it to your RubyEstimator app for reliable, persistent data storage.

## Step 1: Create PostgreSQL Database in Railway

1. **Go to your Railway project dashboard**
2. **Click "New" → "Database" → "PostgreSQL"**
3. **Name your database**: `rubyestimator-db` (or any name you prefer)
4. **Click "Deploy Database"**

## Step 2: Get Database Connection Details

After creating the database:

1. **Click on your new PostgreSQL database** in the Railway dashboard
2. **Go to "Connect" tab**
3. **Copy the connection details** - Railway will automatically provide these environment variables:
   - `DATABASE_URL` (primary connection string)
   - `PGHOST` (hostname)
   - `PGPORT` (port, usually 5432)
   - `PGDATABASE` (database name)
   - `PGUSER` (username)
   - `PGPASSWORD` (password)

## Step 3: Connect Database to Your App

Railway will automatically connect the database to your app, but you can verify:

1. **Go to your app's dashboard**
2. **Check "Variables" tab** - you should see the database environment variables
3. **If not automatically connected**, manually add the `DATABASE_URL` variable

## Step 4: Deploy Your Updated Code

1. **Push your updated code** to GitHub
2. **Railway will automatically redeploy** with the new PostgreSQL dependencies
3. **Check the logs** for database connection messages

## Step 5: Verify Database Connection

After deployment, check the logs for:

```
=== DATABASE SETUP ===
DATABASE_URL: postgresql://...
PGHOST: ...
PGPORT: 5432
PGDATABASE: ...
PGUSER: ...
PGPASSWORD: Set
Database connection: Database connection successful
✅ Database tables created successfully
```

## Database Schema

The app will automatically create this table:

```sql
CREATE TABLE vehicles (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    curb_weight_lbs INTEGER,
    aluminum_engine BOOLEAN,
    aluminum_rims BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, make, model)
);
```

## Benefits of PostgreSQL

✅ **Automatic Backups**: Railway handles database backups automatically
✅ **Data Persistence**: Data survives app redeployments
✅ **Scalability**: Can handle larger datasets
✅ **Reliability**: ACID compliance and transaction support
✅ **Performance**: Optimized for complex queries

## Troubleshooting

### Database Connection Fails

1. **Check environment variables** in Railway dashboard
2. **Verify database is running** in Railway dashboard
3. **Check logs** for specific error messages
4. **Ensure database is in same project** as your app

### Tables Not Created

1. **Check app logs** for table creation messages
2. **Verify database permissions** are correct
3. **Manually create tables** if needed (see schema above)

### Data Not Persisting

1. **Verify database connection** is working
2. **Check if data is being inserted** (check logs)
3. **Verify database is properly connected** to your app

## Local Development

For local development, you can:

1. **Install PostgreSQL locally**
2. **Create a local database**
3. **Set environment variables** in `.streamlit/secrets.toml`:
   ```toml
   DATABASE_URL = "postgresql://username:password@localhost:5432/rubyestimator"
   ```

## Migration from SQLite

If you have existing SQLite data:

1. **Export data** from SQLite database
2. **Import data** into PostgreSQL (manual process)
3. **Update connection** to use PostgreSQL

## Monitoring

- **Check Railway dashboard** for database metrics
- **Monitor connection logs** in app deployment
- **Use Railway's built-in database tools** for queries

## Security

- **Database credentials** are automatically managed by Railway
- **Connection strings** are encrypted
- **No manual credential management** required
