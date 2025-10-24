import os
import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import streamlit as st
import json

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