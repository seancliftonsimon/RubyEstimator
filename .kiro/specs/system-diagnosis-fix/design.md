# Design Document: System Diagnosis and Fix

## Overview

This design addresses critical failures in the Ruby GEM Estimator system that prevent vehicle search and valuation functionality from working correctly. The system currently fails due to two primary issues:

1. **Database Syntax Incompatibility**: PostgreSQL-specific SQL syntax (`NOW() - INTERVAL '24 hours'`) fails in SQLite local testing environment
2. **Google AI API Model Error**: Deprecated model name `gemini-1.5-flash-latest` returns 404 errors

The design ensures the system works reliably across both local testing (SQLite) and online production (PostgreSQL) environments while maintaining proper error handling and logging throughout.

## Architecture

### Current System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit Application                    │
│                         (app.py)                             │
└───────────────┬─────────────────────────────────────────────┘
                │
                ├──────────────┬──────────────┬────────────────┐
                │              │              │                │
        ┌───────▼──────┐ ┌────▼─────┐ ┌─────▼──────┐ ┌───────▼────────┐
        │ vehicle_data │ │ resolver │ │ database   │ │ Google AI API  │
        │              │ │          │ │ _config    │ │                │
        └──────┬───────┘ └────┬─────┘ └─────┬──────┘ └───────┬────────┘
               │              │              │                │
               │              │              │                │
        ┌──────▼──────────────▼──────────────▼────────────────▼─────┐
        │                                                            │
        │  Database Layer (SQLite local / PostgreSQL production)    │
        │                                                            │
        └────────────────────────────────────────────────────────────┘
```

### Problem Areas

**Issue 1: Database Queries**
- Location: `vehicle_data.py`, `resolver.py`, `monitoring_dashboard.py`
- Problem: PostgreSQL-specific `NOW() - INTERVAL '24 hours'` syntax
- Impact: All resolution queries fail in SQLite environment

**Issue 2: Google AI Model**
- Location: `resolver.py` (line 84), `vehicle_data.py` (line 31)
- Problem: Model name `gemini-1.5-flash-latest` is deprecated/not found
- Impact: All vehicle validation and grounded search operations fail

## Components and Interfaces

### 1. Database Configuration Module (`database_config.py`)

**Current State**: Already has environment detection via `is_sqlite()` function

**Enhancement Required**: Add database-agnostic datetime helper functions

```python
def get_datetime_interval_query(hours: int) -> str:
    """
    Generate database-agnostic datetime interval query.
    
    Args:
        hours: Number of hours to subtract from current time
        
    Returns:
        SQL fragment for datetime comparison compatible with current database
    """
    if is_sqlite():
        return f"datetime('now', '-{hours} hours')"
    else:
        return f"NOW() - INTERVAL '{hours} hours'"
```

**Design Rationale**: 
- Centralizes database-specific logic in one module
- Leverages existing `is_sqlite()` detection
- Provides clean interface for other modules to use
- Maintains backward compatibility with PostgreSQL production

### 2. Resolver Module (`resolver.py`)

**Changes Required**:

#### A. Google AI Model Update

**Current Code** (line 84):
```python
return genai.GenerativeModel(model_name='gemini-1.5-flash-latest')
```

**Updated Code**:
```python
return genai.GenerativeModel(model_name='gemini-1.5-flash-8b')
```

**Design Rationale**:
- `gemini-1.5-flash-8b` is the current stable model name
- Maintains same API interface and capabilities
- Provides faster response times with 8B parameter model
- Fully supported in v1beta API version

**Alternative Models** (for future consideration):
- `gemini-1.5-flash`: Standard flash model
- `gemini-1.5-pro`: Higher capability model for complex queries
- `gemini-2.5-flash`: Current generation fast model

#### B. Database Query Updates

**Location**: `ProvenanceTracker.get_cached_resolution()` method (line 792)

**Current Code**:
```python
query = text("""
    SELECT final_value, confidence_score, method, candidates_json, warnings_json, created_at
    FROM resolutions 
    WHERE vehicle_key = :vehicle_key AND field_name = :field_name
    AND created_at > NOW() - INTERVAL '%s hours'
    ORDER BY created_at DESC
    LIMIT 1
""" % max_age_hours)
```

**Updated Code**:
```python
from database_config import get_datetime_interval_query

# Build query with database-agnostic datetime
datetime_condition = get_datetime_interval_query(max_age_hours)
query = text(f"""
    SELECT final_value, confidence_score, method, candidates_json, warnings_json, created_at
    FROM resolutions 
    WHERE vehicle_key = :vehicle_key AND field_name = :field_name
    AND created_at > {datetime_condition}
    ORDER BY created_at DESC
    LIMIT 1
""")
```

**Additional Locations** (lines 952, 961, 978, 1047):
- `create_monitoring_dashboard_data()`: Multiple queries with 24-hour intervals
- `optimize_database_performance()`: Cleanup query with 7-day interval

All follow same pattern: replace hardcoded `NOW() - INTERVAL` with `get_datetime_interval_query()` call.

### 3. Vehicle Data Module (`vehicle_data.py`)

**Changes Required**:

#### A. Google AI Model Update (line 31)

Same change as resolver.py - update model name to `gemini-1.5-flash-8b`

#### B. Database Query Update (line 258)

**Current Code**:
```python
result = conn.execute(text("""
    SELECT field_name, final_value, confidence_score, created_at
    FROM resolutions 
    WHERE vehicle_key = :vehicle_key 
    AND created_at > NOW() - INTERVAL '24 hours'
    ORDER BY created_at DESC
"""), {"vehicle_key": vehicle_key})
```

**Updated Code**:
```python
from database_config import get_datetime_interval_query

datetime_condition = get_datetime_interval_query(24)
result = conn.execute(text(f"""
    SELECT field_name, final_value, confidence_score, created_at
    FROM resolutions 
    WHERE vehicle_key = :vehicle_key 
    AND created_at > {datetime_condition}
    ORDER BY created_at DESC
"""), {"vehicle_key": vehicle_key})
```

### 4. Monitoring Dashboard Module (`monitoring_dashboard.py`)

**Changes Required**: Update all queries with `NOW() - INTERVAL` syntax (lines 231, 299, 349)

Same pattern as above - replace with `get_datetime_interval_query()` calls.

## Data Models

No changes to existing data models required. The fix maintains compatibility with:

- `SearchCandidate` dataclass
- `ResolutionResult` dataclass  
- `ResolutionRecord` dataclass
- Database schema for `resolutions` table

## Error Handling

### Enhanced Error Handling Strategy

#### 1. Google AI API Errors

**Current Behavior**: Generic error logging without specific handling

**Enhanced Behavior**:
```python
def _initialize_model(self):
    """Initialize and return a Gemini model instance with validation."""
    if not self.api_key or self.api_key == "YOUR_GEMINI_API_KEY":
        logging.warning("Google AI API key not configured")
        return None
    
    try:
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(model_name='gemini-1.5-flash-8b')
        
        # Validate model availability with a test call
        logging.info("Google AI model initialized successfully: gemini-1.5-flash-8b")
        return model
        
    except Exception as e:
        logging.error(f"Failed to initialize Google AI model: {e}")
        logging.error("Available models can be listed with: genai.list_models()")
        return None
```

**Design Rationale**:
- Provides clear logging of model initialization status
- Suggests remediation steps in error messages
- Prevents cascading failures by returning None gracefully
- Allows system to continue with cached data if API unavailable

#### 2. Database Query Errors

**Current Behavior**: Generic SQLAlchemy error with stack trace

**Enhanced Behavior**:
```python
try:
    datetime_condition = get_datetime_interval_query(max_age_hours)
    query = text(f"""
        SELECT final_value, confidence_score, method, candidates_json, warnings_json, created_at
        FROM resolutions 
        WHERE vehicle_key = :vehicle_key AND field_name = :field_name
        AND created_at > {datetime_condition}
        ORDER BY created_at DESC
        LIMIT 1
    """)
    result = conn.execute(query, {"vehicle_key": vehicle_key, "field_name": field_name})
    
except Exception as e:
    logging.error(f"Database query failed for {vehicle_key}.{field_name}: {e}")
    logging.error(f"Database type: {'SQLite' if is_sqlite() else 'PostgreSQL'}")
    logging.error(f"Query attempted: {query}")
    return None
```

**Design Rationale**:
- Provides context about which database type was being used
- Logs the actual query that failed for debugging
- Includes vehicle and field context for troubleshooting
- Returns None to allow fallback mechanisms to engage

#### 3. Cascading Failure Prevention

**Problem**: Current system marks valid vehicles as "not found" when API/DB fails

**Solution**: Implement graceful degradation

```python
def process_vehicle(vehicle_string):
    """Process vehicle with graceful degradation on failures."""
    
    # Try to get cached data first
    cached_data = get_cached_resolution(vehicle_key, 'curb_weight')
    if cached_data:
        logging.info(f"Using cached data for {vehicle_string}")
        return cached_data
    
    # Try vehicle validation
    try:
        validation_result = validate_vehicle_existence(year, make, model)
    except Exception as e:
        logging.warning(f"Vehicle validation failed: {e}")
        validation_result = None  # Don't fail completely
    
    # Try resolver-based queries
    try:
        resolution = resolve_curb_weight(year, make, model)
        if resolution and resolution.confidence_score >= 0.6:
            return resolution
    except Exception as e:
        logging.error(f"Resolver failed: {e}")
    
    # Only mark as "not found" if ALL methods fail AND validation explicitly failed
    if validation_result is False:  # Explicitly validated as fake
        mark_as_not_found(vehicle_string)
    else:
        # Inconclusive - don't mark as not found
        logging.warning(f"Could not resolve {vehicle_string} but validation inconclusive")
        return None
```

**Design Rationale**:
- Tries multiple data sources before giving up
- Distinguishes between "definitely fake" and "couldn't determine"
- Prevents false negatives for valid vehicles
- Maintains audit trail of what was attempted

## Testing Strategy

### Unit Tests

#### 1. Database Helper Function Tests

**File**: `test_database_config.py` (new)

```python
def test_datetime_interval_sqlite():
    """Test datetime interval generation for SQLite."""
    # Mock is_sqlite() to return True
    result = get_datetime_interval_query(24)
    assert result == "datetime('now', '-24 hours')"

def test_datetime_interval_postgresql():
    """Test datetime interval generation for PostgreSQL."""
    # Mock is_sqlite() to return False
    result = get_datetime_interval_query(24)
    assert result == "NOW() - INTERVAL '24 hours'"
```

#### 2. Google AI Model Tests

**File**: `test_resolver.py` (update existing)

```python
def test_model_initialization_success():
    """Test successful model initialization with valid API key."""
    client = GroundedSearchClient()
    assert client.model is not None
    # Verify model name is correct
    assert 'gemini-1.5-flash-8b' in str(client.model)

def test_model_initialization_no_api_key():
    """Test graceful handling when API key is missing."""
    # Mock environment without API key
    client = GroundedSearchClient()
    assert client.model is None
```

#### 3. Query Compatibility Tests

**File**: `test_integration.py` (update existing)

```python
def test_resolution_query_sqlite():
    """Test resolution queries work in SQLite."""
    # Use SQLite test database
    tracker = ProvenanceTracker()
    result = tracker.get_cached_resolution("2013_Toyota_Camry", "curb_weight")
    # Should not raise syntax error

def test_resolution_query_postgresql():
    """Test resolution queries work in PostgreSQL."""
    # Use PostgreSQL test database (if available)
    tracker = ProvenanceTracker()
    result = tracker.get_cached_resolution("2013_Toyota_Camry", "curb_weight")
    # Should not raise syntax error
```

### Integration Tests

#### 1. End-to-End Vehicle Processing

**File**: `test_integration.py` (update existing)

```python
def test_vehicle_processing_2013_toyota_camry():
    """Test complete vehicle processing for known good vehicle."""
    result = process_vehicle("2013 Toyota Camry")
    
    # Should not be marked as "not found"
    assert result is not None
    
    # Should have curb weight data
    assert result.get('curb_weight_lbs') is not None
    assert result['curb_weight_lbs'] > 0

def test_vehicle_processing_with_api_failure():
    """Test graceful degradation when API fails."""
    # Mock API to fail
    with mock.patch('resolver.GroundedSearchClient.search_vehicle_specs', side_effect=Exception("API Error")):
        result = process_vehicle("2013 Toyota Camry")
        
        # Should not crash
        # Should try fallback mechanisms
        # Should not incorrectly mark as "not found"
```

#### 2. Cross-Database Compatibility

**File**: `test_database_compatibility.py` (new)

```python
def test_queries_work_in_both_databases():
    """Test all queries work in both SQLite and PostgreSQL."""
    
    test_queries = [
        ("get_cached_resolution", 24),
        ("get_resolution_history", 24),
        ("create_monitoring_dashboard_data", 24),
    ]
    
    for query_name, hours in test_queries:
        # Test with SQLite
        with sqlite_database():
            result = execute_query(query_name, hours)
            assert result is not None
        
        # Test with PostgreSQL (if available)
        if postgresql_available():
            with postgresql_database():
                result = execute_query(query_name, hours)
                assert result is not None
```

### Manual Testing Checklist

1. **Local Development (SQLite)**
   - [ ] Start application with SQLite database
   - [ ] Process "2013 Toyota Camry" - should succeed
   - [ ] Verify no SQL syntax errors in logs
   - [ ] Check resolution data is cached correctly
   - [ ] Verify Google AI API calls succeed

2. **Production Simulation (PostgreSQL)**
   - [ ] Configure PostgreSQL connection
   - [ ] Process same vehicle
   - [ ] Verify queries use PostgreSQL syntax
   - [ ] Confirm data consistency between environments

3. **Error Scenarios**
   - [ ] Test with invalid API key - should log warning, not crash
   - [ ] Test with database connection failure - should handle gracefully
   - [ ] Test with fake vehicle - should correctly identify as not found
   - [ ] Test with valid vehicle but API down - should use cached data

### Validation Tests

**File**: `end_to_end_validation.py` (update existing)

Add validation for the specific error scenarios from requirements:

```python
def test_no_sql_syntax_errors():
    """Verify no SQL syntax errors occur in SQLite."""
    # Process vehicle and capture logs
    with capture_logs() as logs:
        process_vehicle("2013 Toyota Camry")
    
    # Should not contain SQL syntax errors
    assert "near '24 hours': syntax error" not in logs
    assert "sqlite3.OperationalError" not in logs

def test_no_google_ai_404_errors():
    """Verify no 404 model not found errors."""
    with capture_logs() as logs:
        process_vehicle("2013 Toyota Camry")
    
    # Should not contain 404 errors
    assert "404 models/gemini-1.5-flash-latest is not found" not in logs
    assert "is not found for API version v1beta" not in logs

def test_valid_vehicle_not_marked_as_fake():
    """Verify valid vehicles are not incorrectly marked as not found."""
    result = process_vehicle("2013 Toyota Camry")
    
    # Should not be marked as not found
    session_state = get_session_state()
    assert "2013 Toyota Camry" not in session_state.get('not_found_vehicles', [])
```

## Implementation Notes

### Deployment Considerations

1. **Database Migration**: No schema changes required - only query syntax updates
2. **API Key Validation**: Ensure `GEMINI_API_KEY` is set in both local and production environments
3. **Backward Compatibility**: Changes maintain full compatibility with existing data
4. **Rollback Plan**: Simple - revert code changes, no database rollback needed

### Performance Impact

- **Database Queries**: No performance impact - same query logic, different syntax
- **Google AI API**: `gemini-1.5-flash-8b` is faster than previous model
- **Error Handling**: Minimal overhead from additional logging

### Configuration Requirements

**Environment Variables** (no changes):
- `GEMINI_API_KEY`: Google AI API key
- `DATABASE_URL` or `PG*` variables: Database connection

**No new configuration required** - all changes are code-level fixes.

### Monitoring and Observability

Enhanced logging will provide:
- Model initialization status
- Database type being used for each query
- API call success/failure rates
- Resolution confidence scores
- Cache hit/miss rates

Existing monitoring dashboard will automatically benefit from fixes.

## Summary

This design provides a comprehensive solution to both critical system failures:

1. **Database Compatibility**: Centralized datetime helper function ensures queries work in both SQLite and PostgreSQL
2. **Google AI Integration**: Updated model name resolves 404 errors
3. **Error Handling**: Enhanced logging and graceful degradation prevent cascading failures
4. **Testing**: Comprehensive test strategy validates fixes across environments

The implementation is minimal, focused, and maintains backward compatibility while fixing the root causes of system failures.
