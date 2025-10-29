# ⚡ Quick Start: Deploy to Cloud in 30 Minutes

The fastest path to get your Ruby GEM app live on the internet with free hosting.

---

## ✅ Pre-Deployment Checklist

Before you start, make sure you have:

- [ ] A GitHub account
- [ ] Your code in a GitHub repository
- [ ] Your Google API key handy
- [ ] Your local SQLite database (`rubyestimator_local.db`) with data you want to migrate

---

## 🚀 Deployment Steps

### Step 1: Set Up Cloud Database (10 minutes)

1. **Go to:** https://neon.tech
2. **Sign up** using GitHub
3. **Create project:** Name it "RubyEstimator"
4. **Copy connection string** - it looks like:
   ```
   postgresql://user:password@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
5. **Save it** - you'll need it in the next steps

### Step 2: Migrate Your Data (5 minutes)

1. **Create `.env` file** in your project root:

   ```bash
   DATABASE_URL=postgresql://user:password@your-host.neon.tech/neondb?sslmode=require
   GEMINI_API_KEY=your_gemini_api_key
   ```

2. **Run migration script:**

   ```bash
   pip install -r requirements.txt
   python migrate_to_postgres.py
   ```

3. **Verify:** The script will show you how many rows were migrated

### Step 3: Test Locally (5 minutes)

1. **Run your app:**

   ```bash
   streamlit run app.py
   ```

2. **Test that it works:**

   - Add a new vehicle
   - Check that your old data is there
   - Verify calculations work

3. **If it works**, you're ready to deploy! ✅

### Step 4: Push to GitHub (2 minutes)

```bash
git add .
git commit -m "Ready for cloud deployment"
git push origin main
```

**Verify:** Your `.gitignore` should exclude:

- `.env`
- `.streamlit/secrets.toml`
- `*.db`

### Step 5: Deploy to Streamlit Cloud (8 minutes)

1. **Go to:** https://share.streamlit.io

2. **Sign in** with GitHub

3. **Click:** "New app"

4. **Configure:**

   - Repository: `YourUsername/RubyEstimator`
   - Branch: `main`
   - Main file: `app.py`
   - App URL: Choose a custom name (e.g., `ruby-gem-estimator`)

5. **Click:** "Advanced settings" ⚙️

6. **Add secrets** (paste this with YOUR actual values):

   ```toml
   [api]
   GEMINI_API_KEY = "your_actual_gemini_api_key"

   DATABASE_URL = "postgresql://user:pass@your-host.neon.tech/neondb?sslmode=require"
   ```

7. **Click:** "Deploy!"

8. **Wait** 2-5 minutes for deployment

---

## 🎉 You're Live!

Your app is now accessible at:

```
https://your-app-name.streamlit.app
```

---

## 🧪 Post-Deployment Testing

Visit your live URL and test:

- [ ] Homepage loads
- [ ] Can search for a vehicle
- [ ] Vehicle data is processed correctly
- [ ] Can view history (your migrated data should be there)
- [ ] Admin panel works
- [ ] No errors in the app

---

## 📊 Monitor Your App

### Streamlit Cloud Dashboard

https://share.streamlit.io/

- View logs
- Manage secrets
- Reboot app
- See analytics

### Neon Database Dashboard

https://console.neon.tech/

- View database usage
- Monitor queries
- Manage backups

---

## 🆘 Common Issues

### "Module not found" error

**Fix:**

```bash
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update requirements"
git push
```

### "Database connection failed"

**Fix:**

- Verify your `DATABASE_URL` in Streamlit secrets
- Make sure it ends with `?sslmode=require`
- Check your Neon database is active (not paused)

### App is slow to load

**Normal!** Free tier apps sleep after 15 minutes of inactivity. First load takes 10-30 seconds.

---

## 💰 Cost

**Total: $0/month**

- Streamlit Community Cloud: FREE
- Neon PostgreSQL: FREE (0.5 GB)

Your app will run indefinitely on the free tier unless you exceed:

- 0.5 GB database storage
- 3 GB data transfer/month

Both are very unlikely for a vehicle estimator app.

---

## 🔄 Update Your App

To deploy updates:

```bash
# Make your changes
git add .
git commit -m "Updated feature X"
git push origin main
```

Streamlit Cloud automatically redeploys! (takes ~2 minutes)

---

## 📚 Need More Details?

See the comprehensive guide: `CLOUD_DEPLOYMENT_GUIDE.md`

---

## ✅ Deployment Complete Checklist

- [ ] Neon database created
- [ ] Local data migrated to Neon
- [ ] Tested app locally with cloud database
- [ ] Code pushed to GitHub
- [ ] Streamlit Cloud app created
- [ ] Secrets configured in Streamlit Cloud
- [ ] App deployed successfully
- [ ] Tested live app
- [ ] Bookmarked live URL
- [ ] Bookmarked Streamlit Cloud dashboard
- [ ] Bookmarked Neon database dashboard

**You're done!** 🎊

Share your app URL with users and enjoy your free cloud hosting!
