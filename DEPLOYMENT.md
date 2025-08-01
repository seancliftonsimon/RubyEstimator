# Streamlit Cloud Deployment Guide

## 🚀 Quick Deployment Steps

### 1. Commit and Push Your Changes

```bash
git add .
git commit -m "Setup for Streamlit Cloud deployment with secure API key handling"
git push origin main
```

### 2. Deploy to Streamlit Cloud

1. **Go to Streamlit Cloud**: Visit [share.streamlit.io](https://share.streamlit.io)
2. **Sign in**: Use your GitHub account
3. **Create New App**:
   - Click "New app"
   - Select your repository: `your-username/RubyEstimator`
   - Branch: `main`
   - Main file path: `app.py`
   - Click "Deploy"

### 3. Add Your API Key (CRITICAL)

1. **In your deployed app**, click the hamburger menu (☰) in the top right
2. **Go to Settings** → **Secrets**
3. **Add your Gemini API key**:
   ```toml
   GEMINI_API_KEY = "your-actual-api-key-here"
   ```
4. **Save** and your app will automatically redeploy

### 4. Test Your App

- Your app should now be live at: `https://your-app-name.streamlit.app`
- Test by searching for a vehicle (e.g., "2013 Toyota Camry")
- The API calls should work without exposing your key

## 🔒 Security Features

✅ **API Key Protection**: Your key is now stored securely in Streamlit Cloud secrets
✅ **Private Repository**: Only people you invite can see your code
✅ **No Hardcoded Secrets**: API key is removed from source code
✅ **Environment Isolation**: Local and cloud environments are separate

## 🛠️ Local Development

For local development, your API key is stored in `.streamlit/secrets.toml` (which is gitignored).

To run locally:

```bash
streamlit run app.py
```

## 📊 Monitoring

- **API Usage**: Monitor your Gemini API usage at [Google AI Studio](https://aistudio.google.com/app/apikey)
- **App Performance**: Check Streamlit Cloud dashboard for app metrics
- **Database**: The SQLite database will be created automatically on first use

## 🔧 Troubleshooting

### App Won't Deploy

- Check that `app.py` is in the root directory
- Ensure all dependencies are in `requirements.txt`
- Verify your repository is connected to Streamlit Cloud

### API Key Not Working

- Double-check the secret name: `GEMINI_API_KEY`
- Ensure the key is valid and has sufficient quota
- Check the app logs in Streamlit Cloud settings

### Database Issues

- The database file is excluded from git (good for security)
- A new database will be created on each deployment
- Consider using a cloud database for production

## 🎯 Next Steps

1. **Test thoroughly** with various vehicles
2. **Monitor API costs** - Gemini API has usage limits
3. **Consider adding more features** like batch processing
4. **Share your app** with colleagues using the Streamlit Cloud URL

## 📞 Support

- **Streamlit Cloud Issues**: [Streamlit Community](https://discuss.streamlit.io/)
- **Gemini API Issues**: [Google AI Studio Support](https://ai.google.dev/support)
- **Code Issues**: Check your repository issues
