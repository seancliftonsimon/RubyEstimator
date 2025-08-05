import os
import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import streamlit as st

def get_database_url():
    """Get database URL from environment variables or Railway's built-in vars."""
    # Try Railway's built-in PostgreSQL URL first
    if os.getenv('DATABASE_URL'):
        return os.getenv('DATABASE_URL')
    
    # Fallback to individual components
    host = os.getenv('PGHOST')
    port = os.getenv('PGPORT', '5432')
    database = os.getenv('PGDATABASE')
    username = os.getenv('PGUSER')
    password = os.getenv('PGPASSWORD')
    
    if all([host, database, username, password]):
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    
    # Final fallback for local development
    return "postgresql://localhost/rubyestimator"

def create_database_engine():
    """Create SQLAlchemy engine for database operations."""
    database_url = get_database_url()
    return create_engine(database_url, echo=False)

def get_database_connection():
    """Get direct psycopg2 connection for raw SQL operations."""
    database_url = get_database_url()
    return psycopg2.connect(database_url)

def create_tables():
    """Create the vehicles table if it doesn't exist."""
    engine = create_database_engine()
    
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS vehicles (
                id SERIAL PRIMARY KEY,
                year INTEGER NOT NULL,
                make TEXT NOT NULL,
                model TEXT NOT NULL,
                curb_weight_lbs INTEGER,
                aluminum_engine BOOLEAN,
                aluminum_rims BOOLEAN,
                catalytic_converters INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(year, make, model)
            )
        """))
        try:
            conn.execute(text("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS catalytic_converters INTEGER"))
        except Exception as e:
            print(f"Warning: Could not add catalytic_converters column. It might already exist. Error: {e}")

        conn.commit()
    
    print("✅ Database tables created successfully")

def test_database_connection():
    """Test database connection and return status."""
    try:
        engine = create_database_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        return True, "Database connection successful"
    except Exception as e:
        return False, f"Database connection failed: {str(e)}"

def get_database_info():
    """Get database connection information for debugging."""
    info = {
        'DATABASE_URL': os.getenv('DATABASE_URL', 'Not set'),
        'PGHOST': os.getenv('PGHOST', 'Not set'),
        'PGPORT': os.getenv('PGPORT', 'Not set'),
        'PGDATABASE': os.getenv('PGDATABASE', 'Not set'),
        'PGUSER': os.getenv('PGUSER', 'Not set'),
        'PGPASSWORD': 'Set' if os.getenv('PGPASSWORD') else 'Not set'
    }
    return info 