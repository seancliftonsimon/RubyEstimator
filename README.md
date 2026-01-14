# RubyEstimator - Vehicle Weight & Cost Calculator

A Streamlit web application that estimates vehicle curb weights and calculates commodity values for automotive recycling.

## 🚀 Single-Call Gemini Resolution System

This application uses a **minimal single-call vehicle resolution system** powered by:

- ✅ **Gemini 2.0 Flash (experimental)** with Google Search Grounding
- ✅ **JSON-only output** enforced via prompt instructions
- ✅ **Direct citations** from grounding metadata (OEM preferred, or 2 agreeing secondaries)
- ✅ **Database caching** - prior results reused, always persisted to DB
- ✅ **Simple validation** - numeric units normalized (lbs), booleans (true/false), per-field status

📖 **See [DOCUMENTATION.md](DOCUMENTATION.md) for complete documentation.**

## Quick Start

1. **Set API Key**:
   Create `.streamlit/secrets.toml`:
   ```toml
   [api]
   GEMINI_API_KEY = "your-key"
   ```

2. **Run App**:
   ```bash
   streamlit run app.py
   ```

## File Structure

```
RubyEstimator/
├── app.py                          # Main Streamlit application
├── vehicle_data.py                 # Vehicle data processing and resolver integration
├── single_call_gemini_resolver.py  # Core resolver logic
├── persistence.py                  # Database schema management
├── database_config.py              # Database connection helpers
├── auth.py                         # Password protection
├── confidence_ui.py                # UI components for confidence indicators
├── styles.py                       # Centralized styling
├── seed_catalog.json               # Vehicle catalog seed data
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container configuration
├── railway.json                    # Railway deployment config
├── runtime.txt                     # Python version specification
├── DOCUMENTATION.md                # Complete documentation
└── README.md                       # This file
```

## Deployment

See [DOCUMENTATION.md](DOCUMENTATION.md#deployment-guide) for detailed deployment instructions.

## Support

- **Streamlit Issues**: [Streamlit Community](https://discuss.streamlit.io/)
- **Gemini API Issues**: [Google AI Studio Support](https://ai.google.dev/support)
