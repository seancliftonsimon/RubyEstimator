# Railway Deployment Guide with Database Persistence

## Overview

This guide explains how to deploy RubyEstimator on Railway with persistent database storage.

## Database Persistence Solutions

### Solution 1: Railway Persistent Volumes (Recommended)

The app is configured to use Railway's persistent volumes to store the SQLite database.

**What's configured:**

- Database file stored in `/data/vehicle_weights.db`
- Persistent volume mounted at `/data` with 1GB storage
- Automatic backup/restore system

**To deploy:**

1. Push your code to Railway
2. The persistent volume will be automatically created
3. Database will persist between deployments

### Solution 2: Environment Variable Override (Fallback)

If persistent volumes don't work, you can set a custom database path:

1. Go to your Railway project dashboard
2. Navigate to Variables tab
3. Add environment variable: `DATABASE_PATH=/tmp/vehicle_weights.db`
4. Redeploy

**Alternative paths to try:**

- `/tmp/vehicle_weights.db` (temporary directory, may persist)
- `/app/data/vehicle_weights.db` (app directory)
- `./vehicle_weights.db` (current directory)

### Solution 3: Manual Backup/Restore

The app includes automatic backup/restore functionality:

- **Automatic backups**: Created on app startup
- **Backup location**: `vehicle_weights.db.backup` (same directory as main DB)
- **JSON export**: Available via `export_database_to_json()` function

## Troubleshooting Persistent Volume Issues

### If /data directory doesn't exist:

1. **Check Railway volume configuration**:

   - Go to Railway dashboard → Volumes tab
   - Ensure volume is created and mounted
   - Check volume size and permissions

2. **Try environment variable override**:

   ```
   DATABASE_PATH=/tmp/vehicle_weights.db
   ```

3. **Check Railway logs** for these messages:
   - `✅ Using Railway persistent volume at /data`
   - `✅ Created and using /data directory`
   - `⚠️ /data not writable, using /tmp fallback`

### Database not persisting?

1. Check Railway logs for database path messages
2. Verify persistent volume is mounted: `ls -la /data`
3. Check if backup files exist: `ls -la *.backup`

### Permission errors?

1. Ensure `/data` directory exists and is writable
2. Check Railway volume configuration in dashboard
3. Try alternative paths via environment variables

### Data loss after deployment?

1. Check for backup files: `vehicle_weights.db.backup`
2. Restore manually if needed
3. Consider using JSON export for critical data

## Environment Variables

**Required:**

- `GEMINI_API_KEY`: Your Google Gemini API key

**Optional:**

- `DATABASE_PATH`: Custom database file path
- `RAILWAY_ENVIRONMENT`: Set by Railway automatically

## Monitoring

Check Railway logs for these messages:

- `Using database file: /data/vehicle_weights.db`
- `Database backed up to: /data/vehicle_weights.db.backup`
- `Database restored from: /data/vehicle_weights.db.backup`

## Best Practices

1. **Regular backups**: The app creates backups automatically
2. **Monitor storage**: Check volume usage in Railway dashboard
3. **Test deployments**: Always test with a small dataset first
4. **Keep backups**: Download JSON exports for critical data

## Migration from Local Development

If you have existing data in a local database:

1. Export your local database to JSON:

   ```python
   from vehicle_data import export_database_to_json
   export_database_to_json()
   ```

2. Upload the JSON file to your Railway deployment

3. Import the data:

   ```python
   from vehicle_data import import_database_from_json
   import_database_from_json("vehicle_data_backup_YYYYMMDD_HHMMSS.json")
   ```

## Quick Fix for Current Issue

Since the persistent volume isn't working, try this immediate solution:

1. **Go to Railway dashboard** → Variables tab
2. **Add environment variable**:
   - Name: `DATABASE_PATH`
   - Value: `/tmp/vehicle_weights.db`
3. **Redeploy** your app

This will use the `/tmp` directory which may persist better between deployments than the current setup.
