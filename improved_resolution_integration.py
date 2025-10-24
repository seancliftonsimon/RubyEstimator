"""
Integration module to bridge existing vehicle_data.py with improved data models.

This module provides adapters and helper functions to gradually migrate from the
current implementation to the improved one with ranges, evidence scoring, and
consolidated reports.
"""

from typing import List, Dict, Any, Optional, Tuple
from improved_data_models import (
    SourceTrust, ValueRange, EvidenceScore, FieldResolution, 
    ResolutionReport, DecisionRules, ConditionalFact
)
from enhanced_database_schema import (
    store_field_resolution, get_enhanced_resolution_data,
    check_if_complete_resolution, create_enhanced_resolutions_table
)
from resolver import SearchCandidate, ResolutionResult
from single_call_resolver import VehicleSpecificationBundle
import json


def convert_search_candidates_to_dict(candidates: List[SearchCandidate]) -> List[Dict[str, Any]]:
    """
    Convert SearchCandidate objects to dictionary format expected by DecisionRules.
    
    Args:
        candidates: List of SearchCandidate objects from resolver
        
    Returns:
        List of candidate dictionaries with source, value, confidence
    """
    result = []
    for candidate in candidates:
        result.append({
            'source': candidate.source or candidate.citation,
            'value': candidate.value,
            'confidence': candidate.confidence,
            'citation': candidate.citation
        })
    return result


def resolve_field_with_decision_rules(
    field_name: str, 
    candidates: List[SearchCandidate],
    confidence_threshold: float = 0.7
) -> FieldResolution:
    """
    Apply appropriate decision rule for a field based on candidates.
    
    Args:
        field_name: Name of field to resolve
        candidates: List of SearchCandidate objects
        confidence_threshold: Minimum confidence for acceptance
        
    Returns:
        FieldResolution with complete metadata
    """
    # Convert candidates to dict format
    candidate_dicts = convert_search_candidates_to_dict(candidates)
    
    # Apply appropriate decision rule
    if field_name == 'curb_weight':
        return DecisionRules.resolve_curb_weight(candidate_dicts, confidence_threshold)
    elif field_name == 'aluminum_engine':
        return DecisionRules.resolve_aluminum_engine(candidate_dicts, confidence_threshold)
    elif field_name == 'aluminum_rims':
        return DecisionRules.resolve_aluminum_rims(candidate_dicts, confidence_threshold)
    elif field_name == 'catalytic_converters':
        return DecisionRules.resolve_catalytic_converters(candidate_dicts, confidence_threshold)
    else:
        # Fallback for unknown fields
        resolution = FieldResolution(
            field_name=field_name,
            decision_rule_applied="unknown_field"
        )
        resolution.status = "insufficient_data"
        resolution.warnings.append(f"No decision rule defined for field: {field_name}")
        return resolution


def convert_single_call_result_to_resolutions(
    year: int,
    make: str,
    model: str,
    bundle: VehicleSpecificationBundle,
    confidence_threshold: float = 0.7
) -> ResolutionReport:
    """
    Convert VehicleSpecificationBundle to ResolutionReport with proper evidence scoring.
    
    Args:
        year: Vehicle year
        make: Vehicle make  
        model: Vehicle model
        bundle: VehicleSpecificationBundle from single call resolver
        confidence_threshold: Minimum confidence threshold
        
    Returns:
        ResolutionReport with all field resolutions
    """
    vehicle_key = f"{year}_{make}_{model}"
    report = ResolutionReport(
        vehicle_key=vehicle_key,
        year=year,
        make=make,
        model=model,
        strategy="single_call"
    )
    
    # Helper function to create resolution from bundle field
    def create_resolution_from_bundle(
        field_name: str,
        value: Any,
        conf_key: str,
        sources_key: str
    ) -> Optional[FieldResolution]:
        if value is None:
            return None
        
        confidence = bundle.confidence_scores.get(conf_key, 0.7)
        sources = bundle.source_citations.get(sources_key, [])
        
        resolution = FieldResolution(
            field_name=field_name,
            decision_rule_applied="single_call_resolution",
            confidence=confidence
        )
        
        # Create value range
        resolution.value_range = ValueRange(
            chosen=float(value) if isinstance(value, (int, float)) else (1.0 if value else 0.0),
            estimate_type="single_call"
        )
        
        # Create evidence score from sources
        if sources:
            all_sources = []
            weighted_sum = 0.0
            highest_trust = SourceTrust.UNKNOWN
            
            for source in sources:
                trust = SourceTrust.classify_source(source)
                all_sources.append({
                    'name': source,
                    'value': value,
                    'trust': trust.name,
                    'confidence': confidence
                })
                weighted_sum += trust.value * confidence
                highest_trust = max(highest_trust, trust, key=lambda x: x.value)
            
            resolution.evidence = EvidenceScore(
                weighted_score=weighted_sum,
                source_count=len(sources),
                highest_trust=highest_trust,
                sources=all_sources
            )
        else:
            # No sources provided - create minimal evidence
            resolution.evidence = EvidenceScore(
                weighted_score=confidence * 0.7,  # Assume medium trust
                source_count=1,
                highest_trust=SourceTrust.MEDIUM,
                sources=[{
                    'name': 'single_call_api',
                    'value': value,
                    'trust': SourceTrust.MEDIUM.name,
                    'confidence': confidence
                }]
            )
        
        # Determine status based on confidence and evidence
        if confidence >= confidence_threshold and resolution.evidence.meets_threshold(
            DecisionRules.MIN_EVIDENCE_WEIGHT_FOR_WRITE,
            DecisionRules.MIN_SOURCES_FOR_WRITE
        ):
            resolution.status = "ok"
        else:
            resolution.status = "needs_review"
            resolution.warnings.append(f"Confidence {confidence:.2f} or evidence insufficient")
        
        # Add bundle warnings
        if bundle.warnings:
            resolution.warnings.extend(bundle.warnings)
        
        return resolution
    
    # Process each field
    if bundle.curb_weight_lbs is not None:
        res = create_resolution_from_bundle(
            'curb_weight', bundle.curb_weight_lbs, 
            'curb_weight', 'curb_weight'
        )
        if res:
            report.add_field_resolution(res)
    
    if bundle.aluminum_engine is not None:
        res = create_resolution_from_bundle(
            'aluminum_engine', bundle.aluminum_engine,
            'engine_material', 'engine_material'
        )
        if res:
            report.add_field_resolution(res)
    
    if bundle.aluminum_rims is not None:
        res = create_resolution_from_bundle(
            'aluminum_rims', bundle.aluminum_rims,
            'rim_material', 'rim_material'
        )
        if res:
            report.add_field_resolution(res)
    
    if bundle.catalytic_converters is not None:
        res = create_resolution_from_bundle(
            'catalytic_converters', bundle.catalytic_converters,
            'catalytic_converters', 'catalytic_converters'
        )
        if res:
            report.add_field_resolution(res)
    
    # Calculate overall status
    report.calculate_overall_status()
    
    return report


def store_resolution_report(report: ResolutionReport) -> bool:
    """
    Store a complete ResolutionReport to the enhanced database.
    
    Args:
        report: ResolutionReport to store
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Store each field resolution
        for resolution in [report.curb_weight, report.aluminum_engine, 
                          report.aluminum_rims, report.catalytic_converters]:
            if resolution is not None:
                store_field_resolution(report.vehicle_key, resolution)
        
        print(f"✅ Stored resolution report for {report.vehicle_key}")
        print(f"   Status: {report.outcome} | Confidence: {report.overall_confidence:.2f}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to store resolution report: {e}")
        return False


def get_cached_resolution_report(year: int, make: str, model: str) -> Optional[ResolutionReport]:
    """
    Retrieve cached resolution data and convert to ResolutionReport.
    
    Args:
        year: Vehicle year
        make: Vehicle make
        model: Vehicle model
        
    Returns:
        ResolutionReport if complete cached data exists, None otherwise
    """
    vehicle_key = f"{year}_{make}_{model}"
    
    try:
        resolution_data = get_enhanced_resolution_data(vehicle_key)
        
        if not resolution_data or not check_if_complete_resolution(resolution_data):
            return None
        
        # Create report from cached data
        report = ResolutionReport(
            vehicle_key=vehicle_key,
            year=year,
            make=make,
            model=model,
            strategy="cached"
        )
        
        # Convert each field
        for field_name in ['curb_weight', 'aluminum_engine', 'aluminum_rims', 'catalytic_converters']:
            if field_name not in resolution_data:
                continue
            
            field_data = resolution_data[field_name]
            
            resolution = FieldResolution(
                field_name=field_name,
                confidence=field_data.get('confidence', 0.7),
                status=field_data.get('status', 'ok'),
                decision_rule_applied=field_data.get('decision_rule', 'cached'),
                warnings=field_data.get('warnings', [])
            )
            
            # Reconstruct value range
            resolution.value_range = ValueRange(
                low=field_data.get('value_low'),
                high=field_data.get('value_high'),
                chosen=field_data.get('value'),
                estimate_type=field_data.get('estimate_type', 'cached'),
                variant_needed_for_exact=field_data.get('variant_needed', False)
            )
            
            # Reconstruct evidence
            if field_data.get('evidence_sources'):
                sources = field_data['evidence_sources']
                highest_trust = SourceTrust.UNKNOWN
                for src in sources:
                    trust = SourceTrust[src.get('trust', 'UNKNOWN')]
                    highest_trust = max(highest_trust, trust, key=lambda x: x.value)
                
                resolution.evidence = EvidenceScore(
                    weighted_score=field_data.get('evidence_weight', 0.0),
                    source_count=len(sources),
                    highest_trust=highest_trust,
                    sources=sources
                )
            
            # Reconstruct conditional facts
            if field_data.get('conditional_facts'):
                for cf_data in field_data['conditional_facts']:
                    resolution.conditional_values.append(ConditionalFact(
                        condition=cf_data.get('condition', ''),
                        value=cf_data.get('value'),
                        confidence=cf_data.get('confidence', 0.0),
                        sources=cf_data.get('sources', [])
                    ))
            
            report.add_field_resolution(resolution)
        
        report.calculate_overall_status()
        return report
        
    except Exception as e:
        print(f"Error retrieving cached resolution report: {e}")
        return None


def should_write_to_database(resolution: FieldResolution) -> bool:
    """
    Determine if a field resolution should be written to the database.
    
    Only write if:
    - Status is 'ok'
    - Confidence >= threshold
    - Evidence weight >= threshold
    
    Args:
        resolution: FieldResolution to check
        
    Returns:
        True if should write, False otherwise
    """
    if resolution.status != "ok":
        return False
    
    if resolution.confidence < DecisionRules.MIN_CONFIDENCE_FOR_WRITE:
        return False
    
    if resolution.evidence is None:
        return False
    
    if not resolution.evidence.meets_threshold(
        DecisionRules.MIN_EVIDENCE_WEIGHT_FOR_WRITE,
        DecisionRules.MIN_SOURCES_FOR_WRITE
    ):
        return False
    
    return True


def extract_values_for_legacy_db(report: ResolutionReport) -> Dict[str, Any]:
    """
    Extract simple values from ResolutionReport for legacy database (vehicles table).
    
    Only returns values for fields with status='ok' that meet write thresholds.
    
    Args:
        report: ResolutionReport with field resolutions
        
    Returns:
        Dictionary with simple values for database: {curb_weight_lbs, aluminum_engine, etc.}
    """
    result = {}
    
    # Helper to extract boolean value
    def get_bool_value(resolution: Optional[FieldResolution]) -> Optional[bool]:
        if resolution is None or not should_write_to_database(resolution):
            return None
        value = resolution.get_value()
        return bool(value) if value is not None else None
    
    # Helper to extract numeric value
    def get_numeric_value(resolution: Optional[FieldResolution]) -> Optional[float]:
        if resolution is None or not should_write_to_database(resolution):
            return None
        return resolution.get_value()
    
    # Extract values
    if report.curb_weight:
        result['curb_weight_lbs'] = get_numeric_value(report.curb_weight)
    
    if report.aluminum_engine:
        result['aluminum_engine'] = get_bool_value(report.aluminum_engine)
    
    if report.aluminum_rims:
        result['aluminum_rims'] = get_bool_value(report.aluminum_rims)
    
    if report.catalytic_converters:
        result['catalytic_converters'] = get_numeric_value(report.catalytic_converters)
        # Convert to int if present
        if result['catalytic_converters'] is not None:
            result['catalytic_converters'] = int(result['catalytic_converters'])
    
    return result


def initialize_enhanced_database():
    """Initialize the enhanced database schema."""
    try:
        create_enhanced_resolutions_table()
        print("✅ Enhanced database initialized")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize enhanced database: {e}")
        return False


# Convenience function to get resolution status summary
def get_resolution_status_summary(report: ResolutionReport) -> str:
    """
    Get a one-line summary of resolution status.
    
    Args:
        report: ResolutionReport
        
    Returns:
        String summary
    """
    return (
        f"{report.outcome.upper()}: "
        f"{len(report.fields_resolved)}/{len(report.fields_resolved) + len(report.fields_needing_review) + len(report.fields_failed)} fields | "
        f"Conf: {report.overall_confidence:.2f} | "
        f"{'⚠ Action needed' if report.action_needed else '✓ OK'}"
    )


if __name__ == "__main__":
    # Initialize enhanced database
    initialize_enhanced_database()
    
    # Example usage
    print("\n=== Example: Converting single call result ===")
    from single_call_resolver import VehicleSpecificationBundle
    
    example_bundle = VehicleSpecificationBundle(
        curb_weight_lbs=3500,
        aluminum_engine=True,
        aluminum_rims=True,
        catalytic_converters=2,
        confidence_scores={
            'curb_weight': 0.85,
            'engine_material': 0.90,
            'rim_material': 0.80,
            'catalytic_converters': 0.70
        },
        source_citations={
            'curb_weight': ['KBB.com', 'Edmunds.com'],
            'engine_material': ['Toyota.com official specs'],
            'rim_material': ['Toyota.com'],
            'catalytic_converters': ['EPA.gov']
        }
    )
    
    report = convert_single_call_result_to_resolutions(2022, "Toyota", "Camry", example_bundle)
    print(report.format_compact_report())
    print(f"\nStatus: {get_resolution_status_summary(report)}")

