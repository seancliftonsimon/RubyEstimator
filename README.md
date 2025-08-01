# RubyEstimator - Vehicle Weight & Cost Calculator

A Streamlit web application that estimates vehicle curb weights and calculates commodity values for automotive recycling.

## Features

- **Vehicle Search**: Look up vehicle curb weights using Google's Gemini AI API
- **Cost Calculator**: Calculate commodity values and profit margins
- **Database Storage**: PostgreSQL database to cache vehicle information
- **Material Detection**: Automatically detect aluminum vs iron engines and rims
- **Password Protection**: Optional authentication for secure access

## Local Development Setup

### Prerequisites

- Python 3.8+
- PostgreSQL database (local or cloud)
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

3. Set up environment variables:

   - Create a `.streamlit/secrets.toml` file
   - Add your configuration:

   ```toml
   GEMINI_API_KEY = "your_actual_api_key_here"
   DATABASE_URL = "postgresql://username:password@localhost/rubyestimator"
   password_hash = "your_password_hash_here"  # Optional
   ```

4. Run the application:

```bash
streamlit run app.py
```

## Deployment Options

### Railway Deployment (Recommended)

Railway provides PostgreSQL database and easy deployment:

1. **Push your code to GitHub**

2. **Deploy to Railway**:

   - Go to [railway.app](https://railway.app)
   - Connect your GitHub repository
   - Railway will automatically detect and deploy your app

3. **Set up PostgreSQL Database**:

   - In Railway dashboard, click "New" → "Database" → "PostgreSQL"
   - Name your database (e.g., `rubyestimator-db`)
   - Railway will automatically provide the `DATABASE_URL` environment variable

4. **Set Environment Variables** in Railway dashboard:

   - `DATABASE_URL`: `${{ Postgres.DATABASE_URL }}` (Railway will provide this)
   - `GEMINI_API_KEY`: Your actual Gemini API key
   - `PASSWORD_HASH`: Optional password protection (generate with `python generate_password.py`)

5. **Your app will be live** at the Railway-provided URL

### Streamlit Cloud Deployment

1. **Push your code to GitHub**

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

### Docker Deployment

The project includes a Dockerfile for containerized deployment:

```bash
docker build -t rubyestimator .
docker run -p 8501:8501 rubyestimator
```

## Database Schema

The app automatically creates this PostgreSQL table:

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

## Security Features

- ✅ API keys stored securely using environment variables
- ✅ Database credentials managed by deployment platform
- ✅ Optional password protection with SHA-256 hashing
- ✅ Private repository support for code security

## File Structure

```
RubyEstimator/
├── app.py                 # Main Streamlit application
├── vehicle_data.py        # Vehicle data processing and API calls
├── auth.py               # Password protection and authentication
├── database_config.py    # Database connection and setup
├── requirements.txt      # Python dependencies
├── Dockerfile           # Container configuration
├── railway.json         # Railway deployment config
├── runtime.txt          # Python version specification
├── .streamlit/
│   └── config.toml     # Streamlit configuration
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## Usage

1. Enter vehicle year, make, and model
2. The app will search for curb weight and material specifications
3. View calculated commodity values and profit estimates
4. Use manual entry for unknown vehicles

## API Usage

The app uses Google's Gemini AI API to search for vehicle specifications. API calls are cached in the PostgreSQL database to reduce costs and improve performance.

## Troubleshooting

### Database Connection Issues

- Verify `DATABASE_URL` is set correctly
- Check database is running and accessible
- Ensure all required environment variables are set
- For Railway: Verify database is in the same project as your app

### API Key Issues

- Verify `GEMINI_API_KEY` is set correctly
- Check API key has sufficient quota
- Test API key in Google AI Studio

### Deployment Issues

- Check all environment variables are set
- Verify repository is connected to deployment platform
- Check deployment logs for specific errors

## Support

- **Streamlit Issues**: [Streamlit Community](https://discuss.streamlit.io/)
- **Gemini API Issues**: [Google AI Studio Support](https://ai.google.dev/support)
- **Railway Issues**: [Railway Documentation](https://docs.railway.app/)
