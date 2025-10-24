import os
import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import streamlit as st
import json

def get_database_url():
    """Get database URL from environment variables or Railway's built-in vars."""
    # Try Railway's built-in PostgreSQL URL first
    if os.getenv('DATABASE_URL'):
        return os.getenv('DATABASE_URL')
    
    # Fallback to individual components for PostgreSQL
    host = os.getenv('PGHOST')
    port = os.getenv('PGPORT', '5432')
    database = os.getenv('PGDATABASE')
    username = os.getenv('PGUSER')
    password = os.getenv('PGPASSWORD')
    
    if all([host, database, username, password]):
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    
    # Final fallback for local development - use SQLite
    return "sqlite:///rubyestimator_local.db"

def is_sqlite():
    """Check if we're using SQLite database."""
    return get_database_url().startswith('sqlite:')

def get_datetime_interval_query(hours: int) -> str:
    """
    Generate database-agnostic datetime interval query.
    
    Returns SQL fragment for datetime comparison that works with both SQLite and PostgreSQL.
    For SQLite: datetime('now', '-X hours')
    For PostgreSQL: NOW() - INTERVAL 'X hours'
    
    Args:
        hours: Number of hours to subtract from current time
        
    Returns:
        SQL fragment for datetime comparison compatible with current database
    """
    if is_sqlite():
        return f"datetime('now', '-{hours} hours')"
    else:
        return f"NOW() - INTERVAL '{hours} hours'"

def create_database_engine():
    """Create SQLAlchemy engine for database operations."""
    database_url = get_database_url()
    return create_engine(database_url, echo=False)

def get_database_connection():
    """Get direct database connection for raw SQL operations."""
    database_url = get_database_url()
    if is_sqlite():
        # Extract the database file path from SQLite URL
        db_path = database_url.replace('sqlite:///', '')
        return sqlite3.connect(db_path)
    else:
        # Use psycopg2 for PostgreSQL
        import psycopg2
        return psycopg2.connect(database_url)

def create_tables():
    """Create the vehicles and app_config tables if they don't exist."""
    engine = create_database_engine()
    
    with engine.connect() as conn:
        if is_sqlite():
            # SQLite syntax
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS vehicles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            
            # App config table for admin-editable settings (SQLite uses TEXT instead of JSONB)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS app_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by TEXT
                )
            """))
        else:
            # PostgreSQL syntax
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

            # App config table for admin-editable settings
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS app_config (
                    key TEXT PRIMARY KEY,
                    value JSONB NOT NULL,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by TEXT
                )
            """))

        conn.commit()
    
    print("✅ Database tables created successfully")

def create_resolutions_table():
    """Create the resolutions table for tracking resolution history."""
    engine = create_database_engine()
    
    with engine.connect() as conn:
        if is_sqlite():
            # SQLite syntax
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS resolutions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicle_key VARCHAR(100) NOT NULL,
                    field_name VARCHAR(50) NOT NULL,
                    final_value FLOAT,
                    confidence_score FLOAT,
                    method VARCHAR(50),
                    candidates_json TEXT,
                    warnings_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(vehicle_key, field_name)
                )
            """))
        else:
            # PostgreSQL syntax
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS resolutions (
                    id SERIAL PRIMARY KEY,
                    vehicle_key VARCHAR(100) NOT NULL,
                    field_name VARCHAR(50) NOT NULL,
                    final_value FLOAT,
                    confidence_score FLOAT,
                    method VARCHAR(50),
                    candidates_json JSONB,
                    warnings_json JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(vehicle_key, field_name)
                )
            """))
        
        # Create indexes for fast lookups
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_resolutions_vehicle_key 
            ON resolutions(vehicle_key)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_resolutions_field_name 
            ON resolutions(field_name)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_resolutions_vehicle_field 
            ON resolutions(vehicle_key, field_name)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_resolutions_created_at 
            ON resolutions(created_at)
        """))
        
        conn.commit()
    
    print("✅ Resolutions table created successfully")

def validate_grounding_settings(settings: dict) -> bool:
    """Validate grounding settings configuration."""
    required_keys = ["target_candidates", "clustering_tolerance", "confidence_threshold", "outlier_threshold", "nut_fee_applies_to"]
    
    if not all(key in settings for key in required_keys):
        return False
    
    # Validate ranges
    if not (1 <= settings["target_candidates"] <= 10):
        return False
    if not (0.01 <= settings["clustering_tolerance"] <= 1.0):
        return False
    if not (0.0 <= settings["confidence_threshold"] <= 1.0):
        return False
    if not (0.5 <= settings["outlier_threshold"] <= 5.0):
        return False
    if settings["nut_fee_applies_to"] not in ["curb_weight", "elv_weight"]:
        return False
    
    return True

def validate_consensus_settings(settings: dict) -> bool:
    """Validate consensus settings configuration."""
    required_keys = ["min_agreement_ratio", "preferred_sources", "source_weights"]
    
    if not all(key in settings for key in required_keys):
        return False
    
    # Validate ranges
    if not (0.0 <= settings["min_agreement_ratio"] <= 1.0):
        return False
    
    # Validate preferred_sources is a list
    if not isinstance(settings["preferred_sources"], list):
        return False
    
    # Validate source_weights is a dict with numeric values
    if not isinstance(settings["source_weights"], dict):
        return False
    
    for weight in settings["source_weights"].values():
        if not isinstance(weight, (int, float)) or not (0.1 <= weight <= 3.0):
            return False
    
    return True

def initialize_default_settings():
    """Initialize default grounding and consensus settings if they don't exist."""
    try:
        engine = create_database_engine()
        with engine.connect() as conn:
            # Check if grounding_settings exists
            result = conn.execute(text("SELECT COUNT(*) FROM app_config WHERE key = 'grounding_settings'"))
            if result.fetchone()[0] == 0:
                default_grounding = {
                    "target_candidates": 3,
                    "clustering_tolerance": 0.15,
                    "confidence_threshold": 0.7,
                    "outlier_threshold": 2.0,
                    "nut_fee_applies_to": "curb_weight"
                }
                upsert_app_config("grounding_settings", default_grounding, "Grounding search settings", "system")
                print("✅ Default grounding settings initialized")
            
            # Check if consensus_settings exists
            result = conn.execute(text("SELECT COUNT(*) FROM app_config WHERE key = 'consensus_settings'"))
            if result.fetchone()[0] == 0:
                default_consensus = {
                    "min_agreement_ratio": 0.6,
                    "preferred_sources": ["kbb.com", "edmunds.com", "manufacturer"],
                    "source_weights": {
                        "kbb.com": 1.2,
                        "edmunds.com": 1.2,
                        "manufacturer": 1.5,
                        "default": 1.0
                    }
                }
                upsert_app_config("consensus_settings", default_consensus, "Consensus algorithm settings", "system")
                print("✅ Default consensus settings initialized")
                
        return True
    except Exception as e:
        print(f"❌ Failed to initialize default settings: {e}")
        return False

def migrate_database():
    """Run all database migrations."""
    try:
        create_tables()
        create_resolutions_table()
        initialize_default_settings()
        print("✅ Database migration completed successfully")
        return True
    except Exception as e:
        print(f"❌ Database migration failed: {e}")
        return False

def get_app_config():
    """Fetch all application configuration groups from the database as a dict."""
    try:
        engine = create_database_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT key, value FROM app_config"))
            rows = result.fetchall()
            config = {}
            for row in rows:
                key = row[0]
                value = row[1]
                # Ensure value is a dict if returned as string
                if isinstance(value, str):
                    try:
                        value = json.loads(value)
                    except Exception:
                        value = {}
                config[key] = value
            return config
    except Exception as e:
        print(f"Error fetching app config: {e}")
        return {}

def upsert_app_config(key: str, value_obj: dict, description: str | None = None, updated_by: str | None = None):
    """Insert or update a configuration group.

    Args:
        key: config group key, e.g. 'price_per_lb'.
        value_obj: JSON-serializable dict to store.
        description: optional text description.
        updated_by: optional username or identifier.
    """
    try:
        # Validate settings if they are grounding or consensus settings
        if key == "grounding_settings" and not validate_grounding_settings(value_obj):
            print(f"Invalid grounding settings: {value_obj}")
            return False
        elif key == "consensus_settings" and not validate_consensus_settings(value_obj):
            print(f"Invalid consensus settings: {value_obj}")
            return False
        
        engine = create_database_engine()
        with engine.connect() as conn:
            value_json = json.dumps(value_obj)
            
            if is_sqlite():
                # SQLite syntax - use INSERT OR REPLACE
                conn.execute(text(
                    """
                    INSERT OR REPLACE INTO app_config (key, value, description, updated_by, updated_at)
                    VALUES (:key, :value, :description, :updated_by, CURRENT_TIMESTAMP)
                    """
                ), {
                    "key": key,
                    "value": value_json,
                    "description": description,
                    "updated_by": updated_by,
                })
            else:
                # PostgreSQL syntax
                conn.execute(text(
                    """
                    INSERT INTO app_config (key, value, description, updated_by)
                    VALUES (:key, CAST(:value AS JSONB), :description, :updated_by)
                    ON CONFLICT (key) DO UPDATE SET
                        value = EXCLUDED.value,
                        description = COALESCE(EXCLUDED.description, app_config.description),
                        updated_at = CURRENT_TIMESTAMP,
                        updated_by = EXCLUDED.updated_by
                    """
                ), {
                    "key": key,
                    "value": value_json,
                    "description": description,
                    "updated_by": updated_by,
                })
            
            conn.commit()
            return True
    except Exception as e:
        print(f"Error upserting app config for key '{key}': {e}")
        return False

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