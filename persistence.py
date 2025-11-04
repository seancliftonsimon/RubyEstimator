"""Database persistence layer - schema management for single-call system."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import List

from sqlalchemy import text

from database_config import create_database_engine, is_sqlite

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
        db_type = "SQLite" if is_sqlite() else "PostgreSQL"
        logger.info(f"🗄️  Creating schema for {db_type} database")
        
        if is_sqlite():
            logger.debug("Running SQLite schema validation...")
            _ensure_sqlite_schema(conn)
            logger.debug("Creating SQLite tables (if not exist)...")
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS vehicles (
                        vehicle_key TEXT PRIMARY KEY,
                        year INTEGER NOT NULL,
                        make TEXT NOT NULL,
                        model TEXT NOT NULL,
                        aliases_applied TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            )
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS ref_makes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        name_norm TEXT NOT NULL UNIQUE,
                        aliases_json TEXT,
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
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS ref_models (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        make_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        name_norm TEXT NOT NULL,
                        aliases_json TEXT,
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
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS field_values (
                        vehicle_key TEXT NOT NULL,
                        field TEXT NOT NULL,
                        value_json TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (vehicle_key, field),
                        FOREIGN KEY (vehicle_key) REFERENCES vehicles(vehicle_key)
                    )
                    """
                )
            )
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS runs (
                        run_id TEXT PRIMARY KEY,
                        started_at TIMESTAMP NOT NULL,
                        finished_at TIMESTAMP,
                        total_ms INTEGER,
                        status TEXT,
                        timings_json TEXT
                    )
                    """
                )
            )
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS evidence (
                        run_id TEXT NOT NULL,
                        vehicle_key TEXT NOT NULL,
                        field TEXT NOT NULL,
                        value_json TEXT NOT NULL,
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
            logger.info("✓ SQLite schema validated/created successfully")
        else:
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


def _ensure_sqlite_schema(conn) -> None:
    def table_exists(name: str) -> bool:
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
            {"name": name},
        ).fetchone()
        return result is not None

    def has_required_columns(name: str, required: List[str]) -> bool:
        info = conn.execute(text(f"PRAGMA table_info('{name}')")).fetchall()
        columns = {row[1] for row in info}
        return all(column in columns for column in required)

    drop_targets = [
        ("vehicles", ["vehicle_key", "year", "make", "model", "aliases_applied"]),
        ("field_values", ["vehicle_key", "field", "value_json"]),
        ("runs", ["run_id", "started_at", "status"]),
        ("evidence", ["run_id", "vehicle_key", "field", "value_json", "source_hash"]),
        ("ref_makes", ["id", "name", "name_norm", "aliases_json"]),
        ("ref_models", ["id", "make_id", "name", "name_norm", "aliases_json"]),
        ("ref_aliases", ["alias_norm", "target_type", "target_id"]),
    ]

    for table_name, required_columns in drop_targets:
        if table_exists(table_name) and not has_required_columns(table_name, required_columns):
            conn.execute(text(f"DROP TABLE {table_name}"))


# NOTE: The single-call Gemini resolver handles its own persistence.
# This file now only provides schema management via ensure_schema().


