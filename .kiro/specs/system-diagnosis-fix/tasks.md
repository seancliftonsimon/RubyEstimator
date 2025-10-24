# Implementation Plan

- [x] 1. Add database-agnostic datetime helper function





  - Create `get_datetime_interval_query()` function in `database_config.py` that returns appropriate SQL syntax based on database type (SQLite vs PostgreSQL)
  - Function should accept hours parameter and return database-specific datetime comparison string
  - Leverage existing `is_sqlite()` function for database detection
  - _Requirements: 1.1, 1.2, 1.4_


- [x] 2. Update Google AI model name in resolver module




  - Change model name from `gemini-1.5-flash-latest` to `gemini-1.5-flash-8b` in `resolver.py` line 84
  - Add logging to confirm successful model initialization
  - Add error handling for model initialization failures
  - _Requirements: 2.1, 2.2, 2.3_




- [x] 3. Update Google AI model name in vehicle_data module

  - Change model name from `gemini-1.5-flash-latest` to `gemini-1.5-flash-8b` in `vehicle_data.py` line 31
  - Ensure consistent model usage across the application
  - _Requirements: 2.1, 2.2_

- [x] 4. Fix database queries in resolver.py






- [x] 4.1 Update get_cached_resolution method (line 792)

  - Import `get_datetime_interval_query` from `database_config`
  - Replace hardcoded `NOW() - INTERVAL '%s hours'` with call to `get_datetime_interval_query(max_age_hours)`
  - Test query works in both SQLite and PostgreSQL
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 4.2 Update create_monitoring_dashboard_data method (lines 952, 961, 978)


  - Replace three instances of `NOW() - INTERVAL '24 hours'` with `get_datetime_interval_query(24)`
  - Ensure all monitoring queries use database-agnostic syntax
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 4.3 Update optimize_database_performance method (line 1047)


  - Replace `NOW() - INTERVAL '7 days'` with `get_datetime_interval_query(168)` (7 days = 168 hours)
  - Ensure cleanup query works in both database types
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 5. Fix database query in vehicle_data.py (line 258)





  - Import `get_datetime_interval_query` from `database_config`
  - Replace `NOW() - INTERVAL '24 hours'` with call to `get_datetime_interval_query(24)`
  - Verify resolution data retrieval works correctly
  - _Requirements: 1.1, 1.2, 1.3, 5.2_
-

- [x] 6. Fix database queries in monitoring_dashboard.py





  - Update all queries with `NOW() - INTERVAL` syntax (lines 231, 299, 349)
  - Replace with appropriate `get_datetime_interval_query()` calls
  - Ensure monitoring dashboard works in both environments
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 7. Enhance error handling and logging




- [x] 7.1 Add detailed error logging for database operations


  - Add try-catch blocks around database queries with context logging
  - Log database type (SQLite/PostgreSQL) when errors occur
  - Include vehicle_key and field_name in error messages
  - _Requirements: 3.1, 3.2, 3.4_

- [x] 7.2 Add detailed error logging for Google AI API calls


  - Log model initialization status
  - Log API call failures with request details
  - Provide user-friendly error messages for common failures
  - _Requirements: 3.2, 3.3, 3.4, 2.4_



- [ ] 7.3 Implement graceful degradation for vehicle processing

  - Update vehicle processing logic to try cached data first
  - Implement fallback mechanisms when API calls fail
  - Prevent marking valid vehicles as "not found" when validation is inconclusive
  - _Requirements: 2.4, 5.4, 5.5_

- [ ] 8. Update environment configuration display



  - Enhance database connection status display in app.py
  - Show clear indication of SQLite vs PostgreSQL mode
  - Display Google AI API configuration status
  - _Requirements: 4.1, 4.2, 4.5_

- [ ] 9. Validate fixes with end-to-end testing



  - Test "2013 Toyota Camry" vehicle processing in SQLite environment
  - Verify no SQL syntax errors occur
  - Verify no Google AI 404 errors occur
  - Confirm vehicle is not incorrectly marked as "not found"
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ]* 10. Create unit tests for database helper function
  - Write test for SQLite datetime query generation
  - Write test for PostgreSQL datetime query generation
  - Verify correct syntax for various hour values
  - _Requirements: 1.1, 1.2_

- [ ]* 11. Create integration tests for cross-database compatibility
  - Test resolution queries work in SQLite
  - Test resolution queries work in PostgreSQL (if available)
  - Verify data consistency between environments
  - _Requirements: 1.3, 1.4_

- [ ]* 12. Update validation tests
  - Add test to verify no SQL syntax errors occur
  - Add test to verify no Google AI 404 errors occur
  - Add test to verify valid vehicles are not marked as fake
  - _Requirements: 5.1, 5.2, 5.5_
