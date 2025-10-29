"""Integration layer between Streamlit UI and vehicle resolver."""

from __future__ import annotations

import json
import logging
import sys
from typing import Any, Dict, Optional

import pandas as pd
from sqlalchemy import text

from database_config import create_database_engine
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


