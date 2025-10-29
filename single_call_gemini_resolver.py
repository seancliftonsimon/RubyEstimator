"""Minimal single-call vehicle resolver using Gemini 2.5 Flash with Google Search Grounding."""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from google import genai
from sqlalchemy import text

from database_config import create_database_engine, is_sqlite
from persistence import ensure_schema


# Configure logging with forced console output
import sys
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Force output to stdout
    ],
    force=True  # Override any existing configuration
)
logger = logging.getLogger(__name__)


# Response schema for Gemini strict JSON output
VEHICLE_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "curb_weight": {
            "type": "object",
            "properties": {
                "value": {"type": "number", "nullable": True},
                "unit": {"type": "string"},
                "status": {"type": "string", "enum": ["found", "not_found", "conflicting"]},
                "citations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string"},
                            "quote": {"type": "string"},
                            "source_type": {"type": "string", "enum": ["oem", "secondary"]}
                        },
                        "required": ["url", "quote", "source_type"]
                    }
                }
            },
            "required": ["value", "unit", "status", "citations"]
        },
        "aluminum_engine": {
            "type": "object",
            "properties": {
                "value": {"type": "boolean", "nullable": True},
                "status": {"type": "string", "enum": ["found", "not_found", "conflicting"]},
                "citations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string"},
                            "quote": {"type": "string"},
                            "source_type": {"type": "string", "enum": ["oem", "secondary"]}
                        },
                        "required": ["url", "quote", "source_type"]
                    }
                }
            },
            "required": ["value", "status", "citations"]
        },
        "aluminum_rims": {
            "type": "object",
            "properties": {
                "value": {"type": "boolean", "nullable": True},
                "status": {"type": "string", "enum": ["found", "not_found", "conflicting"]},
                "citations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string"},
                            "quote": {"type": "string"},
                            "source_type": {"type": "string", "enum": ["oem", "secondary"]}
                        },
                        "required": ["url", "quote", "source_type"]
                    }
                }
            },
            "required": ["value", "status", "citations"]
        },
        "catalytic_converters": {
            "type": "object",
            "properties": {
                "value": {"type": "number", "nullable": True},
                "status": {"type": "string", "enum": ["found", "not_found", "conflicting"]},
                "citations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string"},
                            "quote": {"type": "string"},
                            "source_type": {"type": "string", "enum": ["oem", "secondary"]}
                        },
                        "required": ["url", "quote", "source_type"]
                    }
                }
            },
            "required": ["value", "status", "citations"]
        }
    },
    "required": ["curb_weight", "aluminum_engine", "aluminum_rims", "catalytic_converters"]
}


@dataclass
class VehicleResolution:
    """Result of single-call vehicle resolution."""
    vehicle_key: str
    year: int
    make: str
    model: str
    fields: Dict[str, Any]
    run_id: str
    latency_ms: float
    raw_response: Dict[str, Any]


class SingleCallGeminiResolver:
    """Resolves vehicle specifications using a single Gemini API call with Search Grounding."""
    
    def __init__(self, api_key: Optional[str] = None):
        # Try Streamlit secrets first, then environment variable
        if api_key:
            self.api_key = api_key
        else:
            try:
                import streamlit as st
                self.api_key = st.secrets.get("api", {}).get("GEMINI_API_KEY", "")
                if self.api_key:
                    logger.info("✓ API key loaded from Streamlit secrets")
            except (ImportError, FileNotFoundError, KeyError):
                self.api_key = os.getenv("GEMINI_API_KEY", "")
                if self.api_key:
                    logger.info("✓ API key loaded from environment variable")
        
        self.client = self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Gemini client."""
        if not self.api_key or self.api_key == "YOUR_GEMINI_API_KEY":
            logger.error("❌ GEMINI_API_KEY not set or invalid")
            raise ValueError(
                "GEMINI_API_KEY must be set. "
                "Add to .streamlit/secrets.toml or set as environment variable."
            )
        try:
            logger.info("Initializing Gemini client...")
            client = genai.Client(api_key=self.api_key)
            logger.info("✓ Gemini client initialized successfully")
            return client
        except Exception as exc:
            logger.error(f"❌ Failed to initialize Gemini client: {exc}")
            raise ValueError(f"Failed to initialize Gemini client: {exc}")
    
    def _build_prompt(self, year: int, make: str, model: str) -> str:
        """Build concise prompt optimized for speed."""
        return f"""Find specs for {year} {make} {model}. Return JSON ONLY.

FIND 4 FIELDS:
1. curb_weight (lbs, use minimum if multiple trims)
2. aluminum_engine (true/false, needs explicit "aluminum")
3. aluminum_rims (true/false, "aluminum" or "alloy")
4. catalytic_converters (count, integer)

SOURCES: Prefer OEM (mark "oem"), else 2+ secondary sources (mark "secondary"). Include URL + quote.

STATUS: "found" (has data), "not_found" (no data, value=null), "conflicting" (unclear, value=null)

RETURN JSON:
{{
  "curb_weight": {{"value": 3310, "unit": "lbs", "status": "found", "citations": [{{"url": "...", "quote": "...", "source_type": "oem"}}]}},
  "aluminum_engine": {{"value": true, "status": "found", "citations": [...]}},
  "aluminum_rims": {{"value": true, "status": "found", "citations": [...]}},
  "catalytic_converters": {{"value": 2, "status": "found", "citations": [...]}}
}}"""
    
    def resolve_vehicle(self, year: int, make: str, model: str) -> VehicleResolution:
        """Resolve vehicle specifications with single API call."""
        logger.info("="*70)
        logger.info(f"🚗 RESOLVING: {year} {make} {model}")
        logger.info("="*70)
        
        start_time = time.time()
        
        # Generate vehicle key
        vehicle_key = f"{year}_{make.lower().replace(' ', '_')}_{model.lower().replace(' ', '_')}"
        run_id = self._generate_run_id()
        logger.info(f"Vehicle Key: {vehicle_key}")
        logger.info(f"Run ID: {run_id}")
        
        # Check database cache first
        logger.info("\n💾 Checking database cache...")
        cached_data = self._fetch_from_cache(vehicle_key)
        if cached_data:
            cache_time = (time.time() - start_time) * 1000
            logger.info(f"✓ Cache hit! Retrieved data in {cache_time:.2f}ms")
            logger.info("="*70)
            logger.info(f"✅ RESOLUTION COMPLETE (from cache)")
            logger.info(f"Total Time: {cache_time:.2f}ms ({cache_time/1000:.2f}s)")
            logger.info("="*70 + "\n")
            return cached_data
        logger.info("Cache miss - proceeding with API call")
        
        # Build prompt
        logger.info("\n📝 Building prompt...")
        prompt_start = time.time()
        prompt = self._build_prompt(year, make, model)
        prompt_time = (time.time() - prompt_start) * 1000
        logger.info(f"✓ Prompt built in {prompt_time:.2f}ms")
        logger.info(f"Prompt length: {len(prompt)} characters")
        logger.debug(f"Prompt content:\n{prompt[:500]}...\n")
        
        # Call Gemini with Search Grounding
        # NOTE: Cannot use response_mime_type with tools (Search Grounding)
        # We rely on prompt instructions for JSON format instead
        logger.info("\n🌐 Calling Gemini API with Search Grounding...")
        api_start = time.time()
        
        config = {
            "tools": [{"google_search": {}}],
            "temperature": 0,
            # Paid account optimizations:
            # - Higher limits allow more aggressive requests
            # - Faster model with experimental features
        }
        logger.info(f"Model: gemini-2.0-flash-exp")
        logger.info(f"Config: {json.dumps(config, indent=2)}")
        
        # Retry logic optimized for paid accounts (faster retries, fewer attempts)
        max_retries = 2  # Paid accounts have better reliability
        retry_delay = 0.5  # seconds - much shorter for paid tier
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.info(f"🔄 Retry attempt {attempt + 1}/{max_retries} after {retry_delay}s delay...")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5  # Gentler exponential backoff
                
                response = self.client.models.generate_content(
                    model="gemini-2.0-flash-exp",  # Faster experimental model
                    contents=prompt,
                    config=config
                )
                api_time = (time.time() - api_start) * 1000
                logger.info(f"✓ API call completed in {api_time:.2f}ms")
                break  # Success, exit retry loop
                
            except Exception as exc:
                last_exception = exc
                api_time = (time.time() - api_start) * 1000
                exc_str = str(exc)
                
                # Check if this is a retryable error (503, rate limit, etc.)
                is_retryable = (
                    "503" in exc_str or 
                    "overloaded" in exc_str.lower() or 
                    "rate limit" in exc_str.lower() or
                    "unavailable" in exc_str.lower()
                )
                
                if is_retryable and attempt < max_retries - 1:
                    logger.warning(f"⚠️ Retryable error on attempt {attempt + 1}: {exc}")
                    continue  # Retry
                else:
                    # Non-retryable error or last attempt
                    logger.error(f"❌ API call failed after {api_time:.2f}ms: {exc}")
                    raise RuntimeError(f"Gemini API call failed: {exc}")
        else:
            # All retries exhausted
            logger.error(f"❌ All {max_retries} retry attempts failed")
            raise RuntimeError(f"Gemini API call failed after {max_retries} attempts: {last_exception}")
        
        # Parse JSON response
        logger.info("\n📦 Parsing JSON response...")
        parse_start = time.time()
        
        logger.info(f"Response text length: {len(response.text)} characters")
        logger.debug(f"Raw response (first 1000 chars):\n{response.text[:1000]}")
        if len(response.text) > 1000:
            logger.debug(f"Raw response (last 200 chars):\n...{response.text[-200:]}")
        
        # Strip markdown code blocks if present
        response_text = response.text.strip()
        had_markdown = False
        if response_text.startswith("```json"):
            response_text = response_text[7:]  # Remove ```json
            had_markdown = True
            logger.debug("Stripped ```json markdown wrapper")
        elif response_text.startswith("```"):
            response_text = response_text[3:]  # Remove ```
            had_markdown = True
            logger.debug("Stripped ``` markdown wrapper")
        if response_text.endswith("```"):
            response_text = response_text[:-3]  # Remove closing ```
            had_markdown = True
            logger.debug("Stripped closing ``` markdown")
        response_text = response_text.strip()
        
        if had_markdown:
            logger.info("✓ Removed markdown code block wrappers")
        
        try:
            result = json.loads(response_text)
            parse_time = (time.time() - parse_start) * 1000
            logger.info(f"✓ JSON parsed in {parse_time:.2f}ms")
            logger.info(f"Fields in response: {list(result.keys())}")
            
            # Log field statuses
            for field_name in ["curb_weight", "aluminum_engine", "aluminum_rims", "catalytic_converters"]:
                if field_name in result:
                    field_status = result[field_name].get("status", "missing")
                    field_value = result[field_name].get("value")
                    logger.debug(f"  {field_name}: status={field_status}, value={field_value}")
                else:
                    logger.warning(f"⚠️ Field '{field_name}' missing from response!")
                    
        except json.JSONDecodeError as exc:
            parse_time = (time.time() - parse_start) * 1000
            logger.error(f"❌ JSON parsing failed after {parse_time:.2f}ms: {exc}")
            logger.error(f"JSON error position: line {exc.lineno}, column {exc.colno}")
            logger.error(f"Response text (cleaned, first 500 chars): {response_text[:500]}")
            if len(response_text) > 500:
                logger.error(f"Response text (last 200 chars): ...{response_text[-200:]}")
            logger.error(f"Full response text length: {len(response_text)} characters")
            raise RuntimeError(f"Failed to parse Gemini JSON response: {exc}")
        
        # Validate and normalize
        logger.info("\n✅ Validating and normalizing fields...")
        validate_start = time.time()
        validated_fields = self._validate_and_normalize(result)
        validate_time = (time.time() - validate_start) * 1000
        logger.info(f"✓ Validation completed in {validate_time:.2f}ms")
        
        # Log field summaries
        for field_name, field_data in validated_fields.items():
            value = field_data.get("value")
            status = field_data.get("status")
            confidence = field_data.get("confidence", 0.0)
            citations_count = len(field_data.get("citations", []))
            logger.info(f"  • {field_name}: {value} (status={status}, confidence={confidence:.2f}, citations={citations_count})")
        
        # Calculate preliminary latency for DB persistence
        preliminary_latency_ms = (time.time() - start_time) * 1000
        
        # Persist to database
        logger.info("\n💾 Persisting to database...")
        db_start = time.time()
        self._persist_to_db(
            run_id=run_id,
            vehicle_key=vehicle_key,
            year=year,
            make=make,
            model=model,
            fields=validated_fields,
            latency_ms=preliminary_latency_ms
        )
        db_time = (time.time() - db_start) * 1000
        logger.info(f"✓ Database write completed in {db_time:.2f}ms")
        
        # Calculate final total time
        latency_ms = (time.time() - start_time) * 1000
        
        logger.info("\n" + "="*70)
        logger.info(f"✅ RESOLUTION COMPLETE")
        logger.info(f"Total Time: {latency_ms:.2f}ms ({latency_ms/1000:.2f}s)")
        logger.info(f"  - Prompt: {prompt_time:.2f}ms")
        logger.info(f"  - API Call: {api_time:.2f}ms ({api_time/latency_ms*100:.1f}%)")
        logger.info(f"  - Parsing: {parse_time:.2f}ms")
        logger.info(f"  - Validation: {validate_time:.2f}ms")
        logger.info(f"  - Database: {db_time:.2f}ms")
        logger.info("="*70 + "\n")
        
        return VehicleResolution(
            vehicle_key=vehicle_key,
            year=year,
            make=make,
            model=model,
            fields=validated_fields,
            run_id=run_id,
            latency_ms=latency_ms,
            raw_response=result
        )
    
    def _validate_and_normalize(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize field values."""
        logger.debug("Starting field validation and normalization...")
        validated = {}
        
        # Validate curb_weight
        curb_weight = result.get("curb_weight", {})
        raw_weight = curb_weight.get("value")
        normalized_weight = self._normalize_weight(raw_weight)
        if raw_weight != normalized_weight:
            logger.debug(f"curb_weight: normalized {raw_weight} -> {normalized_weight}")
        validated["curb_weight"] = {
            "value": normalized_weight,
            "unit": "lbs",
            "status": curb_weight.get("status", "not_found"),
            "citations": curb_weight.get("citations", []),
            "confidence": self._calculate_confidence(curb_weight)
        }
        
        # Validate aluminum_engine
        aluminum_engine = result.get("aluminum_engine", {})
        raw_engine = aluminum_engine.get("value")
        normalized_engine = self._normalize_boolean(raw_engine)
        if raw_engine != normalized_engine:
            logger.debug(f"aluminum_engine: normalized {raw_engine} -> {normalized_engine}")
        validated["aluminum_engine"] = {
            "value": normalized_engine,
            "status": aluminum_engine.get("status", "not_found"),
            "citations": aluminum_engine.get("citations", []),
            "confidence": self._calculate_confidence(aluminum_engine)
        }
        
        # Validate aluminum_rims
        aluminum_rims = result.get("aluminum_rims", {})
        raw_rims = aluminum_rims.get("value")
        normalized_rims = self._normalize_boolean(raw_rims)
        if raw_rims != normalized_rims:
            logger.debug(f"aluminum_rims: normalized {raw_rims} -> {normalized_rims}")
        validated["aluminum_rims"] = {
            "value": normalized_rims,
            "status": aluminum_rims.get("status", "not_found"),
            "citations": aluminum_rims.get("citations", []),
            "confidence": self._calculate_confidence(aluminum_rims)
        }
        
        # Validate catalytic_converters
        catalytic_converters = result.get("catalytic_converters", {})
        raw_cats = catalytic_converters.get("value")
        normalized_cats = self._normalize_count(raw_cats)
        if raw_cats != normalized_cats:
            logger.debug(f"catalytic_converters: normalized {raw_cats} -> {normalized_cats}")
        validated["catalytic_converters"] = {
            "value": normalized_cats,
            "status": catalytic_converters.get("status", "not_found"),
            "citations": catalytic_converters.get("citations", []),
            "confidence": self._calculate_confidence(catalytic_converters)
        }
        
        logger.debug("✓ Field validation and normalization complete")
        return validated
    
    def _normalize_weight(self, value: Any) -> Optional[float]:
        """Normalize weight to lbs. If multiple weights provided, selects the minimum."""
        if value is None:
            return None
        
        # Handle lists/arrays of weights - select minimum valid weight
        if isinstance(value, (list, tuple)):
            valid_weights = []
            for v in value:
                try:
                    w = float(v)
                    if 1500 <= w <= 10000:
                        valid_weights.append(w)
                    else:
                        logger.debug(f"Weight {w} lbs outside valid range, skipping")
                except (ValueError, TypeError):
                    logger.debug(f"Could not parse weight value '{v}', skipping")
            
            if valid_weights:
                min_weight = min(valid_weights)
                if len(valid_weights) > 1:
                    logger.info(f"Multiple weights found: {valid_weights}, selecting minimum: {min_weight} lbs")
                return min_weight
            else:
                logger.warning(f"⚠️ No valid weights found in list: {value}")
                return None
        
        # Handle single weight value
        try:
            weight = float(value)
            # Basic sanity check
            if 1500 <= weight <= 10000:
                return weight
            else:
                logger.warning(f"⚠️ Weight {weight} lbs outside valid range (1500-10000), rejecting")
                return None
        except (ValueError, TypeError) as e:
            logger.warning(f"⚠️ Failed to normalize weight value '{value}': {e}")
            return None
    
    def _normalize_boolean(self, value: Any) -> Optional[bool]:
        """Normalize to boolean."""
        if isinstance(value, bool):
            return value
        if value is None:
            return None
        # Handle string representations
        if isinstance(value, str):
            if value.lower() in ("true", "yes", "1"):
                return True
            if value.lower() in ("false", "no", "0"):
                return False
            logger.warning(f"⚠️ Unrecognized boolean string value: '{value}'")
        else:
            logger.warning(f"⚠️ Invalid boolean type: {type(value).__name__}")
        return None
    
    def _normalize_count(self, value: Any) -> Optional[int]:
        """Normalize to integer count."""
        if value is None:
            return None
        try:
            count = int(value)
            # Basic sanity check for catalytic converters
            if 0 <= count <= 10:
                return count
            else:
                logger.warning(f"⚠️ Count {count} outside valid range (0-10), rejecting")
                return None
        except (ValueError, TypeError) as e:
            logger.warning(f"⚠️ Failed to normalize count value '{value}': {e}")
            return None
    
    def _calculate_confidence(self, field_data: Dict[str, Any]) -> float:
        """Calculate confidence score based on status and citations."""
        status = field_data.get("status", "not_found")
        citations = field_data.get("citations", [])
        
        if status == "not_found":
            return 0.0
        
        if status == "conflicting":
            return 0.4
        
        # Status is "found"
        if not citations:
            return 0.5
        
        # Check for OEM sources
        has_oem = any(c.get("source_type") == "oem" for c in citations)
        if has_oem:
            return 0.95
        
        # Count secondary sources
        secondary_count = sum(1 for c in citations if c.get("source_type") == "secondary")
        if secondary_count >= 2:
            return 0.85
        elif secondary_count == 1:
            return 0.70
        
        return 0.60
    
    def _generate_run_id(self) -> str:
        """Generate unique run ID."""
        import uuid
        return uuid.uuid4().hex
    
    def _fetch_from_cache(self, vehicle_key: str) -> Optional[VehicleResolution]:
        """Fetch previously resolved data from database cache."""
        logger.info(f"🔍 Checking database cache for vehicle_key: {vehicle_key}")
        try:
            ensure_schema()
            engine = create_database_engine()
            
            with engine.connect() as conn:
                # Get vehicle record
                logger.debug(f"📖 Reading from 'vehicles' table for key: {vehicle_key}")
                vehicle_row = conn.execute(
                    text("""
                        SELECT year, make, model, updated_at 
                        FROM vehicles 
                        WHERE vehicle_key = :key
                    """),
                    {"key": vehicle_key}
                ).fetchone()
                
                if not vehicle_row:
                    logger.info(f"❌ No cached vehicle found for {vehicle_key} - will fetch fresh data")
                    return None
                
                year, make, model, updated_at = vehicle_row
                logger.info(f"✓ Found cached vehicle: {year} {make} {model} (last updated: {updated_at})")
                
                # Get field values and construct response
                logger.debug(f"📖 Reading from 'field_values' table for key: {vehicle_key}")
                field_rows = conn.execute(
                    text("""
                        SELECT field, value_json 
                        FROM field_values 
                        WHERE vehicle_key = :key
                    """),
                    {"key": vehicle_key}
                ).fetchall()
                
                if not field_rows or len(field_rows) < 4:
                    logger.warning(f"❌ Incomplete field data in cache ({len(field_rows) if field_rows else 0}/4 fields) - will fetch fresh data")
                    return None
                
                logger.info(f"✓ Retrieved {len(field_rows)} field values from cache")
                
                # Parse fields
                fields = {}
                for field_name, value_json_str in field_rows:
                    try:
                        value_data = json.loads(value_json_str) if isinstance(value_json_str, str) else value_json_str
                        
                        # Get citations from evidence table
                        citations_rows = conn.execute(
                            text("""
                                SELECT source_url, quote, value_json
                                FROM evidence
                                WHERE vehicle_key = :key AND field = :field
                                ORDER BY fetched_at DESC
                            """),
                            {"key": vehicle_key, "field": field_name}
                        ).fetchall()
                        
                        citations = []
                        for source_url, quote, evidence_json_str in citations_rows:
                            evidence_data = json.loads(evidence_json_str) if isinstance(evidence_json_str, str) else evidence_json_str
                            citations.append({
                                "url": source_url,
                                "quote": quote,
                                "source_type": evidence_data.get("source_type", "secondary")
                            })
                        
                        fields[field_name] = {
                            "value": value_data.get("value"),
                            "unit": value_data.get("unit"),
                            "status": value_data.get("status", "found"),
                            "confidence": value_data.get("confidence", 0.8),
                            "citations": citations
                        }
                        logger.debug(f"  Loaded field '{field_name}': {value_data.get('value')} ({len(citations)} citations)")
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Failed to parse cached field '{field_name}': {e}")
                        return None
                
                # Verify all required fields are present
                required_fields = ["curb_weight", "aluminum_engine", "aluminum_rims", "catalytic_converters"]
                if not all(field in fields for field in required_fields):
                    missing = [f for f in required_fields if f not in fields]
                    logger.debug(f"Missing required fields in cache: {missing}")
                    return None
                
                # Get most recent run_id for this vehicle (for tracking)
                run_row = conn.execute(
                    text("""
                        SELECT run_id 
                        FROM runs 
                        WHERE run_id IN (
                            SELECT DISTINCT run_id FROM evidence WHERE vehicle_key = :key
                        )
                        ORDER BY finished_at DESC 
                        LIMIT 1
                    """),
                    {"key": vehicle_key}
                ).fetchone()
                
                cached_run_id = run_row[0] if run_row else self._generate_run_id()
                
                logger.info(f"✅ Successfully loaded complete vehicle data from cache for {year} {make} {model}")
                return VehicleResolution(
                    vehicle_key=vehicle_key,
                    year=year,
                    make=make,
                    model=model,
                    fields=fields,
                    run_id=cached_run_id,
                    latency_ms=0.0,  # Cache hit has negligible latency
                    raw_response={}  # No raw response for cached data
                )
                
        except Exception as e:
            logger.error(f"❌ Cache lookup failed: {e}", exc_info=True)
            return None
    
    def _persist_to_db(
        self,
        run_id: str,
        vehicle_key: str,
        year: int,
        make: str,
        model: str,
        fields: Dict[str, Any],
        latency_ms: float
    ):
        """Persist results and evidence to database."""
        logger.info(f"💾 Persisting to database: {year} {make} {model} (vehicle_key={vehicle_key}, run_id={run_id})")
        ensure_schema()
        engine = create_database_engine()
        
        with engine.connect() as conn:
            # Insert run record
            logger.debug(f"✍️  Writing to 'runs' table: run_id={run_id}, latency={latency_ms:.2f}ms")
            conn.execute(
                text(
                    "INSERT INTO runs (run_id, started_at, finished_at, total_ms, status) "
                    "VALUES (:run_id, :started_at, :finished_at, :total_ms, :status)"
                ),
                {
                    "run_id": run_id,
                    "started_at": datetime.utcnow(),
                    "finished_at": datetime.utcnow(),
                    "total_ms": int(latency_ms),
                    "status": "complete"
                }
            )
            logger.info("  ✓ Run record inserted into 'runs' table")
            
            # Insert vehicle record
            logger.debug(f"✍️  Writing to 'vehicles' table: {year} {make} {model}")
            conn.execute(
                text(
                    """
                    INSERT INTO vehicles (vehicle_key, year, make, model, created_at, updated_at)
                    VALUES (:key, :year, :make, :model, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT(vehicle_key) DO UPDATE SET
                        year = excluded.year,
                        make = excluded.make,
                        model = excluded.model,
                        updated_at = CURRENT_TIMESTAMP
                    """
                ),
                {
                    "key": vehicle_key,
                    "year": year,
                    "make": make,
                    "model": model
                }
            )
            logger.info("  ✓ Vehicle record upserted into 'vehicles' table")
            
            # Insert field values - prepare batch insert for better performance
            logger.info(f"  ✍️  Writing {len(fields)} field values to 'field_values' table...")
            field_values_batch = []
            for field_name, field_data in fields.items():
                value_json = json.dumps({
                    "value": field_data["value"],
                    "unit": field_data.get("unit"),
                    "status": field_data["status"],
                    "confidence": field_data["confidence"],
                    "source_name": "gemini_search_grounding",
                    "method": "single_call_gemini"
                })
                
                logger.debug(f"    • {field_name}: {field_data['value']} (status={field_data['status']}, confidence={field_data['confidence']})")
                field_values_batch.append({
                    "key": vehicle_key,
                    "field": field_name,
                    "value": value_json
                })
            
            # Execute batch insert for field values
            if field_values_batch:
                stmt = text(
                    """
                    INSERT INTO field_values (vehicle_key, field, value_json, updated_at)
                    VALUES (:key, :field, :value, CURRENT_TIMESTAMP)
                    ON CONFLICT(vehicle_key, field) DO UPDATE SET
                        value_json = excluded.value_json,
                        updated_at = CURRENT_TIMESTAMP
                    """
                )
                conn.execute(stmt, field_values_batch)
            
            # Insert evidence rows for each field's citations
            for field_name, field_data in fields.items():
                citations = field_data.get("citations", [])
                if citations:
                    logger.debug(f"  ✍️  Writing {len(citations)} citation(s) to 'evidence' table for field '{field_name}'")
                for citation in citations:
                    evidence_json = json.dumps({
                        "value": field_data["value"],
                        "unit": field_data.get("unit"),
                        "source_type": citation.get("source_type"),
                        "confidence": field_data["confidence"]
                    })
                    
                    # Generate unique hash for this evidence
                    import hashlib
                    source_hash = hashlib.md5(
                        f"{citation.get('url', '')}_{citation.get('quote', '')}".encode()
                    ).hexdigest()
                    
                    if is_sqlite():
                        stmt = text(
                            """
                            INSERT OR REPLACE INTO evidence (
                                run_id, vehicle_key, field, value_json, quote, source_url, source_hash, fetched_at
                            ) VALUES (
                                :run_id, :vehicle_key, :field, :value, :quote, :source_url, :source_hash, :fetched_at
                            )
                            """
                        )
                    else:
                        stmt = text(
                            """
                            INSERT INTO evidence (
                                run_id, vehicle_key, field, value_json, quote, source_url, source_hash, fetched_at
                            ) VALUES (
                                :run_id, :vehicle_key, :field, CAST(:value AS JSONB), :quote, :source_url, :source_hash, :fetched_at
                            )
                            ON CONFLICT (run_id, field) DO UPDATE SET
                                value_json = EXCLUDED.value_json,
                                quote = EXCLUDED.quote,
                                source_url = EXCLUDED.source_url,
                                source_hash = EXCLUDED.source_hash,
                                fetched_at = EXCLUDED.fetched_at
                            """
                        )
                    
                    conn.execute(
                        stmt,
                        {
                            "run_id": run_id,
                            "vehicle_key": vehicle_key,
                            "field": field_name,
                            "value": evidence_json,
                            "quote": citation.get("quote", ""),
                            "source_url": citation.get("url", ""),
                            "source_hash": source_hash,
                            "fetched_at": datetime.utcnow()
                        }
                    )
            
            logger.info("  ✓ All field values written to 'field_values' table")
            logger.debug("💾 Committing transaction to database...")
            conn.commit()
            logger.info(f"✅ Database write complete! Successfully persisted {year} {make} {model} with {len(fields)} fields")
            
            # Log total evidence count
            total_citations = sum(len(f.get("citations", [])) for f in fields.values())
            if total_citations > 0:
                logger.debug(f"  Total evidence citations stored: {total_citations}")


# Global instance
single_call_resolver = SingleCallGeminiResolver()

