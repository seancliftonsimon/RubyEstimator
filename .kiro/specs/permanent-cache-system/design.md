# Design Document

## Overview

This design transforms the Ruby GEM Estimator's resolution caching from a time-limited cache to a permanent knowledge base. The system will eliminate all time-based cache invalidation logic, allowing resolution data to persist indefinitely. This approach reduces API costs over time as the database accumulates more vehicle data.

## Architecture

### Current Architecture Issues

The current system has time-based cache invalidation at multiple layers:

1. **ProvenanceTracker.get_cached_resolution()** - Uses `max_age_hours` parameter (default 24 hours)
2. **get_resolution_data_from_db()** in vehicle_data.py - Filters by 24-hour window
3. **Monitoring Dashboard queries** - Filter by 24 hours or 7 days
4. **Database cleanup logic** - May exist for removing old records

### New Architecture

The new architecture removes time-based filtering from cache lookups while preserving it only for monitoring/analytics:

```
┌─────────────────────────────────────────┐
│         Resolution Request              │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│    Check Database (No Time Filter)      │
│    - Query by vehicle_key + field_name  │
│    - Return most recent record          │
└──────────────┬──────────────────────────┘
               │
         ┌─────┴─────┐
         │           │
    Found│           │Not Found
         ▼           ▼
┌─────────────┐  ┌──────────────────┐
│Return Cached│  │ Call Google AI   │
│   Result    │  │  Grounded Search │
└─────────────┘  └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Store Resolution │
                 │  (Permanent)     │
                 └──────────────────┘
```

## Components and Interfaces

### 1. ProvenanceTracker Modifications

**Modified Methods:**

```python
def get_cached_resolution(self, vehicle_key: str, field_name: str) -> Optional[ResolutionResult]:
    """
    Get cached resolution if available (no time limit).
    
    Args:
        vehicle_key: Vehicle identifier
        field_name: Field name
        
    Returns:
        ResolutionResult if cached, None otherwise
    """
```

**Changes:**
- Remove `max_age_hours` parameter
- Remove time-based filtering from database query
- Query for most recent record by `created_at DESC LIMIT 1`
- Remove intelligent TTL logic based on confidence scores

### 2. vehicle_data.py Modifications

**Modified Function:**

```python
def get_resolution_data_from_db(year, make, model):
    """
    Checks the resolutions table for cached resolver data (no time limit).
    
    Returns all fields for the vehicle regardless of age.
    """
```

**Changes:**
- Remove `get_datetime_interval_query()` usage
- Remove `created_at > datetime_condition` filter
- Query for most recent records per field using `ORDER BY created_at DESC`
- Keep confidence threshold filtering (only use high-confidence results)

### 3. Monitoring Dashboard Modifications

**Strategy:**
- Keep time-based filtering for analytics/monitoring purposes
- Add "All Time" option to time range selectors
- Default to showing recent data (24h/7d) but allow viewing all data
- Add knowledge base growth metrics

**New Metrics:**
- Total resolutions (all time)
- Unique vehicles in knowledge base
- Unique fields resolved
- Knowledge base coverage percentage
- API call reduction rate

### 4. Database Schema

**No changes required** - existing schema supports permanent storage:

```sql
CREATE TABLE resolutions (
    id SERIAL PRIMARY KEY,
    vehicle_key VARCHAR(100) NOT NULL,
    field_name VARCHAR(50) NOT NULL,
    final_value FLOAT,
    confidence_score FLOAT,
    method VARCHAR(50),
    candidates_json JSONB,
    warnings_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vehicle_key, field_name)
)
```

The `UNIQUE(vehicle_key, field_name)` constraint ensures only one record per vehicle-field combination, automatically updating on conflict.

## Data Models

### ResolutionResult (No Changes)

```python
@dataclass
class ResolutionResult:
    final_value: float
    confidence_score: float
    method: str
    candidates: List[SearchCandidate]
    outliers: List[bool]
    warnings: List[str]
```

### Cache Lookup Flow

**Before:**
```
Query: WHERE vehicle_key = ? AND field_name = ? AND created_at > NOW() - INTERVAL '24 hours'
Result: Recent record or None
```

**After:**
```
Query: WHERE vehicle_key = ? AND field_name = ? ORDER BY created_at DESC LIMIT 1
Result: Most recent record (any age) or None
```

## Error Handling

### Backward Compatibility

- Existing resolution records remain valid
- No migration required
- Old records with any `created_at` timestamp are usable

### Confidence Threshold Handling

- Continue filtering by confidence threshold (default 0.7)
- Low-confidence cached results are ignored
- This ensures data quality without time-based invalidation

### Database Query Failures

- Maintain existing error handling
- Log failures but don't crash
- Fall back to API call if cache lookup fails

## Testing Strategy

### Unit Tests

1. **Test cache lookup without time filter**
   - Verify old records are retrieved
   - Verify most recent record is selected when multiple exist
   - Verify confidence filtering still works

2. **Test resolution storage**
   - Verify UPSERT behavior (update on conflict)
   - Verify all fields are stored correctly
   - Verify created_at is updated on conflict

3. **Test monitoring queries**
   - Verify time-filtered queries still work for analytics
   - Verify "all time" queries return complete dataset
   - Verify metrics calculations are accurate

### Integration Tests

1. **Test complete resolution flow**
   - First lookup: No cache, calls API, stores result
   - Second lookup: Uses cached result (immediate)
   - Third lookup (days later): Still uses cached result

2. **Test API cost reduction**
   - Track API calls for repeated vehicle lookups
   - Verify zero API calls after first resolution
   - Measure cost savings over time

### Manual Testing

1. **Test with real vehicles**
   - Look up vehicle multiple times over several days
   - Verify no repeated API calls
   - Verify consistent results from cache

2. **Test monitoring dashboard**
   - Verify all-time metrics display correctly
   - Verify time-range selectors work
   - Verify knowledge base growth is visible

## Migration Plan

### Phase 1: Code Changes
- Update ProvenanceTracker.get_cached_resolution()
- Update get_resolution_data_from_db()
- Remove max_age_hours parameters from all call sites

### Phase 2: Monitoring Updates
- Add all-time metrics to dashboard
- Add knowledge base growth visualizations
- Keep time-filtered views for recent activity

### Phase 3: Validation
- Monitor API call reduction
- Verify cache hit rates increase over time
- Confirm no regressions in data quality

### Phase 4: Documentation
- Update code comments
- Document manual cleanup procedures
- Update system architecture documentation

## Performance Considerations

### Database Query Performance

- Existing indexes support efficient lookups:
  - `idx_resolutions_vehicle_field` on (vehicle_key, field_name)
  - `idx_resolutions_created_at` on (created_at)
- No performance degradation expected from removing time filter

### Database Growth

- Estimate: ~100 bytes per resolution record
- 10,000 vehicles × 4 fields = 40,000 records = ~4 MB
- 100,000 vehicles × 4 fields = 400,000 records = ~40 MB
- Growth is manageable for years of operation

### Cache Hit Rate Improvement

- Current: Cache expires after 24 hours
- New: Cache never expires
- Expected improvement: 90%+ cache hit rate after initial population

## Administrative Tools

### Manual Cleanup (Future Enhancement)

If database size becomes a concern, provide admin tools to:

1. **Delete by confidence threshold**
   - Remove all resolutions below certain confidence
   - Useful for cleaning up low-quality data

2. **Delete by vehicle age**
   - Remove resolutions for vehicles older than X years
   - Useful if focusing on recent vehicles

3. **Delete by field**
   - Remove specific fields if no longer needed
   - Useful for schema changes

4. **Bulk export/import**
   - Export knowledge base for backup
   - Import curated datasets

These tools are not part of the initial implementation but should be considered for future development.
