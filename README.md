# RubyEstimator - Vehicle Weight & Cost Calculator

A Streamlit web application that estimates vehicle curb weights and calculates commodity values for automotive recycling.

## 🚀 NEW: Single-Call Gemini Resolution System

This application now uses a **minimal single-call vehicle resolution system** powered by:

- ✅ **Gemini 2.5 Flash** with Google Search Grounding
- ✅ **Strict JSON output** via `responseSchema` + `responseMimeType: "application/json"`
- ✅ **Direct citations** from grounding metadata (OEM preferred, or 2 agreeing secondaries)
- ✅ **No caching** - always fresh, always persisted to DB
- ✅ **Simple validation** - numeric units normalized (lbs), booleans (true/false), per-field status

📖 **See [DOCUMENTATION.md](DOCUMENTATION.md) for complete documentation.**

### Quick Start

1. **Set API Key** (copy template and edit):
   ```bash
   cp .streamlit/secrets.toml.template .streamlit/secrets.toml
   # Edit .streamlit/secrets.toml and add your GEMINI_API_KEY
   ```
2. **Test It**:

   ```bash
   python test_single_call_gemini.py
   ```

3. **Run App**:
   ```bash
   streamlit run app.py
   ```

---

## Features

- **Vehicle Search**: Look up vehicle curb weights using Google's Gemini AI API with Search Grounding
- **Cost Calculator**: Calculate commodity values and profit margins
- **Database Storage**: PostgreSQL/SQLite database with evidence tracking
- **Material Detection**: Automatically detect aluminum vs iron engines and rims
- **Password Protection**: Optional authentication for secure access
- **Citation Tracking**: Every field value includes source URLs and quotes from grounding

## Color Palette & Usage

RubyEstimator uses a distinctive six-color palette for a cohesive, branded look throughout the app:

| Color Name     | Hex     | Sample                                                          | Usage                                                                       |
| -------------- | ------- | --------------------------------------------------------------- | --------------------------------------------------------------------------- |
| Big Dip O'Ruby | #990C41 | ![#990C41](https://via.placeholder.com/15/990C41/000000?text=+) | **Dominant color**: Main branding, headers, primary buttons, key highlights |
| Ruby           | #E0115F | ![#E0115F](https://via.placeholder.com/15/E0115F/000000?text=+) | Accent: Secondary buttons, links, important highlights                      |
| French Rose    | #F14C8A | ![#F14C8A](https://via.placeholder.com/15/F14C8A/000000?text=+) | Accent: Subtle highlights, info, hover states                               |
| Green (NCS)    | #0C9964 | ![#0C9964](https://via.placeholder.com/15/0C9964/000000?text=+) | Success: Success messages, positive feedback                                |
| UFO Green      | #11E092 | ![#11E092](https://via.placeholder.com/15/11E092/000000?text=+) | Success accent: Progress bars, secondary success, confirmations             |
| Bright Mint    | #4CF1B3 | ![#4CF1B3](https://via.placeholder.com/15/4CF1B3/000000?text=+) | Background accent: Info boxes, backgrounds, subtle accents                  |

**Guidelines:**

- Use **Big Dip O'Ruby (#990C41)** for all primary branding, main headers, and primary action buttons.
- Use **Ruby (#E0115F)** for secondary actions, links, and important highlights.
- Use **French Rose (#F14C8A)** for subtle highlights, info, and hover states.
- Use **Green (NCS) (#0C9964)** for success messages and positive feedback.
- Use **UFO Green (#11E092)** for progress bars and secondary success indicators.
- Use **Bright Mint (#4CF1B3)** for info boxes, backgrounds, and subtle accent areas.

This palette ensures a vibrant, accessible, and consistent user experience.

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
├── app.py                          # Main Streamlit application
├── vehicle_data.py                 # Vehicle data processing and resolver integration
├── auth.py                        # Password protection and authentication
├── database_config.py             # Database connection helpers
├── confidence_ui.py               # UI components for confidence indicators
├── simplified_ui_components.py    # Streamlined UI components
├── canonicalizer.py               # Input alias mapping and validation
├── source_router.py               # Deterministic source routing
├── parallel_http_fetcher.py       # Strict HTTP fetching with timeouts
├── source_parsers.py              # CSS/XPath per-source parsers
├── candidate_validator.py         # Field-level validation rules
├── candidate_resolver.py          # Deterministic value selection rules
├── micro_llm_resolver.py          # Optional micro-LLM conflict resolver
├── persistence.py                 # Database persistence (vehicles/field_values/evidence/runs)
├── generate_password.py           # Password hash generator utility
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Container configuration
├── railway.json                   # Railway deployment config
├── runtime.txt                    # Python version specification
├── DEPLOYMENT_GUIDE.md            # Detailed deployment instructions
├── DEPLOYMENT_CHECKLIST.md        # Pre-deployment checklist
├── .streamlit/
│   └── config.toml               # Streamlit configuration
├── .kiro/                        # Kiro AI assistant specifications
│   └── specs/                    # Feature specifications and tasks
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
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
