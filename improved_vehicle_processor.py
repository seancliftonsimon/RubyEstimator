"""
Improved vehicle processing module using enhanced data models, evidence scoring,
and consolidated resolution reports.

This module demonstrates the improved approach to vehicle specification resolution.
"""

from typing import Optional, Dict, Any, Callable
from improved_data_models import ResolutionReport, DecisionRules
from improved_resolution_integration import (
    convert_single_call_result_to_resolutions,
    resolve_field_with_decision_rules,
    store_resolution_report,
    get_cached_resolution_report,
    extract_values_for_legacy_db,
    get_resolution_status_summary
)
from single_call_resolver import SingleCallVehicleResolver
from resolver import GroundedSearchClient, ConsensusResolver
import logging


class ImprovedVehicleProcessor:
    """
    Enhanced vehicle processor with improved data models and decision rules.
    """
    
    def __init__(
        self, 
        api_key: str,
        confidence_threshold: float = 0.7,
        use_cache: bool = True
    ):
        """
        Initialize the improved vehicle processor.
        
        Args:
            api_key: Google AI API key
            confidence_threshold: Minimum confidence threshold for accepting results
            use_cache: Whether to use cached results when available
        """
        self.confidence_threshold = confidence_threshold
        self.use_cache = use_cache
        
        # Initialize resolvers
        self.single_call_resolver = SingleCallVehicleResolver(
            api_key=api_key,
            confidence_threshold=confidence_threshold
        )
        self.grounded_search = GroundedSearchClient()
        self.consensus_resolver = ConsensusResolver(
            confidence_threshold=confidence_threshold
        )
        
        # Statistics
        self.stats = {
            'cache_hits': 0,
            'single_call_success': 0,
            'multi_call_fallback': 0,
            'failures': 0
        }
    
    def process_vehicle(
        self,
        year: int,
        make: str,
        model: str,
        progress_callback: Optional[Callable] = None
    ) -> Optional[ResolutionReport]:
        """
        Process vehicle specifications with improved data models and decision rules.
        
        Strategy:
        1. Check cache for complete high-confidence data
        2. Try single-call resolution
        3. Fallback to multi-call with individual field resolution
        4. Generate consolidated report with ranges, evidence scores, and clear status
        
        Args:
            year: Vehicle year
            make: Vehicle make
            model: Vehicle model
            progress_callback: Optional callback for progress updates
                             Should accept (phase: str, spec_name: str, status: str)
        
        Returns:
            ResolutionReport with complete resolution metadata, or None if failed
        """
        vehicle_key = f"{year}_{make}_{model}"
        logging.info(f"Processing vehicle with improved system: {vehicle_key}")
        
        def update_progress(phase: str, spec_name: Optional[str] = None, 
                          status: Optional[str] = None, confidence: Optional[float] = None,
                          error_message: Optional[str] = None):
            """Helper to safely call progress callback."""
            if progress_callback:
                try:
                    progress_callback(phase, spec_name, status, confidence, error_message)
                except Exception as e:
                    logging.warning(f"Progress callback error: {e}")
        
        # Step 1: Check cache
        update_progress("Checking cache...", None, None)
        
        if self.use_cache:
            cached_report = get_cached_resolution_report(year, make, model)
            if cached_report and cached_report.outcome == "complete":
                logging.info(f"Using complete cached resolution for {vehicle_key}")
                print(f"✅ Found complete cached resolution for {year} {make} {model}")
                print(f"   {get_resolution_status_summary(cached_report)}")
                self.stats['cache_hits'] += 1
                update_progress("Using cached data", None, "complete")
                return cached_report
        
        # Step 2: Try single-call resolution
        update_progress("Running AI search...", None, "searching")
        
        try:
            logging.info(f"Attempting single-call resolution for {vehicle_key}")
            bundle = self.single_call_resolver.resolve_all_specifications(year, make, model)
            
            if bundle and self.single_call_resolver.has_sufficient_confidence(bundle):
                # Convert to resolution report
                report = convert_single_call_result_to_resolutions(
                    year, make, model, bundle, self.confidence_threshold
                )
                
                # Update progress for each field
                for field_name in ['curb_weight', 'aluminum_engine', 'aluminum_rims', 'catalytic_converters']:
                    resolution = getattr(report, field_name, None)
                    if resolution:
                        update_progress(
                            "Searching specifications...",
                            field_name,
                            resolution.status,
                            resolution.confidence
                        )
                
                logging.info(f"Single-call resolution successful: {get_resolution_status_summary(report)}")
                print(f"\n✅ Single-call resolution successful for {year} {make} {model}")
                print(report.format_compact_report())
                
                # Store to enhanced database
                update_progress("Saving results...", None, None)
                store_resolution_report(report)
                
                self.stats['single_call_success'] += 1
                update_progress("Search complete", None, "complete")
                return report
            
            else:
                logging.warning(f"Single-call resolution insufficient confidence for {vehicle_key}")
                if bundle and bundle.warnings:
                    for warning in bundle.warnings:
                        logging.warning(f"  {warning}")
        
        except Exception as e:
            logging.error(f"Single-call resolution failed for {vehicle_key}: {e}")
        
        # Step 3: Fallback to multi-call resolution with improved decision rules
        logging.info(f"Falling back to multi-call resolution for {vehicle_key}")
        print(f"\n⚠ Single-call insufficient, using multi-call fallback...")
        
        report = ResolutionReport(
            vehicle_key=vehicle_key,
            year=year,
            make=make,
            model=model,
            strategy="multi_call"
        )
        
        # Resolve each field individually with decision rules
        fields_to_resolve = [
            ('curb_weight', 'Curb weight'),
            ('aluminum_engine', 'Engine material'),
            ('aluminum_rims', 'Rim material'),
            ('catalytic_converters', 'Catalytic converters')
        ]
        
        for field_name, display_name in fields_to_resolve:
            update_progress(f"Searching specifications...", field_name, "searching")
            
            try:
                # Get candidates from grounded search
                candidates = self.grounded_search.search_vehicle_specs(
                    year, make, model, field_name
                )
                
                if not candidates:
                    logging.warning(f"No candidates found for {field_name}")
                    update_progress(
                        "Searching specifications...",
                        field_name,
                        "failed",
                        None,
                        f"No data found for {display_name}"
                    )
                    continue
                
                # Apply decision rule
                resolution = resolve_field_with_decision_rules(
                    field_name, 
                    candidates,
                    self.confidence_threshold
                )
                
                # Add to report
                report.add_field_resolution(resolution)
                
                # Update progress
                update_progress(
                    "Searching specifications...",
                    field_name,
                    resolution.status,
                    resolution.confidence,
                    resolution.warnings[0] if resolution.warnings else None
                )
                
                logging.info(f"Resolved {field_name}: {resolution.status} (conf: {resolution.confidence:.2f})")
                
            except Exception as e:
                logging.error(f"Failed to resolve {field_name} for {vehicle_key}: {e}")
                update_progress(
                    "Searching specifications...",
                    field_name,
                    "failed",
                    None,
                    f"Error resolving {display_name}"
                )
        
        # Calculate overall status
        report.calculate_overall_status()
        
        logging.info(f"Multi-call resolution complete: {get_resolution_status_summary(report)}")
        print(f"\n📊 Multi-call resolution complete:")
        print(report.format_compact_report())
        
        # Store to enhanced database
        update_progress("Saving results...", None, None)
        store_resolution_report(report)
        
        self.stats['multi_call_fallback'] += 1
        update_progress("Search complete", None, "complete")
        
        if report.outcome == "failed":
            self.stats['failures'] += 1
            return None
        
        return report
    
    def get_values_for_database(self, report: ResolutionReport) -> Dict[str, Any]:
        """
        Extract values suitable for writing to legacy database.
        
        Only returns fields that meet write thresholds (status='ok', 
        confidence >= threshold, evidence >= threshold).
        
        Args:
            report: ResolutionReport
            
        Returns:
            Dictionary with values ready for database write
        """
        return extract_values_for_legacy_db(report)
    
    def print_statistics(self):
        """Print processing statistics."""
        total = sum(self.stats.values())
        if total == 0:
            print("No vehicles processed yet")
            return
        
        print("\n=== Processing Statistics ===")
        print(f"Total vehicles processed: {total}")
        print(f"Cache hits: {self.stats['cache_hits']} ({self.stats['cache_hits']/total*100:.1f}%)")
        print(f"Single-call success: {self.stats['single_call_success']} ({self.stats['single_call_success']/total*100:.1f}%)")
        print(f"Multi-call fallback: {self.stats['multi_call_fallback']} ({self.stats['multi_call_fallback']/total*100:.1f}%)")
        print(f"Failures: {self.stats['failures']} ({self.stats['failures']/total*100:.1f}%)")


def demonstrate_improvements():
    """
    Demonstration of the improved system showing all enhancements.
    """
    import os
    
    print("="*60)
    print("IMPROVED VEHICLE DATA SYSTEM DEMONSTRATION")
    print("="*60)
    
    print("\n📋 Key Improvements:")
    print("1. ✓ Store ranges {low, high, chosen} with estimate_type")
    print("2. ✓ Evidence scoring with source taxonomy (OEM=high, reviews=medium, forums=low)")
    print("3. ✓ Clear decision rules per attribute")
    print("4. ✓ Confidence thresholds control DB writes")
    print("5. ✓ One consolidated Resolution Report")
    
    # Get API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n❌ GEMINI_API_KEY not set - cannot run demonstration")
        return
    
    # Initialize processor
    print("\n🔧 Initializing improved processor...")
    processor = ImprovedVehicleProcessor(
        api_key=api_key,
        confidence_threshold=0.7,
        use_cache=True
    )
    
    # Test vehicles
    test_vehicles = [
        (2022, "Toyota", "Camry"),
        (2023, "Ford", "F-150"),
        (2019, "Honda", "Civic")
    ]
    
    for year, make, model in test_vehicles:
        print("\n" + "="*60)
        print(f"Processing: {year} {make} {model}")
        print("="*60)
        
        report = processor.process_vehicle(year, make, model)
        
        if report:
            # Show what would be written to database
            db_values = processor.get_values_for_database(report)
            print("\n📝 Values approved for database write:")
            for field, value in db_values.items():
                print(f"   {field}: {value}")
            
            # Show fields that were excluded
            all_fields = ['curb_weight_lbs', 'aluminum_engine', 'aluminum_rims', 'catalytic_converters']
            excluded = [f for f in all_fields if f not in db_values]
            if excluded:
                print("\n⚠ Fields excluded from database (insufficient confidence/evidence):")
                for field in excluded:
                    print(f"   {field}")
        else:
            print("\n❌ Resolution failed - no data written to database")
    
    # Print statistics
    processor.print_statistics()
    
    print("\n" + "="*60)
    print("DEMONSTRATION COMPLETE")
    print("="*60)


if __name__ == "__main__":
    demonstrate_improvements()

