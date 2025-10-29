"""
Comprehensive error handling and validation for Fast Deterministic Vehicle Resolution System.

This module implements robust input validation, bounds checking, timeout handling,
and fallback value systems as specified in requirements 7.1, 7.2, 7.3, 7.4, 7.5.
"""

import re
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, Union, List, Tuple


class ErrorCode(Enum):
    """Structured error codes for systematic error tracking."""
    # Input validation errors (7.1, 7.2)
    INVALID_YEAR_RANGE = "E001"
    INVALID_FIELD_NAME = "E002"
    INVALID_CURB_WEIGHT_BOUNDS = "E003"
    INVALID_UNIT_FORMAT = "E004"
    INVALID_CATALYTIC_CONVERTER_COUNT = "E005"
    INVALID_BOOLEAN_VALUE = "E006"
    
    # Source and timeout errors (7.3, 7.4)
    HTTP_TIMEOUT = "E101"
    SOURCE_UNAVAILABLE = "E102"
    PARSING_FAILED = "E103"
    PRIMARY_SOURCE_FAILED = "E104"
    ALL_SOURCES_FAILED = "E105"
    
    # System errors
    CACHE_ERROR = "E201"
    LLM_TIMEOUT = "E202"
    PROCESSING_TIMEOUT = "E203"
    VALIDATION_FAILED = "E204"


@dataclass
class ValidationResult:
    """Result of input validation with detailed error information."""
    is_valid: bool
    normalized_value: Any = None
    error_code: Optional[ErrorCode] = None
    error_message: Optional[str] = None
    field_name: Optional[str] = None


@dataclass
class PartialResult:
    """Partial resolution result with confidence indicators."""
    specifications: Any  # VehicleSpecification from fast_deterministic_models
    confidence_scores: Dict[str, float]
    source_attribution: Dict[str, str]
    missing_fields: List[str]
    error_codes: List[ErrorCode]
    processing_time_ms: int
    evidence_payload: Dict[str, Any]


@dataclass
class FallbackValue:
    """Fallback value with confidence and source information."""
    value: Any
    confidence: float
    source: str
    reasoning: str


class InputValidator:
    """
    Comprehensive input validation and bounds checking system.
    
    Implements requirements 7.1, 7.2 for input validation and bounds checking.
    """
    
    def __init__(self):
        """Initialize validator with vehicle type bounds."""
        # Import here to avoid circular imports
        import fast_deterministic_models
        self.models = fast_deterministic_models
        
        # Vehicle-type-specific weight bounds (in pounds)
        self.weight_bounds = {
            "SUV": (2800, 6500),
            "SEDAN": (2500, 4500),
            "TRUCK": (4000, 8000),
            "COUPE": (2500, 4500),
            "HATCHBACK": (2200, 4000),
            "WAGON": (2800, 5000),
            "CONVERTIBLE": (2500, 4500),
            "DEFAULT": (2000, 8000)  # Conservative default range
        }
        
        # Valid boolean representations
        self.true_values = {'true', 'yes', '1', 'on', 'enabled', 'present'}
        self.false_values = {'false', 'no', '0', 'off', 'disabled', 'absent', 'none'}
    
    def validate_curb_weight(self, weight_value: Union[str, float, int], 
                           vehicle_type: str = "DEFAULT") -> ValidationResult:
        """
        Validate and normalize curb weight with unit conversion and bounds checking.
        
        Args:
            weight_value: Raw weight value (string, float, or int)
            vehicle_type: Vehicle type for bounds checking
            
        Returns:
            ValidationResult with normalized weight or error information
            
        Requirements: 7.1, 7.2
        """
        try:
            # Handle None or empty values
            if weight_value is None or (isinstance(weight_value, str) and not weight_value.strip()):
                return ValidationResult(
                    is_valid=False,
                    error_code=ErrorCode.INVALID_UNIT_FORMAT,
                    error_message="Weight value cannot be empty or None",
                    field_name="curb_weight"
                )
            
            # Normalize the weight value
            try:
                normalized_weight = self.models.normalize_curb_weight(weight_value)
            except self.models.ValidationError as e:
                return ValidationResult(
                    is_valid=False,
                    error_code=ErrorCode.INVALID_UNIT_FORMAT,
                    error_message=f"Failed to parse weight value: {str(e)}",
                    field_name="curb_weight"
                )
            
            # Validate bounds
            if not self.models.validate_curb_weight_bounds(normalized_weight, vehicle_type):
                bounds = self.weight_bounds.get(vehicle_type.upper(), self.weight_bounds["DEFAULT"])
                return ValidationResult(
                    is_valid=False,
                    error_code=ErrorCode.INVALID_CURB_WEIGHT_BOUNDS,
                    error_message=f"Weight {normalized_weight} lbs out of bounds for {vehicle_type}. "
                                f"Expected range: {bounds[0]}-{bounds[1]} lbs",
                    field_name="curb_weight"
                )
            
            return ValidationResult(
                is_valid=True,
                normalized_value=float(normalized_weight),
                field_name="curb_weight"
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_code=ErrorCode.VALIDATION_FAILED,
                error_message=f"Unexpected error validating weight: {str(e)}",
                field_name="curb_weight"
            )
    
    def validate_catalytic_converters(self, count_value: Union[str, int]) -> ValidationResult:
        """
        Validate catalytic converter count.
        
        Args:
            count_value: Raw count value (string or int)
            
        Returns:
            ValidationResult with normalized count or error information
            
        Requirements: 7.1, 7.2
        """
        try:
            # Handle None or empty values
            if count_value is None or (isinstance(count_value, str) and not count_value.strip()):
                return ValidationResult(
                    is_valid=False,
                    error_code=ErrorCode.INVALID_CATALYTIC_CONVERTER_COUNT,
                    error_message="Catalytic converter count cannot be empty or None",
                    field_name="catalytic_converters"
                )
            
            # Convert to integer
            try:
                if isinstance(count_value, str):
                    # Strip units and formatting
                    cleaned = re.sub(r'[^\d]', '', count_value.strip())
                    if not cleaned:
                        raise ValueError("No numeric value found")
                    count = int(cleaned)
                else:
                    count = int(count_value)
            except (ValueError, TypeError) as e:
                return ValidationResult(
                    is_valid=False,
                    error_code=ErrorCode.INVALID_CATALYTIC_CONVERTER_COUNT,
                    error_message=f"Invalid catalytic converter count format: {count_value}",
                    field_name="catalytic_converters"
                )
            
            # Validate range
            if not self.models.validate_catalytic_converter_count(count):
                return ValidationResult(
                    is_valid=False,
                    error_code=ErrorCode.INVALID_CATALYTIC_CONVERTER_COUNT,
                    error_message=f"Catalytic converter count {count} out of valid range (1-4)",
                    field_name="catalytic_converters"
                )
            
            return ValidationResult(
                is_valid=True,
                normalized_value=count,
                field_name="catalytic_converters"
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_code=ErrorCode.VALIDATION_FAILED,
                error_message=f"Unexpected error validating catalytic converter count: {str(e)}",
                field_name="catalytic_converters"
            )
    
    def validate_boolean_field(self, bool_value: Union[str, bool], field_name: str) -> ValidationResult:
        """
        Validate and normalize boolean fields (aluminum_engine, aluminum_rims).
        
        Args:
            bool_value: Raw boolean value (string or bool)
            field_name: Name of the field being validated
            
        Returns:
            ValidationResult with normalized boolean or error information
            
        Requirements: 7.1, 7.2
        """
        try:
            # Handle None values
            if bool_value is None:
                return ValidationResult(
                    is_valid=True,
                    normalized_value=None,
                    field_name=field_name
                )
            
            # Handle boolean input
            if isinstance(bool_value, bool):
                return ValidationResult(
                    is_valid=True,
                    normalized_value=bool_value,
                    field_name=field_name
                )
            
            # Handle string input
            if isinstance(bool_value, str):
                normalized_str = bool_value.strip().lower()
                
                if normalized_str in self.true_values:
                    return ValidationResult(
                        is_valid=True,
                        normalized_value=True,
                        field_name=field_name
                    )
                elif normalized_str in self.false_values:
                    return ValidationResult(
                        is_valid=True,
                        normalized_value=False,
                        field_name=field_name
                    )
                else:
                    return ValidationResult(
                        is_valid=False,
                        error_code=ErrorCode.INVALID_BOOLEAN_VALUE,
                        error_message=f"Invalid boolean value for {field_name}: '{bool_value}'. "
                                    f"Valid values: {self.true_values | self.false_values}",
                        field_name=field_name
                    )
            
            # Handle other types
            return ValidationResult(
                is_valid=False,
                error_code=ErrorCode.INVALID_BOOLEAN_VALUE,
                error_message=f"Invalid type for {field_name}: {type(bool_value)}. Expected bool or string.",
                field_name=field_name
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_code=ErrorCode.VALIDATION_FAILED,
                error_message=f"Unexpected error validating {field_name}: {str(e)}",
                field_name=field_name
            )
    
    def validate_vehicle_specification(self, raw_specs: Dict[str, Any], 
                                     vehicle_type: str = "DEFAULT") -> Tuple[Any, List[ValidationResult]]:
        """
        Validate complete vehicle specification with all fields.
        
        Args:
            raw_specs: Dictionary of raw specification values
            vehicle_type: Vehicle type for bounds checking
            
        Returns:
            Tuple of (VehicleSpecification, List of validation errors)
            
        Requirements: 7.1, 7.2
        """
        validated_specs = self.models.VehicleSpecification()
        validation_errors = []
        
        # Validate curb weight
        if 'curb_weight' in raw_specs:
            weight_result = self.validate_curb_weight(raw_specs['curb_weight'], vehicle_type)
            if weight_result.is_valid:
                validated_specs.curb_weight = weight_result.normalized_value
            else:
                validation_errors.append(weight_result)
        
        # Validate aluminum engine
        if 'aluminum_engine' in raw_specs:
            engine_result = self.validate_boolean_field(raw_specs['aluminum_engine'], 'aluminum_engine')
            if engine_result.is_valid:
                validated_specs.aluminum_engine = engine_result.normalized_value
            else:
                validation_errors.append(engine_result)
        
        # Validate aluminum rims
        if 'aluminum_rims' in raw_specs:
            rims_result = self.validate_boolean_field(raw_specs['aluminum_rims'], 'aluminum_rims')
            if rims_result.is_valid:
                validated_specs.aluminum_rims = rims_result.normalized_value
            else:
                validation_errors.append(rims_result)
        
        # Validate catalytic converters
        if 'catalytic_converters' in raw_specs:
            cat_result = self.validate_catalytic_converters(raw_specs['catalytic_converters'])
            if cat_result.is_valid:
                validated_specs.catalytic_converters = cat_result.normalized_value
            else:
                validation_errors.append(cat_result)
        
        return validated_specs, validation_errors


class ErrorLogger:
    """
    Structured error logging system for systematic error tracking.
    
    Implements requirements 7.3, 7.4 for structured error logging.
    """
    
    def __init__(self, logger_name: str = "vehicle_resolution"):
        """Initialize error logger."""
        self.logger = logging.getLogger(logger_name)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log_validation_error(self, validation_result: ValidationResult, 
                           context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log validation error with structured information.
        
        Args:
            validation_result: ValidationResult containing error details
            context: Additional context information
        """
        error_data = {
            'error_code': validation_result.error_code.value if validation_result.error_code else 'UNKNOWN',
            'field_name': validation_result.field_name,
            'error_message': validation_result.error_message,
            'context': context or {}
        }
        
        self.logger.error(f"Validation Error: {error_data}")
    
    def log_timeout_error(self, operation: str, timeout_ms: int, 
                         context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log timeout error with operation details.
        
        Args:
            operation: Name of the operation that timed out
            timeout_ms: Timeout value in milliseconds
            context: Additional context information
        """
        error_data = {
            'error_code': ErrorCode.PROCESSING_TIMEOUT.value,
            'operation': operation,
            'timeout_ms': timeout_ms,
            'context': context or {}
        }
        
        self.logger.error(f"Timeout Error: {error_data}")
    
    def log_source_error(self, source_name: str, error_code: ErrorCode, 
                        error_message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log source-related error.
        
        Args:
            source_name: Name of the data source
            error_code: Specific error code
            error_message: Error message
            context: Additional context information
        """
        error_data = {
            'error_code': error_code.value,
            'source_name': source_name,
            'error_message': error_message,
            'context': context or {}
        }
        
        self.logger.error(f"Source Error: {error_data}")


# Test if classes are defined
if __name__ == "__main__":
    print("Testing error handling classes...")
    print(f"ErrorCode defined: {ErrorCode}")
    print(f"ValidationResult defined: {ValidationResult}")
    print("All classes defined successfully")

# Global instances for easy access
try:
    input_validator = InputValidator()
    error_logger = ErrorLogger()
    print("Global instances created successfully")
except Exception as e:
    print(f"Error creating global instances: {e}")
    import traceback
    traceback.print_exc()