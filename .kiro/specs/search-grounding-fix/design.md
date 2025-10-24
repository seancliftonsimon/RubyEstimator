# Design Document

## Overview

This design addresses the search grounding configuration issue in the Ruby GEM Estimator application. The system currently fails with "400 Search Grounding is not supported" errors because it uses an incorrect tool configuration format. Based on the Google Gemini cookbook (Search_Grounding.ipynb), the fix involves updating all instances of `{"google_search_retrieval": {}}` to `{"google_search": {}}` across the codebase.

The design ensures minimal disruption to existing functionality while correcting the API configuration to match the official Google Gemini documentation.

## Architecture

The search grounding fix affects two main modules:

1. **resolver.py** - Contains the `GroundedSearchClient` class that handles search-based vehicle specification resolution
2. **vehicle_data.py** - Contains various functions that perform vehicle validation and data gathering using search grounding

The architecture remains unchanged - only the tool configuration parameter is updated to use the correct format.

### Current vs. Corrected Configuration

**Current (Incorrect):**
```python
tools=[{"google_search_retrieval": {}}]
```

**Corrected (Per Cookbook):**
```python
tools=[{"google_search": {}}]
```

## Components and Interfaces

### GroundedSearchClient (resolver.py)

**Affected Methods:**
- `search_vehicle_specs()` - Line 147: Main search method for vehicle specifications
- `get_multiple_candidates()` - Lines 211 and 223: Methods for collecting diverse candidate values

**Interface Changes:**
- No interface changes to public methods
- Internal tool configuration updated to match cookbook specification
- All existing parameters and return types remain unchanged

### Vehicle Data Functions (vehicle_data.py)

**Affected Functions:**
- `validate_vehicle_existence()` - Line 435: Vehicle validation using search
- `get_aluminum_engine_from_api()` - Line 562: Aluminum engine detection fallback
- `get_aluminum_rims_from_api()` - Line 669: Aluminum rims detection fallback
- `get_curb_weight_from_api()` - Lines 772 and 797: Curb weight resolution fallback
- `get_catalytic_converters_from_api()` - Line 879: Catalytic converter count resolution

**Interface Changes:**
- No interface changes to public functions
- Internal tool configuration updated to match cookbook specification
- All existing parameters and return types remain unchanged

## Data Models

No changes to existing data models are required. The fix only affects the tool configuration parameter passed to the Google AI API.

**Existing Models Remain Unchanged:**
- `SearchCandidate` - Represents search result candidates
- `ResolutionResult` - Represents final resolution results
- `ResolutionRecord` - Represents stored resolution records

## Error Handling

### Current Error Behavior
The system currently encounters "400 Search Grounding is not supported" errors, which are logged and cause fallback to less reliable methods or complete failure.

### Improved Error Handling
After the fix:
1. **Successful API Calls**: Search grounding will work correctly, eliminating the 400 errors
2. **Existing Error Handling**: All existing error handling for other API issues (rate limits, authentication, etc.) remains in place
3. **Logging**: Error logs will show successful search grounding operations instead of configuration errors

### Error Recovery
- The fix eliminates the primary error source (incorrect tool configuration)
- Existing retry mechanisms and fallback strategies remain unchanged
- Enhanced logging will help identify any remaining issues

## Testing Strategy

### Validation Approach
1. **Configuration Verification**: Ensure all instances of `google_search_retrieval` are replaced with `google_search`
2. **Functional Testing**: Verify that search grounding API calls complete successfully
3. **Integration Testing**: Test end-to-end vehicle data resolution workflows
4. **Error Monitoring**: Confirm elimination of "Search Grounding is not supported" errors

### Test Cases
1. **Vehicle Validation**: Test `validate_vehicle_existence()` with various vehicle inputs
2. **Specification Resolution**: Test curb weight, aluminum engine, aluminum rims, and catalytic converter resolution
3. **Error Scenarios**: Verify proper handling of other API errors (rate limits, authentication)
4. **Fallback Mechanisms**: Ensure fallback methods still work when search grounding fails for other reasons

### Success Criteria
- Zero "400 Search Grounding is not supported" errors in logs
- Successful completion of vehicle data resolution workflows
- Maintained data quality and response formats
- No regression in existing functionality

## Implementation Considerations

### Minimal Change Approach
- Only the tool configuration string is changed
- No modifications to business logic, data processing, or response handling
- Existing error handling and retry mechanisms remain intact

### Backward Compatibility
- The change is forward-compatible with the Google AI API
- No impact on stored data or database schemas
- Existing cached resolutions remain valid

### Deployment Safety
- The change is low-risk as it only corrects an API parameter
- Can be deployed without downtime
- Easy to rollback if unexpected issues arise (though none are anticipated)

### Reference Compliance
- Implementation follows the Google Gemini cookbook exactly
- Uses the same tool configuration format as shown in cookbook examples
- Maintains consistency with official Google documentation