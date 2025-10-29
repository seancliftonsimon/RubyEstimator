"""Database helpers for deterministic resolver."""

from __future__ import annotations

import json
import os
from typing import Any, Dict

from pathlib import Path
from sqlalchemy import create_engine as _create_engine, text


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url

    host = os.getenv("PGHOST")
    port = os.getenv("PGPORT", "5432")
    database = os.getenv("PGDATABASE")
    username = os.getenv("PGUSER")
    password = os.getenv("PGPASSWORD")

    if all([host, database, username, password]):
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"

    project_root = Path(__file__).resolve().parent
    db_path = project_root / "rubyestimator_local.db"
    return f"sqlite:///{db_path.as_posix()}"


def is_sqlite() -> bool:
    return get_database_url().startswith("sqlite:")


def create_database_engine():
    return _create_engine(get_database_url(), echo=False)


def test_database_connection():
    try:
        engine = create_database_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "Database connection successful"
    except Exception as exc:  # pragma: no cover
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


