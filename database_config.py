"""Database helpers for deterministic resolver."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict

from pathlib import Path
from sqlalchemy import create_engine as _create_engine, text

# Configure logging
logger = logging.getLogger(__name__)


def get_database_url() -> str:
    """Get database URL from environment or fallback to SQLite."""
    url = os.getenv("DATABASE_URL")
    if url:
        # Mask password in log
        masked_url = _mask_password(url)
        logger.info(f"🔗 Using DATABASE_URL: {masked_url}")
        return url

    host = os.getenv("PGHOST")
    port = os.getenv("PGPORT", "5432")
    database = os.getenv("PGDATABASE")
    username = os.getenv("PGUSER")
    password = os.getenv("PGPASSWORD")

    if all([host, database, username, password]):
        logger.info(f"🔗 Using PostgreSQL connection: {username}@{host}:{port}/{database}")
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"

    project_root = Path(__file__).resolve().parent
    db_path = project_root / "rubyestimator_local.db"
    logger.info(f"🔗 Using SQLite database: {db_path}")
    return f"sqlite:///{db_path.as_posix()}"


def _mask_password(url: str) -> str:
    """Mask password in database URL for logging."""
    if "://" not in url:
        return url
    protocol, rest = url.split("://", 1)
    if "@" not in rest:
        return url
    credentials, host_part = rest.split("@", 1)
    if ":" in credentials:
        username, _ = credentials.split(":", 1)
        return f"{protocol}://{username}:****@{host_part}"
    return url


def is_sqlite() -> bool:
    return get_database_url().startswith("sqlite:")


def create_database_engine():
    """Create SQLAlchemy engine with connection logging."""
    url = get_database_url()
    db_type = "PostgreSQL (Neon)" if url.startswith("postgresql://") else "SQLite"
    logger.info(f"⚙️  Creating database engine for {db_type}")
    try:
        engine = _create_engine(url, echo=False)
        logger.info(f"✓ Database engine created successfully")
        return engine
    except Exception as e:
        logger.error(f"❌ Failed to create database engine: {e}", exc_info=True)
        raise


def test_database_connection():
    """Test database connection with detailed logging."""
    logger.info("🔍 Testing database connection...")
    try:
        engine = create_database_engine()
        logger.info("📡 Attempting to connect to database...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info(f"✓ Database connection test successful! Query returned: {result.fetchone()}")
        return True, "Database connection successful"
    except Exception as exc:  # pragma: no cover
        logger.error(f"❌ Database connection test failed: {exc}", exc_info=True)
        return False, f"Database connection failed: {exc}"


def get_database_info() -> Dict[str, Any]:
    return {
        "DATABASE_URL": os.getenv("DATABASE_URL", "Not set"),
        "PGHOST": os.getenv("PGHOST", "Not set"),
        "PGPORT": os.getenv("PGPORT", "Not set"),
        "PGDATABASE": os.getenv("PGDATABASE", "Not set"),
        "PGUSER": os.getenv("PGUSER", "Not set"),
        "PGPASSWORD": "Set" if os.getenv("PGPASSWORD") else "Not set",
    }


def get_app_config() -> Dict[str, Any]:
    engine = create_database_engine()
    with engine.connect() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS app_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by TEXT
                )
                """
            )
        )
        rows = conn.execute(text("SELECT key, value FROM app_config")).fetchall()

    config: Dict[str, Any] = {}
    for key, value in rows:
        if isinstance(value, str):
            try:
                config[key] = json.loads(value)
            except json.JSONDecodeError:
                config[key] = {}
        else:
            config[key] = value or {}
    return config


def upsert_app_config(key: str, value_obj: dict, description: str | None = None, updated_by: str | None = None) -> bool:
    engine = create_database_engine()
    with engine.connect() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS app_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO app_config (key, value, description, updated_by, updated_at)
                VALUES (:key, :value, :description, :updated_by, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET
                    value = EXCLUDED.value,
                    description = COALESCE(EXCLUDED.description, app_config.description),
                    updated_by = EXCLUDED.updated_by,
                    updated_at = CURRENT_TIMESTAMP
                """
            ),
            {
                "key": key,
                "value": json.dumps(value_obj),
                "description": description,
                "updated_by": updated_by,
            },
        )
        conn.commit()
    return True


