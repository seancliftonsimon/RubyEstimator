"""Integration layer between Streamlit UI and vehicle resolver."""

from __future__ import annotations

import json
import logging
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st
from sqlalchemy import text

from database_config import create_database_engine, get_app_config, upsert_app_config
from persistence import ensure_schema
from single_call_gemini_resolver import single_call_resolver

# Configure logging with forced console output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    force=True
)
logger = logging.getLogger(__name__)


def process_vehicle(year: int, make: str, model: str, progress_callback=None) -> Dict[str, Any]:
    """Resolve vehicle specifications using single-call Gemini with Search Grounding."""
    logger.info(f"🔍 Processing vehicle request: {year} {make} {model}")
    
    if progress_callback:
        progress_callback("searching", None, "Searching with Gemini + Google Search")

    try:
        resolution = single_call_resolver.resolve_vehicle(year, make, model)
        logger.info(f"✓ Vehicle resolution completed successfully for {year} {make} {model}")
        logger.debug(f"Resolution run_id: {resolution.run_id}, latency: {resolution.latency_ms:.2f}ms")
    except Exception as exc:
        logger.error(f"❌ Vehicle resolution failed for {year} {make} {model}: {exc}", exc_info=True)
        error_dict = {
            "vehicle_key": None,
            "error": str(exc),
            "curb_weight_lbs": None,
            "aluminum_engine": None,
            "aluminum_rims": None,
            "catalytic_converters": None,
            "warnings": [str(exc)],
            "missing_fields": {},
            "timings": {},
        }
        logger.debug(f"Returning error dict: {error_dict}")
        return error_dict

    fields = resolution.fields
    
    # Log field resolution status
    for field_name, field_data in fields.items():
        status = field_data.get("status", "unknown")
        value = field_data.get("value")
        confidence = field_data.get("confidence", 0.0)
        logger.debug(f"  Field '{field_name}': status={status}, value={value}, confidence={confidence:.2f}")
    
    output = {
        "vehicle_key": resolution.vehicle_key,
        "aliases_applied": [],
        "curb_weight_lbs": fields.get("curb_weight", {}).get("value"),
        "aluminum_engine": fields.get("aluminum_engine", {}).get("value"),
        "aluminum_rims": fields.get("aluminum_rims", {}).get("value"),
        "catalytic_converters": fields.get("catalytic_converters", {}).get("value"),
        "warnings": [],
        "missing_fields": {
            field: "not_found" 
            for field, data in fields.items() 
            if data.get("status") == "not_found"
        },
        "timings": {"total_ms": resolution.latency_ms},
        "run_id": resolution.run_id,
    }
    
    # Log missing fields
    if output["missing_fields"]:
        logger.warning(f"⚠️ Missing fields for {year} {make} {model}: {list(output['missing_fields'].keys())}")
    else:
        logger.info(f"✓ All fields found for {year} {make} {model}")

    # Attach per-field confidence metadata for downstream displays
    output["confidence_scores"] = {
        field: data.get("confidence", 0.0) for field, data in fields.items()
    }
    output["source_attribution"] = {
        field: "gemini_search_grounding" for field in fields
    }
    
    # Add citations for provenance display
    output["citations"] = {
        field: data.get("citations", []) for field, data in fields.items()
    }
    
    # Log citation counts
    citation_counts = {field: len(cites) for field, cites in output["citations"].items()}
    logger.debug(f"Citation counts: {citation_counts}")

    if progress_callback:
        progress_callback("complete", None, "done", None, None)

    logger.info(f"✓ Returning output for {year} {make} {model} (run_id: {output['run_id']})")
    return output


def get_last_ten_entries() -> pd.DataFrame:
    """Return the ten most recently updated vehicles with resolved fields."""
    ensure_schema()
    engine = create_database_engine()
    query = text(
        """
        SELECT v.year, v.make, v.model,
               fv.field,
               fv.value_json,
               v.updated_at
        FROM vehicles v
        LEFT JOIN field_values fv ON fv.vehicle_key = v.vehicle_key
        ORDER BY v.updated_at DESC, fv.updated_at DESC
        LIMIT 40
        """
    )

    with engine.connect() as conn:
        rows = conn.execute(query).fetchall()

    if not rows:
        return pd.DataFrame(columns=[
            "year",
            "make",
            "model",
            "curb_weight_lbs",
            "aluminum_engine",
            "aluminum_rims",
            "catalytic_converters",
        ])

    records: Dict[tuple, Dict[str, Any]] = {}
    for year, make, model, field, value_json, updated_at in rows:
        key = (year, make, model)
        if key not in records:
            records[key] = {
                "year": year,
                "make": make,
                "model": model,
                "curb_weight_lbs": None,
                "aluminum_engine": None,
                "aluminum_rims": None,
                "catalytic_converters": None,
                "updated_at": updated_at,
            }

        if not field or not value_json:
            continue

        try:
            value_dict = json.loads(value_json) if isinstance(value_json, str) else value_json
        except Exception:
            continue

        value = value_dict.get("value")
        if field == "curb_weight":
            records[key]["curb_weight_lbs"] = value
        elif field == "aluminum_engine":
            records[key]["aluminum_engine"] = value
        elif field == "aluminum_rims":
            records[key]["aluminum_rims"] = value
        elif field == "catalytic_converters":
            records[key]["catalytic_converters"] = value

    df = pd.DataFrame(records.values())
    if "updated_at" in df.columns:
        df = df.sort_values("updated_at", ascending=False)
        df = df.drop(columns=["updated_at"])
    return df


# --- Reference Catalog Functions ---

def normalize_catalog_string(s: str) -> Dict[str, str]:
    """
    Normalize a catalog string for consistent storage and lookup.

    Applies title case for display, normalized lowercase for keys.
    Uses similar logic to sanitize_input() from app.py.

    Args:
        s: Input string to normalize

    Returns:
        Dict with 'display' (Title Case) and 'norm' (lowercase, single spaces) keys
    """
    if s is None:
        return {"display": "", "norm": ""}

    # Convert to string if not already
    s = str(s)

    # Strip leading/trailing whitespace
    s = s.strip()

    # Replace multiple spaces with single space
    import re
    s = re.sub(r'\s+', ' ', s)

    # Remove non-printable characters
    s = ''.join(char for char in s if char.isprintable())

    # Create display version (Title Case)
    display = s.title()

    # Create normalized version (lowercase, single spaces)
    norm = s.lower()

    return {"display": display, "norm": norm}


def bump_catalog_version() -> bool:
    """Update the reference catalog version in app_config to trigger cache invalidation."""
    try:
        version = int(time.time() * 1000)  # millisecond timestamp
        success = upsert_app_config(
            "reference_catalog_version",
            version,
            "Reference catalog version for cache invalidation",
            "system"
        )
        if success:
            logger.info(f"✓ Bumped catalog version to {version}")
        return success
    except Exception as e:
        logger.error(f"❌ Failed to bump catalog version: {e}")
        return False


def import_catalog_from_json(json_data: Dict[str, Any]) -> bool:
    """
    Import reference catalog from JSON data.

    Parses makes and models, upserts to database, rebuilds aliases, bumps version.

    Args:
        json_data: JSON data with "makes" array containing make objects

    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("📥 Starting catalog import from JSON")

    try:
        ensure_schema()
        engine = create_database_engine()

        with engine.connect() as conn:
            # Clear existing data
            conn.execute(text("DELETE FROM ref_aliases"))
            conn.execute(text("DELETE FROM ref_models"))
            conn.execute(text("DELETE FROM ref_makes"))
            logger.info("✓ Cleared existing catalog data")

            # Import makes and models
            for make_data in json_data.get("makes", []):
                make_name = make_data["make"]
                make_norm = normalize_catalog_string(make_name)
                aliases = make_data.get("aliases", [])

                # Insert make
                make_result = conn.execute(
                    text("""
                        INSERT INTO ref_makes (name, name_norm, aliases_json)
                        VALUES (:name, :name_norm, :aliases_json)
                        RETURNING id
                    """),
                    {
                        "name": make_norm["display"],
                        "name_norm": make_norm["norm"],
                        "aliases_json": json.dumps(aliases)
                    }
                )
                make_id = make_result.fetchone()[0]
                logger.info(f"✓ Imported make: {make_name} (ID: {make_id})")

                # Insert models for this make
                for model_data in make_data.get("models", []):
                    model_name = model_data["name"]
                    model_norm = normalize_catalog_string(model_name)
                    model_aliases = model_data.get("aliases", [])

                    conn.execute(
                        text("""
                            INSERT INTO ref_models (make_id, name, name_norm, aliases_json)
                            VALUES (:make_id, :name, :name_norm, :aliases_json)
                        """),
                        {
                            "make_id": make_id,
                            "name": model_norm["display"],
                            "name_norm": model_norm["norm"],
                            "aliases_json": json.dumps(model_aliases)
                        }
                    )
                    logger.info(f"  ✓ Imported model: {model_name}")

            # Rebuild aliases table
            if not rebuild_alias_table():
                logger.error("❌ Failed to rebuild aliases table")
                return False

            # Bump version
            if not bump_catalog_version():
                logger.error("❌ Failed to bump catalog version")
                return False

            conn.commit()
            logger.info("✓ Catalog import completed successfully")
            return True

    except Exception as e:
        logger.error(f"❌ Catalog import failed: {e}", exc_info=True)
        return False


def export_catalog_to_json() -> Dict[str, Any]:
    """
    Export complete reference catalog to JSON format.

    Returns:
        Dict: JSON-serializable catalog data
    """
    logger.info("📤 Exporting catalog to JSON")

    try:
        from database_config import is_sqlite
        ensure_schema()
        engine = create_database_engine()

        with engine.connect() as conn:
            if is_sqlite():
                # SQLite version - use simpler queries
                makes_result = conn.execute(
                    text("""
                        SELECT m.id, m.name, m.aliases_json
                        FROM ref_makes m
                        ORDER BY m.name
                    """)
                )

                makes = []
                for make_row in makes_result:
                    make_id, make_name, make_aliases_json = make_row

                    make_data = {
                        "make": make_name,
                        "aliases": json.loads(make_aliases_json) if make_aliases_json else [],
                        "models": []
                    }

                    # Get models for this make
                    models_result = conn.execute(
                        text("""
                            SELECT name, aliases_json
                            FROM ref_models
                            WHERE make_id = ?
                            ORDER BY name
                        """),
                        (make_id,)
                    )

                    for model_row in models_result:
                        model_name, model_aliases_json = model_row
                        model_data = {
                            "name": model_name,
                            "aliases": json.loads(model_aliases_json) if model_aliases_json else []
                        }
                        make_data["models"].append(model_data)

                    makes.append(make_data)
            else:
                # PostgreSQL version with JSON functions
                makes_result = conn.execute(
                    text("""
                        SELECT m.id, m.name, m.aliases_json,
                               json_agg(
                                   json_build_object(
                                       'name', md.name,
                                       'aliases', md.aliases_json::json
                                   )
                               ) as models
                        FROM ref_makes m
                        LEFT JOIN ref_models md ON md.make_id = m.id
                        GROUP BY m.id, m.name, m.aliases_json
                        ORDER BY m.name
                    """)
                )

                makes = []
                for row in makes_result:
                    make_data = {
                        "make": row[1],  # name
                        "aliases": json.loads(row[2]) if row[2] else [],  # aliases_json
                        "models": []
                    }

                    # Process models
                    if row[3]:  # models JSON array
                        for model_json in row[3]:
                            if model_json:  # Skip null models
                                model_data = {
                                    "name": model_json["name"],
                                    "aliases": model_json["aliases"] if model_json["aliases"] else []
                                }
                                make_data["models"].append(model_data)

                    makes.append(make_data)

            result = {"makes": makes}
            logger.info(f"✓ Exported {len(makes)} makes")
            return result

    except Exception as e:
        logger.error(f"❌ Catalog export failed: {e}", exc_info=True)
        return {"makes": []}


def rebuild_alias_table() -> bool:
    """
    Clear and rebuild the ref_aliases table from make and model aliases.

    This creates fast lookup mappings for fuzzy matching.

    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("🔄 Rebuilding alias table")

    try:
        from database_config import is_sqlite
        ensure_schema()
        engine = create_database_engine()

        with engine.connect() as conn:
            # Clear existing aliases
            conn.execute(text("DELETE FROM ref_aliases"))

            if is_sqlite():
                # SQLite version - process aliases manually
                # Process make aliases
                makes_result = conn.execute(
                    text("SELECT id, aliases_json FROM ref_makes WHERE aliases_json IS NOT NULL AND aliases_json != ''")
                )

                for make_row in makes_result:
                    make_id, aliases_json = make_row
                    try:
                        aliases = json.loads(aliases_json)
                        for alias in aliases:
                            if alias and alias.strip():
                                conn.execute(
                                    text("""
                                        INSERT INTO ref_aliases (alias_norm, target_type, target_id)
                                        VALUES (?, 'make', ?)
                                    """),
                                    (alias.strip().lower(), make_id)
                                )
                    except json.JSONDecodeError:
                        continue

                # Process model aliases
                models_result = conn.execute(
                    text("SELECT id, aliases_json FROM ref_models WHERE aliases_json IS NOT NULL AND aliases_json != ''")
                )

                for model_row in models_result:
                    model_id, aliases_json = model_row
                    try:
                        aliases = json.loads(aliases_json)
                        for alias in aliases:
                            if alias and alias.strip():
                                conn.execute(
                                    text("""
                                        INSERT INTO ref_aliases (alias_norm, target_type, target_id)
                                        VALUES (?, 'model', ?)
                                    """),
                                    (alias.strip().lower(), model_id)
                                )
                    except json.JSONDecodeError:
                        continue
            else:
                # PostgreSQL version with JSON functions
                # Insert make aliases
                conn.execute(
                    text("""
                        INSERT INTO ref_aliases (alias_norm, target_type, target_id)
                        SELECT
                            LOWER(TRIM(value)) as alias_norm,
                            'make' as target_type,
                            id as target_id
                        FROM ref_makes,
                        json_array_elements_text(
                            CASE WHEN aliases_json IS NULL OR aliases_json = '' THEN '[]'::json
                                 ELSE aliases_json::json END
                        ) as value
                        WHERE TRIM(value) != ''
                    """)
                )

                # Insert model aliases
                conn.execute(
                    text("""
                        INSERT INTO ref_aliases (alias_norm, target_type, target_id)
                        SELECT
                            LOWER(TRIM(value)) as alias_norm,
                            'model' as target_type,
                            id as target_id
                        FROM ref_models,
                        json_array_elements_text(
                            CASE WHEN aliases_json IS NULL OR aliases_json = '' THEN '[]'::json
                                 ELSE aliases_json::json END
                        ) as value
                        WHERE TRIM(value) != ''
                    """)
                )

            conn.commit()
            logger.info("✓ Alias table rebuilt successfully")
            return True

    except Exception as e:
        logger.error(f"❌ Failed to rebuild alias table: {e}", exc_info=True)
        return False


# --- Reference Catalog Caching & Indices ---

@st.cache_data(show_spinner=False)
def get_catalog_version() -> int:
    """
    Get the current reference catalog version from app_config.

    Returns:
        int: Version timestamp (0 if not set)
    """
    try:
        config = get_app_config()
        return config.get("reference_catalog_version", 0)
    except Exception:
        return 0


def load_reference_catalog() -> Dict[str, Any]:
    """
    Load and build the complete reference catalog cache structure from JSON file.

    Returns:
        Dict: Cached catalog data with indices
    """
    logger.info("🔄 Loading reference catalog into cache from JSON file")

    try:
        import os

        # Load from seed_catalog.json file
        seed_file = os.path.join(os.path.dirname(__file__), 'seed_catalog.json')
        if not os.path.exists(seed_file):
            logger.error(f"❌ seed_catalog.json not found at {seed_file}")
            return {
                "ref_version": 0,
                "make_index": {
                    "all_makes": [],
                    "make_by_norm": {},
                    "make_alias_to_canonical": {}
                },
                "model_index_by_make": {}
            }

        with open(seed_file, 'r') as f:
            json_data = json.load(f)

        cache_data = {
            "ref_version": 1,  # Static version for JSON file
            "make_index": {
                "all_makes": [],
                "make_by_norm": {},
                "make_alias_to_canonical": {}
            },
            "model_index_by_make": {}
        }

        # Process makes and models from JSON
        for make_data in json_data.get("makes", []):
            make_name = make_data["make"]
            make_norm_data = normalize_catalog_string(make_name)
            aliases = make_data.get("aliases", [])

            # Add to all_makes list
            cache_data["make_index"]["all_makes"].append(make_name)

            # Add to make_by_norm dict
            cache_data["make_index"]["make_by_norm"][make_norm_data["norm"]] = {
                "id": len(cache_data["make_index"]["all_makes"]),  # Use index as ID
                "name": make_name,
                "aliases": aliases
            }

            # Add aliases to alias map
            for alias in aliases:
                if alias and alias.strip():
                    norm_alias = alias.strip().lower()
                    cache_data["make_index"]["make_alias_to_canonical"][norm_alias] = make_name

            # Initialize model index for this make
            cache_data["model_index_by_make"][make_name] = {
                "all_models": [],
                "model_by_norm": {},
                "alias_to_canonical": {}
            }

            # Process models for this make
            for model_data in make_data.get("models", []):
                model_name = model_data["name"]
                model_norm_data = normalize_catalog_string(model_name)
                model_aliases = model_data.get("aliases", [])

                make_models = cache_data["model_index_by_make"][make_name]

                # Add to all_models list
                make_models["all_models"].append(model_name)

                # Add to model_by_norm dict
                make_models["model_by_norm"][model_norm_data["norm"]] = {
                    "id": len(make_models["all_models"]),  # Use index as ID
                    "name": model_name,
                    "aliases": model_aliases
                }

                # Add aliases to alias map
                for alias in model_aliases:
                    if alias and alias.strip():
                        norm_alias = alias.strip().lower()
                        make_models["alias_to_canonical"][norm_alias] = model_name

        logger.info(f"✅ Loaded {len(cache_data['make_index']['all_makes'])} makes from JSON catalog")
        return cache_data

    except Exception as e:
        logger.error(f"❌ Error loading reference catalog from JSON: {e}", exc_info=True)
        # Return empty cache on error
        return {
            "ref_version": 0,
            "make_index": {
                "all_makes": [],
                "make_by_norm": {},
                "make_alias_to_canonical": {}
            },
            "model_index_by_make": {}
        }


def ensure_catalog_cached() -> Dict[str, Any]:
    """
    Ensure the catalog cache is loaded and current.

    Checks version against DB and reloads if needed.

    Returns:
        Dict: Current cached catalog data
    """
    try:
        current_version = get_catalog_version()
        cached_version = st.session_state.get("ref_version", 0)

        if current_version != cached_version or "make_index" not in st.session_state:
            logger.info(f"🔄 Cache version mismatch ({cached_version} vs {current_version}), reloading")
            cache_data = load_reference_catalog()
            st.session_state.update(cache_data)
            return cache_data
        else:
            # Return cached data from session state
            return {
                "ref_version": st.session_state.get("ref_version"),
                "make_index": st.session_state.get("make_index", {}),
                "model_index_by_make": st.session_state.get("model_index_by_make", {})
            }

    except Exception as e:
        logger.error(f"❌ Error ensuring catalog cache: {e}", exc_info=True)
        # Return empty cache on error
        return {
            "ref_version": 0,
            "make_index": {
                "all_makes": [],
                "make_by_norm": {},
                "make_alias_to_canonical": {}
            },
            "model_index_by_make": {}
        }


def invalidate_catalog_cache() -> bool:
    """
    Invalidate the catalog cache by bumping version and clearing session state.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Bump version in DB
        if not bump_catalog_version():
            logger.error("❌ Failed to bump catalog version during invalidation")
            return False

        # Clear cache from session state
        keys_to_clear = ["ref_version", "make_index", "model_index_by_make"]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]

        # Clear the cached function
        load_reference_catalog.clear()

        logger.info("✓ Catalog cache invalidated")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to invalidate catalog cache: {e}", exc_info=True)
        return False


def get_all_makes() -> List[str]:
    """
    Get list of all canonical make names.

    Returns:
        List[str]: Sorted list of make names
    """
    cache = ensure_catalog_cached()
    return cache["make_index"]["all_makes"]


def get_models_for_make(make_name: str) -> List[str]:
    """
    Get list of all model names for a given make.

    Args:
        make_name: Canonical make name

    Returns:
        List[str]: Sorted list of model names for the make
    """
    cache = ensure_catalog_cached()
    make_data = cache["model_index_by_make"].get(make_name, {})
    return make_data.get("all_models", [])


def get_catalog_stats() -> Dict[str, int]:
    """
    Get basic statistics about the reference catalog.

    Returns:
        Dict: Statistics with makes, models, aliases counts
    """
    try:
        ensure_schema()
        engine = create_database_engine()

        with engine.connect() as conn:
            # Count makes
            makes_count = conn.execute(text("SELECT COUNT(*) FROM ref_makes")).fetchone()[0]

            # Count models
            models_count = conn.execute(text("SELECT COUNT(*) FROM ref_models")).fetchone()[0]

            # Count aliases
            aliases_count = conn.execute(text("SELECT COUNT(*) FROM ref_aliases")).fetchone()[0]

            return {
                "makes": makes_count,
                "models": models_count,
                "aliases": aliases_count
            }

    except Exception as e:
        logger.error(f"❌ Failed to get catalog stats: {e}", exc_info=True)
        return {"makes": 0, "models": 0, "aliases": 0}


# --- Fuzzy Matching Functions ---

def suggest_make(raw_input: str, threshold: int = 80) -> Optional[str]:
    """
    Suggest a canonical make name based on fuzzy matching against makes and aliases.

    Args:
        raw_input: Raw user input for make
        threshold: Minimum similarity score (0-100)

    Returns:
        Optional[str]: Best matching canonical make name, or None if no good match
    """
    try:
        from rapidfuzz import fuzz

        if not raw_input or not raw_input.strip():
            return None

        input_norm = raw_input.strip().lower()
        cache = ensure_catalog_cached()

        best_match = None
        best_score = 0

        # Check canonical makes first
        for make_name in cache["make_index"]["all_makes"]:
            score = fuzz.ratio(input_norm, make_name.lower())
            if score >= threshold and score > best_score:
                best_score = score
                best_match = make_name

        # Check aliases
        for alias_norm, canonical_make in cache["make_index"]["make_alias_to_canonical"].items():
            score = fuzz.ratio(input_norm, alias_norm)
            if score >= threshold and score > best_score:
                best_score = score
                best_match = canonical_make

        return best_match if best_score >= threshold else None

    except ImportError:
        logger.warning("rapidfuzz not available, fuzzy matching disabled")
        return None
    except Exception as e:
        logger.error(f"❌ Error in suggest_make: {e}", exc_info=True)
        return None


def suggest_model(make: str, raw_input: str, threshold: int = 80) -> Optional[str]:
    """
    Suggest a canonical model name based on fuzzy matching within a specific make.

    Args:
        make: Canonical make name to search within
        raw_input: Raw user input for model
        threshold: Minimum similarity score (0-100)

    Returns:
        Optional[str]: Best matching canonical model name, or None if no good match
    """
    try:
        from rapidfuzz import fuzz

        if not raw_input or not raw_input.strip() or not make:
            return None

        input_norm = raw_input.strip().lower()
        cache = ensure_catalog_cached()

        make_data = cache["model_index_by_make"].get(make)
        if not make_data:
            return None

        best_match = None
        best_score = 0

        # Check canonical models for this make
        for model_name in make_data["all_models"]:
            score = fuzz.ratio(input_norm, model_name.lower())
            if score >= threshold and score > best_score:
                best_score = score
                best_match = model_name

        # Check model aliases for this make
        for alias_norm, canonical_model in make_data["alias_to_canonical"].items():
            score = fuzz.ratio(input_norm, alias_norm)
            if score >= threshold and score > best_score:
                best_score = score
                best_match = canonical_model

        return best_match if best_score >= threshold else None

    except ImportError:
        logger.warning("rapidfuzz not available, fuzzy matching disabled")
        return None
    except Exception as e:
        logger.error(f"❌ Error in suggest_model: {e}", exc_info=True)
        return None


def cross_make_model_hint(raw_model: str) -> List[Tuple[str, str]]:
    """
    Find if a model name is known but belongs to a different make.

    Useful for suggesting make changes when user types a model from another manufacturer.

    Args:
        raw_model: Raw model input to search for

    Returns:
        List[Tuple[str, str]]: List of (canonical_make, canonical_model) pairs
    """
    try:
        from rapidfuzz import fuzz

        if not raw_model or not raw_model.strip():
            return []

        input_norm = raw_model.strip().lower()
        cache = ensure_catalog_cached()

        matches = []

        # Search through all make-model combinations
        for make_name, make_data in cache["model_index_by_make"].items():
            for model_name in make_data["all_models"]:
                score = fuzz.ratio(input_norm, model_name.lower())
                if score >= 85:  # Higher threshold for cross-make hints
                    matches.append((make_name, model_name))

            # Also check model aliases
            for alias_norm, canonical_model in make_data["alias_to_canonical"].items():
                score = fuzz.ratio(input_norm, alias_norm)
                if score >= 85:
                    matches.append((make_name, canonical_model))

        # Remove duplicates and return top matches
        seen = set()
        unique_matches = []
        for make, model in matches:
            key = (make, model)
            if key not in seen:
                seen.add(key)
                unique_matches.append((make, model))

        return unique_matches[:3]  # Return top 3 matches

    except ImportError:
        logger.warning("rapidfuzz not available, cross-make hints disabled")
        return []
    except Exception as e:
        logger.error(f"❌ Error in cross_make_model_hint: {e}", exc_info=True)
        return []


def filter_make_suggestions(raw_input: str, max_suggestions: int = 10) -> List[str]:
    """
    Filter make suggestions based on user input (prefix/substring matching).

    Args:
        raw_input: Raw user input
        max_suggestions: Maximum number of suggestions to return

    Returns:
        List[str]: Filtered list of canonical make names
    """
    try:
        if not raw_input or not raw_input.strip():
            cache = ensure_catalog_cached()
            return cache["make_index"]["all_makes"][:max_suggestions]

        input_lower = raw_input.strip().lower()
        cache = ensure_catalog_cached()

        matches = []
        for make_name in cache["make_index"]["all_makes"]:
            if input_lower in make_name.lower():
                matches.append(make_name)

        return matches[:max_suggestions]

    except Exception as e:
        logger.error(f"❌ Error in filter_make_suggestions: {e}", exc_info=True)
        return []


def filter_model_suggestions(make: str, raw_input: str, max_suggestions: int = 10) -> List[str]:
    """
    Filter model suggestions based on user input within a specific make.

    Args:
        make: Canonical make name
        raw_input: Raw user input
        max_suggestions: Maximum number of suggestions to return

    Returns:
        List[str]: Filtered list of canonical model names
    """
    try:
        cache = ensure_catalog_cached()
        make_data = cache["model_index_by_make"].get(make)

        if not make_data:
            return []

        if not raw_input or not raw_input.strip():
            return make_data["all_models"][:max_suggestions]

        input_lower = raw_input.strip().lower()
        matches = []

        for model_name in make_data["all_models"]:
            if input_lower in model_name.lower():
                matches.append(model_name)

        return matches[:max_suggestions]

    except Exception as e:
        logger.error(f"❌ Error in filter_model_suggestions: {e}", exc_info=True)
        return []


