"""Database persistence layer - schema management for single-call system."""

from __future__ import annotations

from contextlib import contextmanager
from typing import List

from sqlalchemy import text

from database_config import create_database_engine, is_sqlite


@contextmanager
def _connect():
    engine = create_database_engine()
    with engine.connect() as conn:
        yield conn


def ensure_schema() -> None:
    with _connect() as conn:
        if is_sqlite():
            _ensure_sqlite_schema(conn)
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
        else:
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

        conn.commit()


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
    ]

    for table_name, required_columns in drop_targets:
        if table_exists(table_name) and not has_required_columns(table_name, required_columns):
            conn.execute(text(f"DROP TABLE {table_name}"))


# NOTE: The single-call Gemini resolver handles its own persistence.
# This file now only provides schema management via ensure_schema().


