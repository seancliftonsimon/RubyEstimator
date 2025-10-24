# Implementation Plan

- [x] 1. Set up core resolver infrastructure and data models





  - Create resolver module with GroundedSearchClient, ConsensusResolver, and ProvenanceTracker classes
  - Implement SearchCandidate, ResolutionResult, and ResolutionRecord dataclasses
  - Set up database schema extensions for resolutions table
  - _Requirements: 1.1, 2.1, 5.4_

- [x] 1.1 Implement GroundedSearchClient for Google AI integration


  - Create search_vehicle_specs method to query Google AI with grounded search
  - Implement get_multiple_candidates method to collect diverse candidate values
  - Add response parsing and validation for numeric vehicle specifications
  - _Requirements: 1.1, 2.1_

- [x] 1.2 Build ConsensusResolver with clustering and confidence algorithms


  - Implement resolve_field method with similarity-based clustering
  - Create detect_outliers method using statistical thresholds
  - Build calculate_confidence method based on agreement and spread metrics
  - _Requirements: 2.2, 2.3, 2.4_

- [x] 1.3 Create ProvenanceTracker for resolution history management


  - Implement create_resolution_record method for database storage
  - Build get_resolution_history method for audit trail retrieval
  - Add resolution caching and lookup optimization



  - _Requirements: 5.1, 5.2, 5.3_

- [x] 2. Extend database schema and admin configuration system

  - Add resolutions table with proper indexes and constraints
  - Extend app_config table with grounding and consensus settings
  - Create database migration utilities for schema updates
  - _Requirements: 3.2, 3.4_

- [x] 2.1 Create database migration for resolutions table


  - Write SQL schema for resolutions table with vehicle_key, field_name, and JSONB columns
  - Add proper indexes for fast lookups by vehicle and field combinations



  - Implement database migration function in database_config.py
  - _Requirements: 5.4, 5.5_

- [x] 2.2 Extend admin settings with grounding configuration
  - Add grounding_settings and consensus_settings to default configuration
  - Create admin UI sections for target candidates, clustering tolerance, and confidence thresholds
  - Implement settings validation and persistence in app_config table
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 3. Integrate resolver layer with existing vehicle processing



  - Modify process_vehicle function to use new resolver system



  - Replace direct API calls with consensus-based resolution
  - Add fallback logic for resolver failures
  - _Requirements: 1.1, 2.1, 2.2_

- [x] 3.1 Update vehicle_data.py to use resolver system
  - Replace get_curb_weight_from_api with resolver-based approach
  - Modify aluminum_engine and aluminum_rims detection to use consensus
  - Integrate resolution caching with existing database lookups
  - _Requirements: 1.1, 2.1, 2.2_



- [x] 3.2 Implement resolver fallback and error handling
  - Add graceful degradation when grounded search fails
  - Implement retry logic with exponential backoff for API calls
  - Create error logging and monitoring for resolution failures
  - _Requirements: 1.3, 2.5_


- [ ] 4. Enhance UI with confidence indicators and provenance display

  - Add confidence badges (green/amber/red) to result displays
  - Create provenance panel showing sources and resolution methods
  - Implement warning banners for low-confidence estimates
  - _Requirements: 1.2, 1.4, 5.1, 5.2, 6.3_

- [ ] 4.1 Create confidence indicator components
  - Build confidence badge component with color-coded status
  - Add plain-English explanations for confidence levels
  - Implement warning banners for manual review requirements
  - _Requirements: 1.4, 1.5, 6.3_

- [ ] 4.2 Build provenance panel for source transparency
  - Create expandable panel showing resolution method and candidate sources
  - Add clickable citations linking back to original sources
  - Display confidence scores and outlier detection results
  - _Requirements: 5.1, 5.2, 5.3_

- [ ] 4.3 Update results tables with enhanced data presentation
  - Modify commodity tables to show confidence indicators inline
  - Add tooltips with provenance information for each resolved value
  - Implement visual highlighting for low-confidence or flagged values
  - _Requirements: 6.1, 6.2, 6.4_

- [x] 5. Implement Nut fee toggle and pricing rule enhancements



  - Add admin toggle for Nut fee calculation (ELV vs curb weight)
  - Ensure tires are consistently treated as revenue items
  - Validate sign conventions for all revenue and cost calculations
  - _Requirements: 3.5, 4.1, 4.2, 4.3, 4.5_

- [x] 5.1 Add Nut fee calculation toggle to admin interface


  - Create admin setting for nut_fee_applies_to with ELV/curb options
  - Update calculate_totals function to respect the toggle setting
  - Add validation to ensure setting changes apply immediately
  - _Requirements: 3.5, 4.4_



- [x] 5.2 Validate and enforce pricing sign conventions




  - Audit all revenue calculations to ensure positive values
  - Verify all cost calculations use negative values consistently
  - Update Net calculation to be Gross + Costs (where Costs are negative)
  - _Requirements: 4.2, 4.3, 4.4_

- [ ] 6. Add comprehensive testing and validation

  - Create unit tests for resolver components and consensus algorithms
  - Build integration tests for end-to-end resolution workflows
  - Add data quality tests with known vehicle verification
  - _Requirements: 1.1, 2.1, 2.2, 2.3_

- [ ]* 6.1 Write unit tests for resolver components
  - Test ConsensusResolver clustering and outlier detection algorithms
  - Create mock tests for GroundedSearchClient API interactions
  - Add tests for ProvenanceTracker database operations
  - _Requirements: 2.2, 2.3, 2.4_

- [ ]* 6.2 Build integration tests for resolution workflows
  - Test complete vehicle resolution from input to database storage
  - Verify admin settings changes affect resolution behavior
  - Add tests for error handling and fallback scenarios
  - _Requirements: 1.1, 2.1, 3.2_

- [ ]* 6.3 Create data quality validation tests
  - Test resolver accuracy against manually verified vehicle data
  - Add regression tests for existing vehicle database entries
  - Implement performance tests for concurrent resolution requests
  - _Requirements: 1.1, 2.1, 2.2_

- [ ] 7. Optimize performance and add monitoring
  - Implement resolution caching with intelligent invalidation
  - Add request deduplication for identical grounded searches
  - Create logging and monitoring for resolution quality metrics
  - _Requirements: 1.1, 2.1, 5.4_

- [ ] 7.1 Implement intelligent resolution caching
  - Add TTL-based caching for resolution results based on confidence scores
  - Create cache invalidation logic for low-confidence resolutions
  - Optimize database queries with proper indexing for resolution lookups
  - _Requirements: 5.4, 5.5_

- [ ] 7.2 Add resolution quality monitoring and logging
  - Implement detailed logging for all resolution attempts and results
  - Create metrics tracking for confidence score distributions
  - Add monitoring alerts for high failure rates or low confidence trends
  - _Requirements: 1.3, 2.5_

- [x] 8. Complete and polish remaining implementation





  - Finalize all UI enhancements with confidence indicators and provenance display
  - Implement comprehensive testing suite covering all resolver components
  - Add performance optimizations and monitoring capabilities
  - Conduct end-to-end validation and bug fixes
  - _Requirements: All remaining requirements_

- [x] 8.1 Finalize UI enhancements and user experience


  - Complete confidence indicator implementation across all result displays
  - Build and integrate provenance panels for source transparency
  - Add interactive tooltips and visual highlighting for data quality indicators
  - Ensure consistent styling and responsive design across all new components
  - _Requirements: 1.2, 1.4, 1.5, 5.1, 5.2, 6.1, 6.2, 6.3, 6.4_


- [x] 8.2 Complete testing and quality assurance

  - Implement full unit test coverage for all resolver components
  - Build comprehensive integration tests for end-to-end workflows
  - Add data quality validation tests with known vehicle benchmarks
  - Create performance and load testing for concurrent resolution requests
  - Validate error handling and fallback scenarios under various failure conditions
  - _Requirements: 1.1, 2.1, 2.2, 2.3, 2.4, 3.2_

- [x] 8.3 Implement production-ready monitoring and optimization


  - Deploy intelligent caching with TTL-based invalidation strategies
  - Add comprehensive logging and metrics collection for resolution quality
  - Implement request deduplication and performance optimizations
  - Create monitoring dashboards and alerting for system health
  - Optimize database queries and indexing for production scale
  - _Requirements: 1.1, 1.3, 2.1, 2.5, 5.4, 5.5_



- [-] 8.4 Final validation and deployment preparation



  - Conduct thorough end-to-end testing with real vehicle data
  - Validate all admin configuration changes work correctly
  - Ensure backward compatibility with existing vehicle database
  - Document new features and configuration options
  - Prepare deployment checklist and rollback procedures
  - _Requirements: All system requirements_