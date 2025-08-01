# RubyEstimator - Vehicle Weight & Cost Calculator

A Streamlit web application that estimates vehicle curb weights and calculates commodity values for automotive recycling.

## Features

- **Vehicle Search**: Look up vehicle curb weights using Google's Gemini AI API
- **Cost Calculator**: Calculate commodity values and profit margins
- **Database Storage**: Local SQLite database to cache vehicle information
- **Material Detection**: Automatically detect aluminum vs iron engines and rims

## Local Development Setup

### Prerequisites

- Python 3.8+
- Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

### Installation

1. Clone the repository:

```bash
git clone <your-repo-url>
cd RubyEstimator
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up your API key:

   - Create a `.streamlit/secrets.toml` file (already created)
   - Replace the placeholder API key with your actual Gemini API key

4. Run the application:

```bash
streamlit run app.py
```

## Deployment to Streamlit Cloud

### Prerequisites

- GitHub repository (private or public)
- Streamlit Cloud account

### Steps

1. **Push your code to GitHub** (if not already done):

```bash
git add .
git commit -m "Setup for Streamlit Cloud deployment"
git push origin main
```

2. **Deploy to Streamlit Cloud**:

   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository and main branch
   - Set the path to your app: `app.py`
   - Click "Deploy"

3. **Add your API key to Streamlit Cloud**:
   - In your app's settings, go to "Secrets"
   - Add your Gemini API key:
   ```toml
   GEMINI_API_KEY = "your-actual-api-key-here"
   ```

## Security Notes

- ✅ API keys are stored securely using Streamlit secrets
- ✅ Local development secrets are ignored by git
- ✅ Database file is excluded from version control
- ✅ Private repository keeps code secure

## File Structure

```
RubyEstimator/
├── app.py                 # Main Streamlit application
├── vehicle_data.py        # Vehicle data processing and API calls
├── requirements.txt       # Python dependencies
├── .streamlit/
│   └── secrets.toml      # Local development secrets (gitignored)
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## Usage

1. Enter vehicle year, make, and model
2. The app will search for curb weight and material specifications
3. View calculated commodity values and profit estimates
4. Use manual entry for unknown vehicles

## API Usage

The app uses Google's Gemini AI API to search for vehicle specifications. API calls are cached in the local database to reduce costs and improve performance.
