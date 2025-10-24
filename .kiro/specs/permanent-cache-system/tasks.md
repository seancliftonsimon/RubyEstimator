# Implementation Plan

- [x] 1. Update ProvenanceTracker cache lookup method
  - Remove `max_age_hours` parameter from `get_cached_resolution()` method signature
  - Remove time-based filtering from database query (remove `get_datetime_interval_query()` usage)
  - Update query to select most recent record: `ORDER BY created_at DESC LIMIT 1`
  - Remove intelligent TTL logic based on confidence scores
  - Update method docstring to reflect permanent caching behavior
  - _Requirements: 1.1, 1.2, 4.1, 4.2, 4.3_

- [x] 2. Update vehicle_data.py cache lookup functions
  - Modify `get_resolution_data_from_db()` to remove time-based filtering
  - Remove `get_datetime_interval_query()` calls from the function
  - Update query to retrieve most recent records per field without time constraints
  - Keep confidence threshold filtering (only use high-confidence results)
  - Update function docstring to reflect permanent caching
  - _Requirements: 1.1, 1.2, 4.3_

- [x] 3. Update all call sites that use max_age_hours parameter
  - Find all calls to `get_cached_resolution()` with `max_age_hours` argument
  - Remove the `max_age_hours` parameter from all call sites
  - Update calls in `get_curb_weight_from_resolver()`
  - Update calls in `get_aluminum_engine_from_resolver()`
  - Update calls in `get_aluminum_rims_from_resolver()`
  - Update any other resolver functions that use cached resolutions
  - _Requirements: 1.1, 4.2_

- [x] 4. Update monitoring dashboard for permanent cache
  - Modify `render_time_based_analysis()` to keep time filtering for analytics
  - Modify `render_field_analysis()` to keep time filtering for analytics
  - Modify `render_vehicle_analysis()` to keep time filtering for analytics
  - Add "All Time" metrics section showing total knowledge base statistics
  - Add knowledge base growth metrics (total resolutions, unique vehicles, unique fields)
  - Update dashboard queries to support both time-filtered and all-time views
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 5. Add knowledge base statistics to monitoring dashboard
  - Create new function `render_knowledge_base_stats()` for all-time metrics
  - Query total resolution count across all time
  - Query unique vehicle count in knowledge base
  - Query unique field count resolved
  - Display cache hit rate and API call reduction metrics
  - Add visualization for knowledge base growth over time
  - _Requirements: 2.2, 2.3_

- [x] 6. Remove obsolete database cleanup logic from resolver.py





  - Locate `optimize_database_performance()` function in resolver.py
  - Remove the cleanup query that deletes old low-confidence records
  - Update function to only perform index optimization and statistics updates
  - Update function docstring to reflect that no automatic deletion occurs
  - _Requirements: 3.1, 3.2_

- [x] 7. Verify and test permanent caching behavior





  - Test cache lookup retrieves old records (simulate by setting old created_at)
  - Test most recent record is selected when multiple records exist
  - Test confidence filtering still works correctly
  - Test UPSERT behavior updates existing records
  - Verify no API calls occur for cached vehicles
  - _Requirements: 1.1, 1.2, 1.3, 4.4_
