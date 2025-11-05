"""Database persistence layer - schema management for single-call system."""

from __future__ import annotations

import logging
from contextlib import contextmanager

from sqlalchemy import text

from database_config import create_database_engine

# Configure logging
logger = logging.getLogger(__name__)

# Schema validation cache to prevent redundant checks
_schema_validated = False


@contextmanager
def _connect():
    engine = create_database_engine()
    with engine.connect() as conn:
        yield conn


def ensure_schema() -> None:
    """Ensure database schema exists, creating tables if needed."""
    global _schema_validated
    
    # Skip if already validated in this session
    if _schema_validated:
        logger.debug("♻️  Schema already validated in this session, skipping check")
        return
    
    logger.info("📋 Ensuring database schema exists...")
    with _connect() as conn:
        logger.info("🗄️  Creating schema for PostgreSQL database")
        logger.debug("Creating PostgreSQL tables (if not exist) with JSONB support...")
        conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS vehicles (
                        vehicle_key TEXT PRIMARY KEY,
                        year INTEGER NOT NULL,
                        make TEXT NOT NULL,
                        model TEXT NOT NULL,
                        aliases_applied JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            )
            logger.debug("  ✓ vehicles table ready")
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS ref_makes (
                        id SERIAL PRIMARY KEY,
                        name TEXT NOT NULL UNIQUE,
                        name_norm TEXT NOT NULL UNIQUE,
                        aliases_json JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            )
            conn.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS idx_ref_makes_name_norm ON ref_makes(name_norm)
                    """
                )
            )
            logger.debug("  ✓ ref_makes table ready")
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS ref_models (
                        id SERIAL PRIMARY KEY,
                        make_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        name_norm TEXT NOT NULL,
                        aliases_json JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (make_id) REFERENCES ref_makes(id) ON DELETE CASCADE,
                        UNIQUE(make_id, name_norm)
                    )
                    """
                )
            )
            conn.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS idx_ref_models_make_id_name_norm ON ref_models(make_id, name_norm)
                    """
                )
            )
            logger.debug("  ✓ ref_models table ready")
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS ref_aliases (
                        alias_norm TEXT NOT NULL,
                        target_type TEXT NOT NULL,
                        target_id INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (alias_norm, target_type)
                    )
                    """
                )
            )
            conn.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS idx_ref_aliases_norm_type ON ref_aliases(alias_norm, target_type)
                    """
                )
            )
            logger.debug("  ✓ ref_aliases table ready")
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS field_values (
                        vehicle_key TEXT NOT NULL,
                        field TEXT NOT NULL,
                        value_json JSONB NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (vehicle_key, field),
                        FOREIGN KEY (vehicle_key) REFERENCES vehicles(vehicle_key)
                    )
                    """
                )
            )
            logger.debug("  ✓ field_values table ready")
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS runs (
                        run_id TEXT PRIMARY KEY,
                        started_at TIMESTAMP NOT NULL,
                        finished_at TIMESTAMP,
                        total_ms INTEGER,
                        status TEXT,
                        timings_json JSONB
                    )
                    """
                )
            )
            logger.debug("  ✓ runs table ready")
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS evidence (
                        run_id TEXT NOT NULL,
                        vehicle_key TEXT NOT NULL,
                        field TEXT NOT NULL,
                        value_json JSONB NOT NULL,
                        quote TEXT,
                        source_url TEXT,
                        source_hash TEXT,
                        fetched_at TIMESTAMP,
                        PRIMARY KEY (run_id, field),
                        FOREIGN KEY (run_id) REFERENCES runs(run_id)
                    )
                    """
                )
            )
            logger.debug("  ✓ evidence table ready")
            logger.info("✓ PostgreSQL (Neon) schema validated/created successfully")

        conn.commit()
        logger.info("✓ Schema commit completed")
        
        # Mark as validated for this session
        _schema_validated = True


# NOTE: The single-call Gemini resolver handles its own persistence.
# This file now only provides schema management via ensure_schema().


