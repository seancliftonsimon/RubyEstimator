"""
Enhanced database schema for storing ranges, evidence scores, and metadata.

This module provides database migrations and enhanced table structures to support:
1. Value ranges (low, high, chosen)
2. Evidence scoring and source tracking
3. Conditional facts for variant-dependent fields
4. Resolution metadata
"""

from sqlalchemy import text
from database_config import create_database_engine, is_sqlite
import json


def create_enhanced_resolutions_table():
    """
    Create or update the resolutions table with enhanced fields for ranges and metadata.
    
    New fields:
    - value_low: Lower bound of value range
    - value_high: Upper bound of value range
    - estimate_type: How the value was estimated (median_of_trusted, consensus, etc.)
    - variant_needed: Whether exact value needs variant info (trim, engine, etc.)
    - evidence_weight: Weighted evidence score from sources
    - evidence_sources: JSON array of source details with trust levels
    - conditional_facts: JSON array of variant-dependent values
    - decision_rule: Which decision rule was applied
    - status: ok, needs_review, or insufficient_data
    """
    engine = create_database_engine()
    
    with engine.connect() as conn:
        if is_sqlite():
            # SQLite: Create new table with enhanced schema
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS enhanced_resolutions (
                    id TEXT PRIMARY KEY,
                    vehicle_key TEXT NOT NULL,
                    field_name TEXT NOT NULL,
                    
                    -- Value and range
                    final_value REAL,
                    value_low REAL,
                    value_high REAL,
                    estimate_type TEXT DEFAULT 'unknown',
                    variant_needed BOOLEAN DEFAULT 0,
                    
                    -- Evidence and confidence
                    confidence_score REAL DEFAULT 0.0,
                    evidence_weight REAL DEFAULT 0.0,
                    evidence_sources TEXT,  -- JSON array
                    
                    -- Decision metadata
                    method TEXT DEFAULT 'unknown',
                    decision_rule TEXT,
                    status TEXT DEFAULT 'insufficient_data',
                    
                    -- Conditional/variant-dependent data
                    conditional_facts TEXT,  -- JSON array
                    
                    -- Provenance
                    candidates_json TEXT,
                    warnings TEXT,  -- JSON array
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    UNIQUE(vehicle_key, field_name, created_at)
                )
            """))
            
            # Try to migrate data from old resolutions table if it exists
            try:
                # Check if old table exists
                result = conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='resolutions'
                """))
                if result.fetchone():
                    # Migrate existing data
                    conn.execute(text("""
                        INSERT OR IGNORE INTO enhanced_resolutions 
                        (id, vehicle_key, field_name, final_value, confidence_score, method, candidates_json, created_at)
                        SELECT id, vehicle_key, field_name, final_value, confidence_score, method, candidates_json, created_at
                        FROM resolutions
                    """))
                    print("✅ Migrated data from old resolutions table to enhanced_resolutions")
            except Exception as e:
                print(f"  Note: Could not migrate old data (this is normal for new installations): {e}")
            
            conn.commit()
            
        else:
            # PostgreSQL: Use ALTER TABLE to add new columns to existing table
            # First ensure base table exists
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS enhanced_resolutions (
                    id TEXT PRIMARY KEY,
                    vehicle_key TEXT NOT NULL,
                    field_name TEXT NOT NULL,
                    
                    -- Value and range
                    final_value REAL,
                    value_low REAL,
                    value_high REAL,
                    estimate_type TEXT DEFAULT 'unknown',
                    variant_needed BOOLEAN DEFAULT FALSE,
                    
                    -- Evidence and confidence
                    confidence_score REAL DEFAULT 0.0,
                    evidence_weight REAL DEFAULT 0.0,
                    evidence_sources JSONB,
                    
                    -- Decision metadata
                    method TEXT DEFAULT 'unknown',
                    decision_rule TEXT,
                    status TEXT DEFAULT 'insufficient_data',
                    
                    -- Conditional/variant-dependent data
                    conditional_facts JSONB,
                    
                    -- Provenance
                    candidates_json JSONB,
                    warnings JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    
                    UNIQUE(vehicle_key, field_name, created_at)
                )
            """))
            
            # Try to migrate from old table
            try:
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'resolutions'
                    )
                """))
                if result.scalar():
                    conn.execute(text("""
                        INSERT INTO enhanced_resolutions 
                        (id, vehicle_key, field_name, final_value, confidence_score, method, candidates_json, created_at)
                        SELECT id, vehicle_key, field_name, final_value, confidence_score, method, 
                               candidates_json::jsonb, created_at
                        FROM resolutions
                        ON CONFLICT (vehicle_key, field_name, created_at) DO NOTHING
                    """))
                    print("✅ Migrated data from old resolutions table to enhanced_resolutions")
            except Exception as e:
                print(f"  Note: Could not migrate old data (this is normal for new installations): {e}")
            
            conn.commit()
    
    print("✅ Enhanced resolutions table created")


def store_field_resolution(vehicle_key: str, field_resolution) -> str:
    """
    Store a FieldResolution object in the enhanced database.
    
    Args:
        vehicle_key: Vehicle identifier (year_make_model)
        field_resolution: FieldResolution object from improved_data_models
        
    Returns:
        Record ID
    """
    import uuid
    from datetime import datetime
    
    engine = create_database_engine()
    record_id = str(uuid.uuid4())
    
    # Extract data from field_resolution
    value = field_resolution.get_value()
    value_low = field_resolution.value_range.low if field_resolution.value_range else None
    value_high = field_resolution.value_range.high if field_resolution.value_range else None
    estimate_type = field_resolution.value_range.estimate_type if field_resolution.value_range else 'unknown'
    variant_needed = field_resolution.value_range.variant_needed_for_exact if field_resolution.value_range else False
    
    evidence_weight = field_resolution.evidence.weighted_score if field_resolution.evidence else 0.0
    evidence_sources = json.dumps(field_resolution.evidence.sources) if field_resolution.evidence else '[]'
    
    conditional_facts = json.dumps([
        {
            'condition': cf.condition,
            'value': cf.value,
            'confidence': cf.confidence,
            'sources': cf.sources
        }
        for cf in field_resolution.conditional_values
    ]) if field_resolution.conditional_values else '[]'
    
    warnings = json.dumps(field_resolution.warnings) if field_resolution.warnings else '[]'
    
    with engine.connect() as conn:
        if is_sqlite():
            conn.execute(text("""
                INSERT OR REPLACE INTO enhanced_resolutions (
                    id, vehicle_key, field_name,
                    final_value, value_low, value_high, estimate_type, variant_needed,
                    confidence_score, evidence_weight, evidence_sources,
                    method, decision_rule, status,
                    conditional_facts, warnings, created_at
                ) VALUES (
                    :id, :vehicle_key, :field_name,
                    :final_value, :value_low, :value_high, :estimate_type, :variant_needed,
                    :confidence_score, :evidence_weight, :evidence_sources,
                    :method, :decision_rule, :status,
                    :conditional_facts, :warnings, :created_at
                )
            """), {
                'id': record_id,
                'vehicle_key': vehicle_key,
                'field_name': field_resolution.field_name,
                'final_value': value,
                'value_low': value_low,
                'value_high': value_high,
                'estimate_type': estimate_type,
                'variant_needed': variant_needed,
                'confidence_score': field_resolution.confidence,
                'evidence_weight': evidence_weight,
                'evidence_sources': evidence_sources,
                'method': 'enhanced_resolution',
                'decision_rule': field_resolution.decision_rule_applied,
                'status': field_resolution.status,
                'conditional_facts': conditional_facts,
                'warnings': warnings,
                'created_at': datetime.now()
            })
        else:
            # PostgreSQL with JSONB
            conn.execute(text("""
                INSERT INTO enhanced_resolutions (
                    id, vehicle_key, field_name,
                    final_value, value_low, value_high, estimate_type, variant_needed,
                    confidence_score, evidence_weight, evidence_sources,
                    method, decision_rule, status,
                    conditional_facts, warnings, created_at
                ) VALUES (
                    :id, :vehicle_key, :field_name,
                    :final_value, :value_low, :value_high, :estimate_type, :variant_needed,
                    :confidence_score, :evidence_weight, :evidence_sources,
                    :method, :decision_rule, :status,
                    :conditional_facts, :warnings, NOW()
                )
                ON CONFLICT (vehicle_key, field_name, created_at) DO UPDATE SET
                    final_value = EXCLUDED.final_value,
                    value_low = EXCLUDED.value_low,
                    value_high = EXCLUDED.value_high,
                    confidence_score = EXCLUDED.confidence_score,
                    evidence_weight = EXCLUDED.evidence_weight,
                    status = EXCLUDED.status
            """), {
                'id': record_id,
                'vehicle_key': vehicle_key,
                'field_name': field_resolution.field_name,
                'final_value': value,
                'value_low': value_low,
                'value_high': value_high,
                'estimate_type': estimate_type,
                'variant_needed': variant_needed,
                'confidence_score': field_resolution.confidence,
                'evidence_weight': evidence_weight,
                'evidence_sources': evidence_sources,
                'method': 'enhanced_resolution',
                'decision_rule': field_resolution.decision_rule_applied,
                'status': field_resolution.status,
                'conditional_facts': conditional_facts,
                'warnings': warnings
            })
        
        conn.commit()
    
    return record_id


def get_enhanced_resolution_data(vehicle_key: str) -> Dict[str, Any]:
    """
    Retrieve enhanced resolution data for a vehicle.
    
    Returns only high-confidence resolutions with status='ok'.
    
    Returns:
        Dictionary mapping field_name to resolution data
    """
    from typing import Dict, Any
    
    engine = create_database_engine()
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT field_name, final_value, value_low, value_high, estimate_type, 
                       variant_needed, confidence_score, evidence_weight, evidence_sources,
                       decision_rule, status, conditional_facts, warnings, created_at
                FROM enhanced_resolutions
                WHERE vehicle_key = :vehicle_key
                  AND status = 'ok'
                  AND confidence_score >= 0.7
                ORDER BY created_at DESC
            """), {'vehicle_key': vehicle_key})
            
            resolution_data = {}
            for row in result.fetchall():
                field_name = row[0]
                
                # Only store the most recent record for each field
                if field_name not in resolution_data:
                    resolution_data[field_name] = {
                        'value': row[1],
                        'value_low': row[2],
                        'value_high': row[3],
                        'estimate_type': row[4],
                        'variant_needed': row[5],
                        'confidence': row[6],
                        'evidence_weight': row[7],
                        'evidence_sources': json.loads(row[8]) if row[8] else [],
                        'decision_rule': row[9],
                        'status': row[10],
                        'conditional_facts': json.loads(row[11]) if row[11] else [],
                        'warnings': json.loads(row[12]) if row[12] else [],
                        'created_at': row[13]
                    }
            
            return resolution_data if resolution_data else None
            
    except Exception as e:
        print(f"Error retrieving enhanced resolution data: {e}")
        return None


def check_if_complete_resolution(resolution_data: Dict[str, Any]) -> bool:
    """
    Check if resolution data contains all required fields with 'ok' status.
    
    Required fields: curb_weight, aluminum_engine, aluminum_rims, catalytic_converters
    """
    required_fields = ['curb_weight', 'aluminum_engine', 'aluminum_rims', 'catalytic_converters']
    
    if not resolution_data:
        return False
    
    for field in required_fields:
        if field not in resolution_data:
            return False
        
        field_data = resolution_data[field]
        if not isinstance(field_data, dict):
            return False
        
        # Check that value exists and status is ok
        if field_data.get('value') is None or field_data.get('status') != 'ok':
            return False
    
    return True


if __name__ == "__main__":
    # Run migrations
    print("Running database migrations...")
    create_enhanced_resolutions_table()
    print("✅ Database migrations complete")

