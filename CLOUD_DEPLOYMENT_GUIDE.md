# 🚀 Cloud Deployment Guide

Complete guide to deploy Ruby GEM Vehicle Estimator to the cloud with free hosting.

## 📌 Recommended Setup

- **Web App Hosting:** Streamlit Community Cloud (FREE)
- **Database:** Neon PostgreSQL (FREE tier)
- **Total Cost:** $0/month
- **Deployment Time:** ~30 minutes

---

## 🗄️ Part 1: Set Up Cloud Database (Neon PostgreSQL)

### Step 1: Create Neon Account & Database

1. Go to https://neon.tech
2. Click "Sign Up" (use GitHub for easy auth)
3. Create a new project:
   - **Project Name:** RubyEstimator
   - **PostgreSQL Version:** 15 (default)
   - **Region:** Choose closest to your users (US East is good default)
4. Click "Create Project"

### Step 2: Get Connection String

1. In your Neon dashboard, click on your project
2. Go to "Connection Details" or "Dashboard"
3. Copy the **Connection String** (it looks like):
   ```
   postgresql://username:password@ep-cool-name-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
4. **SAVE THIS SECURELY** - you'll need it multiple times

### Step 3: Save Credentials Locally

Create or update your `.env` file in your project root:

```bash
# PostgreSQL Database (Neon)
DATABASE_URL=postgresql://your-username:password@your-host.neon.tech/neondb?sslmode=require

# Your existing API keys (also works as GEMINI_API_KEY)
GEMINI_API_KEY=your_actual_gemini_api_key_here

# Admin password (if using)
ADMIN_PASSWORD=your_admin_password
```

⚠️ **Important:** Add `.env` to your `.gitignore` to prevent committing secrets!

---

## 📊 Part 2: Migrate Data from SQLite to PostgreSQL

### Step 1: Run Migration Script

Open your terminal in the project directory and run:

```bash
# Make sure you have dependencies installed
pip install -r requirements.txt

# Run migration
python migrate_to_postgres.py
```

The script will:

- ✓ Connect to your local SQLite database
- ✓ Connect to your cloud PostgreSQL database
- ✓ Copy all tables and data
- ✓ Verify the migration

### Step 2: Test Local Connection to Cloud DB

Test that your app works with the cloud database:

```bash
streamlit run app.py
```

Try adding a vehicle and verify:

- Data saves successfully
- Previous data (from migration) is visible
- No errors in the console

---

## ☁️ Part 3: Deploy to Streamlit Community Cloud

### Step 1: Prepare GitHub Repository

1. **Push your code to GitHub:**

   ```bash
   git add .
   git commit -m "Prepare for cloud deployment"
   git push origin main
   ```

2. **Verify `.gitignore` excludes:**
   - `.env`
   - `*.db` (SQLite files)
   - `__pycache__/`
   - `.streamlit/secrets.toml`

### Step 2: Create Streamlit Cloud Account

1. Go to https://share.streamlit.io
2. Sign in with **GitHub** (same account as your repository)
3. Grant Streamlit access to your repositories

### Step 3: Deploy Your App

1. Click "New app" or "Deploy an app"
2. Fill in the details:

   - **Repository:** Select your `RubyEstimator` repository
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **App URL:** Choose a custom URL (e.g., `ruby-gem-estimator`)

3. Click "Advanced settings" ⚙️

4. **Add Secrets** (this is where you add your environment variables):

   Click on "Secrets" and paste your credentials in TOML format:

   ```toml
   # Database Configuration
   DATABASE_URL = "postgresql://username:password@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require"

   # API Keys
   [api]
   GEMINI_API_KEY = "your_actual_gemini_api_key"

   # Admin Access (if using password protection)
   ADMIN_PASSWORD = "your_admin_password"
   ```

   ⚠️ **Replace with your actual values!**

5. Click "Deploy!"

### Step 4: Monitor Deployment

- Watch the deployment logs
- Initial deployment takes 2-5 minutes
- Look for "Your app is live!" message

### Step 5: Test Your Live App

1. Visit your app URL (e.g., `https://ruby-gem-estimator.streamlit.app`)
2. Test all features:
   - ✓ Add a new vehicle
   - ✓ View history
   - ✓ Check admin panel
   - ✓ Verify calculations

---

## 🔒 Part 4: Secure Your Deployment

### Database Security

✓ **Already Secure:** Neon automatically:

- Uses SSL/TLS encryption
- Requires authentication
- Isolates your database
- Auto-suspends when idle (saves resources)

### API Keys Security

✓ **Already Secure:** Streamlit secrets:

- Are never exposed in your code
- Are encrypted at rest
- Are only accessible to your app

### Application Security

✓ **Already Implemented:**

- Password protection for admin panel (in `auth.py`)
- No sensitive data in client-side code

---

## 💰 Cost Breakdown

### Streamlit Community Cloud (FREE)

- ✓ Unlimited public apps
- ✓ 1 GB RAM per app
- ✓ Automatic SSL
- ✓ Auto-updates from GitHub
- ⚠️ Limitation: App goes to sleep after inactivity (wakes up in 10-30 seconds)

### Neon PostgreSQL (FREE Tier)

- ✓ 0.5 GB storage (plenty for your needs)
- ✓ 3 GB data transfer/month
- ✓ Auto-suspend after 5 minutes of inactivity
- ✓ Unlimited compute time
- ⚠️ Limitation: Cold starts (1-2 seconds when waking up)

**Total: $0/month** 🎉

If you need more (future scaling):

- Neon Pro: $19/month (always-on, 10 GB, no cold starts)
- Streamlit for Teams: $250/month (private apps, more resources)

---

## 🔄 Part 5: Update & Maintain

### Update Your App

Your app auto-deploys when you push to GitHub:

```bash
# Make changes to your code
git add .
git commit -m "Update feature X"
git push origin main
```

Streamlit Cloud will automatically:

1. Detect the push
2. Rebuild your app
3. Deploy the new version (takes ~2 minutes)

### Monitor Your App

1. **Streamlit Cloud Dashboard:**

   - View logs
   - See metrics (CPU, memory)
   - Manage secrets
   - Reboot app if needed

2. **Neon Dashboard:**
   - Monitor database usage
   - View query performance
   - Check storage usage
   - Download backups

### Backup Your Database

**Automated (Neon):**

- Neon automatically backs up your database
- Point-in-time recovery available (last 7 days on free tier)

**Manual Backup:**

```bash
# Set your DATABASE_URL in .env
python -c "
from database_config import create_database_engine
import pandas as pd
from sqlalchemy import inspect

engine = create_database_engine()
inspector = inspect(engine)

for table in inspector.get_table_names():
    df = pd.read_sql_table(table, engine)
    df.to_csv(f'backup_{table}.csv', index=False)
    print(f'✓ Backed up {table}: {len(df)} rows')
"
```

---

## 🆘 Troubleshooting

### App Won't Deploy

**Error:** "ModuleNotFoundError"

- **Fix:** Make sure all dependencies are in `requirements.txt`
- Run: `pip freeze > requirements.txt`

**Error:** "Database connection failed"

- **Fix:** Check your `DATABASE_URL` in Streamlit secrets
- Make sure it includes `?sslmode=require`

### App is Slow

**Cause:** Cold start after inactivity

- **Free tier limitation:** App sleeps after 15 minutes
- **Solution:** Upgrade to paid tier OR accept 10-30 second wake-up time
- **Workaround:** Use a service like UptimeRobot to ping your app every 5 minutes

### Database Connection Errors

**Error:** "SSL connection required"

- **Fix:** Add `?sslmode=require` to end of DATABASE_URL

**Error:** "Too many connections"

- **Fix:** Neon free tier has connection limits. Make sure you're not creating too many engine instances.
- Already handled in your code with `create_engine()`

### Migration Issues

**Data didn't migrate:**

1. Check `rubyestimator_local.db` exists
2. Verify `DATABASE_URL` is correct in `.env`
3. Re-run `python migrate_to_postgres.py`

---

## 📱 Alternative Deployment Options

### Option 2: Railway.app (Easiest All-in-One)

**Pros:**

- One platform for app + database
- Auto-detects Streamlit
- Simple GitHub integration
- You already have `railway.json` configured!

**Cost:**

- $5/month free credit (hobbyist plan)
- ~$5-10/month after credits run out

**Steps:**

1. Go to https://railway.app
2. "New Project" → "Deploy from GitHub"
3. Select your repository
4. Railway auto-detects everything!
5. Add environment variables in Railway dashboard
6. Deploy!

### Option 3: Render + Supabase

**Pros:**

- Both have generous free tiers
- Supabase has nice database UI

**Cost:** $0/month

**Steps:**

1. **Database:** Sign up at https://supabase.com
2. Create project, get PostgreSQL URL
3. **Web:** Sign up at https://render.com
4. "New Web Service" → Connect GitHub
5. Add environment variables
6. Deploy!

---

## ✅ Post-Deployment Checklist

- [ ] App is accessible at your Streamlit Cloud URL
- [ ] Can add new vehicles and see results
- [ ] Historical data from SQLite is visible
- [ ] Admin panel works (if using password protection)
- [ ] API calls to Google work
- [ ] No errors in Streamlit Cloud logs
- [ ] Database is storing data in Neon
- [ ] Shared URL with users/stakeholders
- [ ] Bookmarked Streamlit Cloud dashboard
- [ ] Bookmarked Neon database dashboard
- [ ] Documented your URLs and credentials securely
- [ ] Set up backups (if needed)

---

## 🎉 You're Done!

Your app is now:

- ✅ Accessible from anywhere
- ✅ Using a cloud database
- ✅ Costing $0/month
- ✅ Auto-deploying from GitHub
- ✅ Secure and backed up

**Your Live URL:** `https://your-app-name.streamlit.app`

Share it with the world! 🌍
