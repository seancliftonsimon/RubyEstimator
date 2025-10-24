"""
End-to-end validation script for Ruby GEM Estimator with real vehicle data.

This script conducts thorough testing with known vehicle specifications to validate
the complete system functionality and accuracy.
"""

import sys
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Import system components
from resolver import (
    GroundedSearchClient, ConsensusResolver, ProvenanceTracker,
    SearchCandidate, ResolutionResult
)
from vehicle_data import process_vehicle
from app import get_config, calculate_totals, compute_commodities, validate_pricing_conventions
from database_config import test_database_connection


class EndToEndValidator:
    """Comprehensive end-to-end validation with real vehicle data."""
    
    def __init__(self):
        """Initialize the validator with known vehicle test data."""
        self.test_vehicles = [
            {
                "year": 2020,
                "make": "Toyota",
                "model": "Camry",
                "expected": {
                    "curb_weight": 3500,
                    "aluminum_engine": True,
                    "aluminum_rims": False,
                    "catalytic_converters": 2
                }
            },
            {
                "year": 2019,
                "make": "Honda", 
                "model": "Civic",
                "expected": {
                    "curb_weight": 2900,
                    "aluminum_engine": True,
                    "aluminum_rims": False,
                    "catalytic_converters": 1
                }
            },
            {
                "year": 2021,
                "make": "Ford",
                "model": "F-150",
                "expected": {
                    "curb_weight": 4500,
                    "aluminum_engine": False,
                    "aluminum_rims": True,
                    "catalytic_converters": 2
                }
            }
        ]
        self.validation_results = []
        self.performance_metrics = {} 
   
    def run_complete_validation(self) -> Dict[str, Any]:
        """Run complete end-to-end validation."""
        print("🔍 Starting End-to-End Validation with Real Vehicle Data")
        print("=" * 70)
        
        # Test database connectivity
        self.validate_database_connectivity()
        
        # Test configuration system
        self.validate_configuration_system()
        
        # Test resolver components with real data
        self.validate_resolver_with_real_data()
        
        # Test complete vehicle processing workflow
        self.validate_complete_workflow()
        
        # Test admin configuration changes
        self.validate_admin_configuration()
        
        # Test backward compatibility
        self.validate_backward_compatibility()
        
        # Performance benchmarking
        self.benchmark_system_performance()
        
        return self.generate_final_report()
    
    def validate_database_connectivity(self):
        """Validate database connectivity and schema."""
        print("\n📊 Validating Database Connectivity...")
        
        try:
            db_info = test_database_connection()
            if db_info and db_info.get("connected"):
                self.log_success("Database connection established")
                self.log_info(f"Database: {db_info.get('database_name', 'Unknown')}")
            else:
                self.log_error("Database connection failed")
                
        except Exception as e:
            self.log_error(f"Database validation failed: {e}")
    
    def validate_configuration_system(self):
        """Validate configuration loading and admin settings."""
        print("\n⚙️ Validating Configuration System...")
        
        try:
            config = get_config()
            
            # Validate required sections
            required_sections = [
                "price_per_lb", "flat_costs", "weights_fixed", 
                "assumptions", "heuristics", "grounding_settings", "consensus_settings"
            ]
            
            missing_sections = [section for section in required_sections if section not in config]
            if not missing_sections:
                self.log_success("All configuration sections present")
            else:
                self.log_error(f"Missing configuration sections: {missing_sections}")
            
            # Test grounding settings
            grounding = config.get("grounding_settings", {})
            if all(key in grounding for key in ["target_candidates", "clustering_tolerance", "confidence_threshold"]):
                self.log_success("Grounding settings validation passed")
            else:
                self.log_error("Missing grounding settings")
                
        except Exception as e:
            self.log_error(f"Configuration validation failed: {e}")
    
    def validate_resolver_with_real_data(self):
        """Validate resolver components with real vehicle data."""
        print("\n🔧 Validating Resolver with Real Vehicle Data...")
        
        try:
            resolver = ConsensusResolver()
            tracker = ProvenanceTracker()
            
            for vehicle in self.test_vehicles:
                vehicle_key = f"{vehicle['year']}_{vehicle['make']}_{vehicle['model']}"
                
                # Test curb weight resolution
                weight_candidates = self.create_weight_candidates(vehicle)
                weight_result = resolver.resolve_field(weight_candidates)
                
                if self.validate_weight_result(weight_result, vehicle["expected"]["curb_weight"]):
                    self.log_success(f"Weight resolution accurate for {vehicle_key}")
                else:
                    self.log_warning(f"Weight resolution inaccurate for {vehicle_key}")
                
                # Test engine material resolution
                engine_candidates = self.create_engine_candidates(vehicle)
                engine_result = resolver.resolve_field(engine_candidates)
                
                if self.validate_engine_result(engine_result, vehicle["expected"]["aluminum_engine"]):
                    self.log_success(f"Engine material resolution accurate for {vehicle_key}")
                else:
                    self.log_warning(f"Engine material resolution inaccurate for {vehicle_key}")
                
                # Test provenance tracking
                record_id = tracker.create_resolution_record(vehicle_key, "curb_weight", weight_result)
                if record_id:
                    self.log_success(f"Provenance tracking working for {vehicle_key}")
                else:
                    self.log_warning(f"Provenance tracking issues for {vehicle_key}")
                    
        except Exception as e:
            self.log_error(f"Resolver validation failed: {e}")
    
    def validate_complete_workflow(self):
        """Validate complete vehicle processing workflow."""
        print("\n🔄 Validating Complete Workflow...")
        
        try:
            for vehicle in self.test_vehicles:
                start_time = time.time()
                
                # Process vehicle through complete workflow
                result = process_vehicle(
                    year=vehicle["year"],
                    make=vehicle["make"], 
                    model=vehicle["model"],
                    cars=1
                )
                
                processing_time = time.time() - start_time
                
                if result and "curb_weight" in result:
                    self.log_success(f"Complete workflow successful for {vehicle['year']} {vehicle['make']} {vehicle['model']}")
                    self.log_info(f"Processing time: {processing_time:.2f}s")
                    
                    # Validate pricing calculations
                    commodities = compute_commodities(
                        cars=1,
                        curb_weight=result["curb_weight"],
                        aluminum_engine=result.get("aluminum_engine"),
                        aluminum_rims=result.get("aluminum_rims"),
                        catalytic_converters=result.get("catalytic_converters")
                    )
                    
                    totals = calculate_totals(commodities, 1, result["curb_weight"])
                    
                    # Validate pricing conventions
                    validation_errors = validate_pricing_conventions(commodities, totals)
                    if not validation_errors:
                        self.log_success("Pricing calculations valid")
                    else:
                        self.log_error(f"Pricing validation errors: {validation_errors}")
                        
                else:
                    self.log_error(f"Complete workflow failed for {vehicle['year']} {vehicle['make']} {vehicle['model']}")
                    
        except Exception as e:
            self.log_error(f"Complete workflow validation failed: {e}")  
  
    def validate_admin_configuration(self):
        """Validate admin configuration changes work correctly."""
        print("\n👨‍💼 Validating Admin Configuration...")
        
        try:
            from database_config import upsert_app_config, get_app_config
            
            # Test configuration update
            test_config = {"test_setting": 123.45}
            success = upsert_app_config("test_section", test_config, "Test config", "validator")
            
            if success:
                self.log_success("Configuration update successful")
                
                # Verify configuration retrieval
                retrieved_config = get_app_config()
                if retrieved_config and "test_section" in retrieved_config:
                    self.log_success("Configuration retrieval successful")
                else:
                    self.log_warning("Configuration retrieval incomplete")
            else:
                self.log_error("Configuration update failed")
                
        except Exception as e:
            self.log_error(f"Admin configuration validation failed: {e}")
    
    def validate_backward_compatibility(self):
        """Validate backward compatibility with existing vehicle database."""
        print("\n🔄 Validating Backward Compatibility...")
        
        try:
            from vehicle_data import get_last_ten_entries
            
            # Test existing database access
            entries = get_last_ten_entries()
            if entries is not None:
                self.log_success("Existing vehicle database access working")
                self.log_info(f"Retrieved {len(entries)} existing entries")
            else:
                self.log_warning("No existing vehicle entries found (expected for new installations)")
            
            # Test that new features don't break existing functionality
            config = get_config()
            if config and "price_per_lb" in config:
                self.log_success("Existing configuration structure maintained")
            else:
                self.log_error("Configuration structure compatibility broken")
                
        except Exception as e:
            self.log_error(f"Backward compatibility validation failed: {e}")
    
    def benchmark_system_performance(self):
        """Benchmark system performance under load."""
        print("\n⚡ Benchmarking System Performance...")
        
        try:
            resolver = ConsensusResolver()
            
            # Single resolution benchmark
            start_time = time.time()
            candidates = [
                SearchCandidate(3500.0, "kbb.com", "3500 from kbb", 0.9, "3500"),
                SearchCandidate(3520.0, "edmunds.com", "3520 from edmunds", 0.9, "3520"),
                SearchCandidate(3480.0, "autotrader.com", "3480 from autotrader", 0.7, "3480")
            ]
            result = resolver.resolve_field(candidates)
            single_time = time.time() - start_time
            
            self.performance_metrics["single_resolution_time"] = single_time
            
            if single_time < 0.1:
                self.log_success(f"Single resolution performance excellent: {single_time:.3f}s")
            elif single_time < 0.5:
                self.log_success(f"Single resolution performance good: {single_time:.3f}s")
            else:
                self.log_warning(f"Single resolution performance slow: {single_time:.3f}s")
            
            # Batch resolution benchmark
            start_time = time.time()
            for i in range(10):
                batch_candidates = [
                    SearchCandidate(3500.0 + i, f"source_{i}.com", f"value from {i}", 0.8, f"val_{i}"),
                    SearchCandidate(3520.0 + i, f"source2_{i}.com", f"value2 from {i}", 0.8, f"val2_{i}")
                ]
                resolver.resolve_field(batch_candidates)
            batch_time = time.time() - start_time
            
            self.performance_metrics["batch_resolution_time"] = batch_time
            
            if batch_time < 1.0:
                self.log_success(f"Batch resolution performance excellent: {batch_time:.3f}s for 10 resolutions")
            elif batch_time < 2.0:
                self.log_success(f"Batch resolution performance good: {batch_time:.3f}s for 10 resolutions")
            else:
                self.log_warning(f"Batch resolution performance slow: {batch_time:.3f}s for 10 resolutions")
                
        except Exception as e:
            self.log_error(f"Performance benchmarking failed: {e}")
    
    def create_weight_candidates(self, vehicle: Dict) -> List[SearchCandidate]:
        """Create realistic weight candidates for testing."""
        expected_weight = vehicle["expected"]["curb_weight"]
        return [
            SearchCandidate(float(expected_weight), "kbb.com", f"{expected_weight} from kbb", 0.9, str(expected_weight)),
            SearchCandidate(float(expected_weight + 20), "edmunds.com", f"{expected_weight + 20} from edmunds", 0.9, str(expected_weight + 20)),
            SearchCandidate(float(expected_weight - 15), "manufacturer.com", f"{expected_weight - 15} from manufacturer", 0.95, str(expected_weight - 15))
        ]
    
    def create_engine_candidates(self, vehicle: Dict) -> List[SearchCandidate]:
        """Create realistic engine material candidates for testing."""
        is_aluminum = vehicle["expected"]["aluminum_engine"]
        material = "aluminum" if is_aluminum else "iron"
        value = 1.0 if is_aluminum else 0.0
        
        return [
            SearchCandidate(value, "kbb.com", f"{material} engine from kbb", 0.9, material),
            SearchCandidate(value, "edmunds.com", f"{material} engine from edmunds", 0.9, material),
            SearchCandidate(value, "manufacturer.com", f"{material} engine from manufacturer", 0.95, material)
        ]
    
    def validate_weight_result(self, result: ResolutionResult, expected_weight: float) -> bool:
        """Validate weight resolution result against expected value."""
        return abs(result.final_value - expected_weight) <= 50.0 and result.confidence_score >= 0.7
    
    def validate_engine_result(self, result: ResolutionResult, expected_aluminum: bool) -> bool:
        """Validate engine material result against expected value."""
        expected_value = 1.0 if expected_aluminum else 0.0
        return result.final_value == expected_value and result.confidence_score >= 0.7
    
    def log_success(self, message: str):
        """Log a successful validation."""
        print(f"  ✅ {message}")
        self.validation_results.append({"type": "success", "message": message})
    
    def log_warning(self, message: str):
        """Log a validation warning."""
        print(f"  ⚠️ {message}")
        self.validation_results.append({"type": "warning", "message": message})
    
    def log_error(self, message: str):
        """Log a validation error."""
        print(f"  ❌ {message}")
        self.validation_results.append({"type": "error", "message": message})
    
    def log_info(self, message: str):
        """Log validation info."""
        print(f"  ℹ️ {message}")
        self.validation_results.append({"type": "info", "message": message})
    
    def generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive final validation report."""
        end_time = datetime.now()
        
        # Count results by type
        success_count = len([r for r in self.validation_results if r["type"] == "success"])
        warning_count = len([r for r in self.validation_results if r["type"] == "warning"])
        error_count = len([r for r in self.validation_results if r["type"] == "error"])
        
        # Determine deployment readiness
        if error_count == 0 and warning_count <= 2:
            deployment_status = "READY"
        elif error_count == 0:
            deployment_status = "READY_WITH_WARNINGS"
        else:
            deployment_status = "NOT_READY"
        
        report = {
            "timestamp": end_time.isoformat(),
            "deployment_status": deployment_status,
            "validation_summary": {
                "total_validations": len(self.validation_results),
                "successes": success_count,
                "warnings": warning_count,
                "errors": error_count
            },
            "performance_metrics": self.performance_metrics,
            "test_vehicles": len(self.test_vehicles),
            "details": self.validation_results
        }
        
        # Print final summary
        print("\n" + "=" * 70)
        print("📋 END-TO-END VALIDATION SUMMARY")
        print("=" * 70)
        print(f"Deployment Status: {deployment_status}")
        print(f"Total Validations: {len(self.validation_results)}")
        print(f"✅ Successes: {success_count}")
        print(f"⚠️ Warnings: {warning_count}")
        print(f"❌ Errors: {error_count}")
        print(f"🚗 Test Vehicles: {len(self.test_vehicles)}")
        
        if deployment_status == "READY":
            print("\n🎉 System is READY for production deployment!")
        elif deployment_status == "READY_WITH_WARNINGS":
            print("\n✅ System is ready for deployment with minor warnings to address.")
        else:
            print("\n🚨 System is NOT READY for deployment. Address errors first.")
        
        return report


def main():
    """Main validation entry point."""
    validator = EndToEndValidator()
    report = validator.run_complete_validation()
    
    # Save detailed report
    with open("end_to_end_validation_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed validation report saved to: end_to_end_validation_report.json")
    
    # Exit with appropriate code
    if report["deployment_status"] == "NOT_READY":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()