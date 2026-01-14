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
    """Context manager for database connections with improved error handling."""
    try:
        engine = create_database_engine()
        with engine.connect() as conn:
            yield conn
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}", exc_info=True)
        # Re-raise with more context
        raise ConnectionError(
            f"Unable to connect to database. Please check your DATABASE_URL configuration. "
            f"Original error: {str(e)}"
        ) from e


def ensure_schema() -> None:
    """Ensure database schema exists, creating tables if needed."""
    global _schema_validated
    
    # Skip if already validated in this session
    if _schema_validated:
        logger.debug("♻️  Schema already validated in this session, skipping check")
        return
    
    logger.info("📋 Ensuring database schema exists...")
    try:
        with _connect() as conn:
            logger.info("🗄️  Creating schema for PostgreSQL database")
            logger.debug("Creating PostgreSQL tables (if not exist) with JSONB support...")
            # --- Users (buyers) ---
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username TEXT NOT NULL UNIQUE,
                        display_name TEXT,
                        password_hash TEXT,
                        is_admin BOOLEAN NOT NULL DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)"))
            logger.debug("  ✓ users table ready")
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
            # Extend runs for multi-user usage + purchases (idempotent migrations)
            conn.execute(text("ALTER TABLE runs ADD COLUMN IF NOT EXISTS user_id INTEGER"))
            conn.execute(text("ALTER TABLE runs ADD COLUMN IF NOT EXISTS vehicle_key TEXT"))
            conn.execute(text("ALTER TABLE runs ADD COLUMN IF NOT EXISTS was_bought BOOLEAN NOT NULL DEFAULT FALSE"))
            conn.execute(text("ALTER TABLE runs ADD COLUMN IF NOT EXISTS purchase_price NUMERIC"))
            conn.execute(text("ALTER TABLE runs ADD COLUMN IF NOT EXISTS dispatch_number TEXT"))
            conn.execute(text("ALTER TABLE runs ADD COLUMN IF NOT EXISTS bought_at TIMESTAMP"))

            # Add FK constraint safely (PostgreSQL has no ADD CONSTRAINT IF NOT EXISTS)
            conn.execute(
                text(
                    """
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_constraint WHERE conname = 'fk_runs_user'
                        ) THEN
                            ALTER TABLE runs
                            ADD CONSTRAINT fk_runs_user
                            FOREIGN KEY (user_id) REFERENCES users(id);
                        END IF;
                    END $$;
                    """
                )
            )
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_runs_user_started_at ON runs(user_id, started_at DESC)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_runs_vehicle_key ON runs(vehicle_key)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_runs_bought_at ON runs(bought_at DESC)"))
            logger.debug("  ✓ runs columns/indexes for purchases/users ready")
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
                        source_hash TEXT NOT NULL,
                        fetched_at TIMESTAMP,
                        PRIMARY KEY (run_id, field, source_hash),
                        FOREIGN KEY (run_id) REFERENCES runs(run_id)
                    )
                    """
                )
            )
            logger.debug("  ✓ evidence table ready")
            # Migrate legacy evidence primary key (run_id, field) -> (run_id, field, source_hash)
            conn.execute(
                text(
                    """
                    DO $$
                    DECLARE
                        pk_cols text[];
                    BEGIN
                        SELECT array_agg(a.attname ORDER BY a.attnum)
                        INTO pk_cols
                        FROM pg_constraint c
                        JOIN pg_class t ON c.conrelid = t.oid
                        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY (c.conkey)
                        WHERE t.relname = 'evidence' AND c.contype = 'p';

                        IF pk_cols = ARRAY['run_id','field'] THEN
                            CREATE TABLE IF NOT EXISTS evidence_v2 (
                                run_id TEXT NOT NULL,
                                vehicle_key TEXT NOT NULL,
                                field TEXT NOT NULL,
                                value_json JSONB NOT NULL,
                                quote TEXT,
                                source_url TEXT,
                                source_hash TEXT NOT NULL,
                                fetched_at TIMESTAMP,
                                PRIMARY KEY (run_id, field, source_hash),
                                FOREIGN KEY (run_id) REFERENCES runs(run_id)
                            );

                            INSERT INTO evidence_v2 (run_id, vehicle_key, field, value_json, quote, source_url, source_hash, fetched_at)
                            SELECT
                                run_id,
                                vehicle_key,
                                field,
                                value_json,
                                quote,
                                source_url,
                                COALESCE(source_hash, md5(COALESCE(source_url, '') || '_' || COALESCE(quote, ''))),
                                fetched_at
                            FROM evidence
                            ON CONFLICT (run_id, field, source_hash) DO NOTHING;

                            DROP TABLE evidence;
                            ALTER TABLE evidence_v2 RENAME TO evidence;
                        END IF;
                    END $$;
                    """
                )
            )
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS cat_prices (
                        id SERIAL PRIMARY KEY,
                        vehicle_name TEXT NOT NULL UNIQUE,
                        cat_count INTEGER NOT NULL,
                        total_sale NUMERIC NOT NULL,
                        current_sale NUMERIC,
                        extra_cat_value NUMERIC,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            )
            conn.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS idx_cat_prices_vehicle_name ON cat_prices(vehicle_name)
                    """
                )
            )
            logger.debug("  ✓ cat_prices table ready")
            logger.info("✓ PostgreSQL (Neon) schema validated/created successfully")

            conn.commit()
            logger.info("✓ Schema commit completed")
            
            # Mark as validated for this session
            _schema_validated = True
    except ConnectionError:
        # Re-raise connection errors as-is (they already have good messages)
        raise
    except Exception as e:
        logger.error(f"❌ Failed to ensure database schema: {e}", exc_info=True)
        raise RuntimeError(
            f"Database schema initialization failed. Please check your database connection. "
            f"Original error: {str(e)}"
        ) from e


# NOTE: The single-call Gemini resolver handles its own persistence.
# This file now only provides schema management via ensure_schema().


