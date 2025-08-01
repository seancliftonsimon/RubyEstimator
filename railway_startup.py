#!/usr/bin/env python3
"""
Railway startup script to ensure proper environment variable handling
and prevent secrets.toml errors.
"""

import os
import sys

def check_environment():
    """Check if required environment variables are set."""
    print("=== Railway Environment Check ===")
    
    # Check for database variables
    db_vars = ['DATABASE_URL', 'PGHOST', 'PGDATABASE', 'PGUSER', 'PGPASSWORD']
    db_configured = any(os.getenv(var) for var in db_vars)
    
    if db_configured:
        print("✅ Database configuration found")
    else:
        print("⚠️  No database configuration found - app may not work properly")
    
    # Check for API key
    if os.getenv('GEMINI_API_KEY'):
        print("✅ GEMINI_API_KEY found")
    else:
        print("⚠️  GEMINI_API_KEY not set - vehicle search may not work")
    
    # Check for password protection
    if os.getenv('PASSWORD_HASH'):
        print("✅ Password protection configured")
    else:
        print("ℹ️  No password protection configured - app will be open")
    
    print("=== Environment Check Complete ===")

if __name__ == "__main__":
    check_environment()
    
    # Start Streamlit
    print("Starting Streamlit application...")
    os.system(f"{sys.executable} -m streamlit run app.py --server.port=8501 --server.address=0.0.0.0") 