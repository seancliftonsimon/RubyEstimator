# Implementation Plan

- [x] 1. Remove existing search stack components and create core two-pass infrastructure





  - Delete StagedVehicleResolver class and all staged resolution logic from staged_vehicle_resolver.py
  - Remove ConsensusResolver mean/std calculations and synthetic source generation from resolver.py
  - Disable all fallback resolver mechanisms and "±5%" synthetic sources
  - Create new two_pass_search_extract.py module with core infrastructure
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
-

- [x] 2. Implement Pass A: Search Component




  - Create PassASearcher class with Google AI client integration
  - Implement collect_excerpts method for parallel field searches
  - Implement search_single_field method with grounded web search
  - Add trust heuristic source prioritization (government 1.0, major spec 0.85, parts 0.7, forums 0.4)
  - Implement URL deduplication while preserving excerpt content
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 3. Implement Pass B: Extract Component  



  - Create PassBExtractor class with temperature 0 for deterministic extraction
  - Implement extract_all_fields method for structured data extraction from excerpts
  - Implement extract_single_field method with evidence tracking
  - Add strict type enforcement for curb_weight_lbs (float), catalytic_converters (int), aluminum specs (bool)
  - Ensure every extracted value includes URL and quote evidence
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 4. Implement Deterministic Collation Engine





  - Create DeterministicCollator class with mathematical rules
  - Implement collate_numeric_weight method using median with 10% trim for curb weight
  - Implement collate_integer_count method using mode for catalytic converters, unknown on ties
  - Implement collate_boolean_material method using majority for aluminum specs, unknown on ties
  - Implement confidence calculation using 70% spread/majority + 30% average trust weight, clamped 0.3-0.95
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 5. Create evidence persistence layer and database schema updates





  - Create attribute_evidence table with vehicle_id, field, url, quote, parsed_value, unit columns
  - Add confidence tracking columns to vehicles table (confidence_curb_weight, confidence_aluminum_engine, etc.)
  - Add needs_review boolean column to vehicles table
  - Implement EvidenceTracker class for storing grounded evidence with URL validation
  - Ensure every evidence row maps to real Pass-A URL with no synthetic entries
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 6. Implement SearchExtractOrchestrator as single entry point




  - Create SearchExtractOrchestrator class coordinating Pass A and Pass B
  - Implement resolve_vehicle method as single entry point for vehicle resolution
  - Add error handling for Pass A/B failures with graceful degradation
  - Implement calculate_overall_confidence using median of individual field confidences
  - Remove all old "overall confidence" rollup calculations from previous system
  - _Requirements: 7.3, 7.4, 7.5_
-


- [-] 7. Update vehicle_data.py to use two-pass system




  - Replace all calls to StagedVehicleResolver with SearchExtractOrchestrator
  - Remove imports and references to ConsensusResolver and synthetic source generation
  - Update process_vehicle function to use new two-pass entry point
  - Maintain backward compatibili


ty for UI integration
  - _Requirements: 1.1, 1.5, 7.3_

- [ ] 8. Update UI components for new confidence display

  - Modify confidence_ui.py to display final value plus confidence score plus up to 3 citations with URLs
  - Add "Insufficient explicit evidence" message display when value is unknown
  - Update citation rendering to show URL and quote evidence from Pass A
  - Remove old confidence rollup display components
  - _Requirements: 7.1, 7.2_

- [ ]* 9. Create comprehensive test suite for two-pass system
  - Write unit tests for PassASearcher excerpt collection and deduplication
  - Write unit tests for PassBExtractor type enforcement and evidence tracking
  - Write unit tests for DeterministicCollator mathematical rules with various evidence combinations
  - Write integration tests for SearchExtractOrchestrator end-to-end flow
  - Write database tests for evidence persistence and URL validation
  - _Requirements: All requirements validation_

- [ ]* 10. Add performance monitoring and error handling
  - Implement processing metrics tracking (pass_a_duration, pass_b_duration, total_api_calls)
  - Add retry logic with exponential backoff for network timeouts
  - Implement connection pooling for database operations
  - Add logging for confidence distribution and system health assessment
  - Create error response format for network, parsing, no_data, and timeout errors
  - _Requirements: Error handling and performance optimization_