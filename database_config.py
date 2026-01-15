"""Database helpers for deterministic resolver."""

from __future__ import annotations

import json
import logging
import os
import socket
from typing import Any, Dict
from urllib.parse import urlparse

from sqlalchemy import create_engine as _create_engine, text

# Configure logging
logger = logging.getLogger(__name__)

# Engine cache for singleton pattern
_engine_cache = None
_database_url_cache = None  # Cache URL to prevent repeated logging


def get_database_url() -> str:
    """Get database URL from environment variables. Requires DATABASE_URL or PostgreSQL connection settings."""
    global _database_url_cache
    
    # Return cached URL if available
    if _database_url_cache is not None:
        return _database_url_cache
    
    url = os.getenv("DATABASE_URL")
    if url:
        # Mask password in log
        masked_url = _mask_password(url)
        logger.info(f"🔗 Using DATABASE_URL: {masked_url}")
        _database_url_cache = url
        return url

    host = os.getenv("PGHOST")
    port = os.getenv("PGPORT", "5432")
    database = os.getenv("PGDATABASE")
    username = os.getenv("PGUSER")
    password = os.getenv("PGPASSWORD")

    if all([host, database, username, password]):
        # Ensure SSL mode is set for cloud PostgreSQL providers (Neon, Supabase, etc.)
        # Check if URL already has query parameters
        url = f"postgresql://{username}:{password}@{host}:{port}/{database}"
        # Add sslmode=require if not already present (Neon and most cloud providers require SSL)
        if "sslmode=" not in url:
            url += "?sslmode=require"
        logger.info(f"🔗 Using PostgreSQL connection: {username}@{host}:{port}/{database}")
        _database_url_cache = url
        return url

    # No database configuration found - raise error
    error_msg = (
        "DATABASE_URL environment variable is required. "
        "Please set DATABASE_URL in your Streamlit Cloud secrets or environment variables. "
        "Example: DATABASE_URL=postgresql://user:pass@host.neon.tech/dbname?sslmode=require"
    )
    logger.error(f"❌ {error_msg}")
    raise ValueError(error_msg)


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


def _resolve_hostname_to_ipv4(hostname: str) -> str:
    """Resolve hostname to IPv4 address to avoid IPv6 connection issues."""
    try:
        # Get all address info for IPv4 only
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_INET, socket.SOCK_STREAM)
        if addr_info:
            # Return the first IPv4 address
            ipv4 = addr_info[0][4][0]
            logger.info(f"🔍 Resolved {hostname} to IPv4: {ipv4}")
            return ipv4
        else:
            logger.warning(f"⚠️  Could not resolve {hostname} to IPv4, using hostname")
            return None
    except (socket.gaierror, OSError) as e:
        logger.warning(f"⚠️  DNS resolution failed for {hostname}: {e}")
        return None


def _get_ipv4_connect_args(url: str) -> Dict[str, Any]:
    """
    Get connection args that force IPv4 connection using psycopg2's hostaddr parameter.
    This keeps the hostname in the URL for SSL certificate validation but connects via IPv4.
    """
    connect_args = {
        "connect_timeout": 10,  # 10 second connection timeout
    }
    
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        
        if not hostname:
            return connect_args
        
        # Check if hostname is already an IP address
        try:
            socket.inet_aton(hostname)
            # Already an IPv4 address, no need to resolve
            return connect_args
        except socket.error:
            pass
        
        # Resolve hostname to IPv4
        ipv4 = _resolve_hostname_to_ipv4(hostname)
        
        if ipv4:
            # Use hostaddr to force the IP address while keeping hostname for SSL
            connect_args["hostaddr"] = ipv4
            logger.info(f"🔄 Using hostaddr={ipv4} to force IPv4 connection (hostname: {hostname})")
        else:
            logger.warning(
                f"🚨 Hostname {hostname} could not be resolved to an IPv4 address. "
                "If this is a Supabase project, you likely need to use the Connection Pooler (port 6543) "
                "because direct connections (port 5432) are often IPv6-only, which Streamlit Cloud doesn't support."
            )
        
        return connect_args
    except Exception as e:
        logger.warning(f"⚠️  Failed to resolve IPv4 for connection: {e}")
        return connect_args


def is_sqlite() -> bool:
    """Always returns False - SQLite support has been removed. Only PostgreSQL/Neon is supported."""
    return False


def create_database_engine():
    """Create or return cached SQLAlchemy engine (singleton pattern)."""
    global _engine_cache
    
    # Return cached engine if available
    if _engine_cache is not None:
        logger.debug("♻️  Reusing cached database engine")
        return _engine_cache
    
    # Create new engine
    url = get_database_url()
    if not url.startswith("postgresql://"):
        error_msg = f"Invalid database URL. Only PostgreSQL connections are supported. URL starts with: {url[:10]}"
        logger.error(f"❌ {error_msg}")
        raise ValueError(error_msg)
    
    # Ensure SSL mode is set for cloud PostgreSQL providers
    if "sslmode=" not in url:
        # Check if there are already query parameters
        if "?" in url:
            url += "&sslmode=require"
        else:
            url += "?sslmode=require"
        logger.info("🔒 Added sslmode=require to database URL")

    # Clean up the URL: Remove pgbouncer=true which Supabase sometimes includes
    # but causes psycopg2 to fail with "invalid connection option"
    if "pgbouncer=true" in url:
        url = url.replace("pgbouncer=true", "")
        # Clean up any resulting double symbols
        while "&&" in url: url = url.replace("&&", "&")
        while "?&" in url: url = url.replace("?&", "?")
        while "??" in url: url = url.replace("??", "?")
        url = url.rstrip("?").rstrip("&")
        logger.info("🧹 Removed pgbouncer=true parameter (not supported by psycopg2)")
    
    # Get connection args with IPv4 resolution to avoid IPv6 issues
    connect_args = _get_ipv4_connect_args(url)
    
    logger.info(f"⚙️  Creating database engine for PostgreSQL")
    try:
        _engine_cache = _create_engine(
            url, 
            echo=False, 
            pool_pre_ping=True,
            connect_args=connect_args
        )
        logger.info(f"✓ Database engine created successfully (cached for reuse)")
        return _engine_cache
    except Exception as e:
        error_msg = (
            f"Failed to create database engine: {e}\n"
            f"Please verify:\n"
            f"1. DATABASE_URL is set correctly in your environment variables\n"
            f"2. The database server is accessible from your network\n"
            f"3. SSL mode is configured (sslmode=require for Neon)\n"
            f"4. Database credentials are correct"
        )
        logger.error(f"❌ {error_msg}", exc_info=True)
        raise ConnectionError(error_msg) from e


def clear_engine_cache():
    """Clear the cached database engine. Useful for testing or reconnection."""
    global _engine_cache, _database_url_cache
    if _engine_cache is not None:
        logger.info("🔄 Clearing cached database engine")
        _engine_cache.dispose()
        _engine_cache = None
    _database_url_cache = None  # Also clear URL cache


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


