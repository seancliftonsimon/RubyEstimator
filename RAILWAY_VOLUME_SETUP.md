# Railway Persistent Volume Setup Guide

## The Problem with Our Current Approach

Railway persistent volumes are **NOT** configured through `railway.json` files. They must be created through the Railway dashboard. Our current configuration won't work because:

1. The `volumes` section in `railway.json` is not the correct way to create persistent volumes
2. Railway volumes must be created manually through the dashboard
3. The volume needs to be properly mounted and configured

## Correct Setup Process

### Step 1: Remove Volume Configuration from railway.json

✅ **DONE** - We've removed the incorrect volume configuration from `railway.json`

### Step 2: Create Volume Through Railway Dashboard

1. **Go to your Railway project dashboard**
2. **Click on "Volumes" tab** (if you don't see it, you may need to upgrade your plan)
3. **Click "New Volume"**
4. **Configure the volume:**
   - **Name**: `database-storage`
   - **Mount Path**: `/data`
   - **Size**: `1GB` (or as needed)
5. **Click "Create Volume"**

### Step 3: Verify Volume Creation

After creating the volume, you should see:

- Volume listed in the Volumes tab
- Status showing as "Active" or "Mounted"
- Mount path showing `/data`

### Step 4: Deploy and Test

1. **Push your code** to trigger a new deployment
2. **Check the logs** for these messages:
   ```
   ✅ Using Railway persistent volume at /data
   Database directory: /data
   Directory exists: True
   Directory writable: True
   ```

## Alternative: Use Railway's Built-in Storage

If you can't create volumes (free tier limitation), Railway provides other persistent storage options:

### Option A: Use `/tmp` Directory (May Persist)

```bash
# Set environment variable
DATABASE_PATH=/tmp/vehicle_weights.db
```

### Option B: Use `/app` Directory (May Persist)

```bash
# Set environment variable
DATABASE_PATH=/app/data/vehicle_weights.db
```

### Option C: Use Current Directory (May Persist)

```bash
# Set environment variable
DATABASE_PATH=./vehicle_weights.db
```

## Testing Volume Setup

### Test 1: Check Volume Creation

After creating the volume in the dashboard, deploy and check logs for:

```
✅ Using Railway persistent volume at /data
```

### Test 2: Test File Operations

The app will automatically test:

- Writing to `/data/test_file.txt`
- Reading from `/data/test_file.txt`
- Database operations in `/data/vehicle_weights.db`

### Test 3: Test Persistence

1. Add a vehicle to the database
2. Redeploy the app
3. Check if the vehicle data persists

## Troubleshooting

### Volume Not Appearing in Dashboard

- **Check your Railway plan** - volumes may require a paid plan
- **Contact Railway support** if volumes tab is missing

### Volume Created But Not Mounted

- **Check mount path** - should be `/data`
- **Redeploy** after volume creation
- **Check logs** for mounting errors

### Permission Errors

- **Check volume permissions** in dashboard
- **Verify mount path** is correct
- **Try different mount paths** if needed

## Recommended Approach

1. **Try creating the volume through the dashboard first**
2. **If that doesn't work, use environment variable fallback:**
   ```
   DATABASE_PATH=/tmp/vehicle_weights.db
   ```
3. **Test persistence** by adding data and redeploying

## Environment Variable Setup

If you need to use the fallback approach:

1. **Go to Railway dashboard** → Variables tab
2. **Add environment variable:**
   - **Name**: `DATABASE_PATH`
   - **Value**: `/tmp/vehicle_weights.db`
3. **Save and redeploy**

This will bypass the volume system and use Railway's temporary storage, which often persists between deployments.
