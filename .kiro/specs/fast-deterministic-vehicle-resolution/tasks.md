# Implementation Plan

- [x] 1. Set up core data models and validation





  - Create VehicleSpecification, NormalizedVehicle, and ResolutionResult dataclasses
  - Implement validation functions for curb weight bounds checking and unit conversion
  - Define FieldEnum for closed field name validation
  - _Requirements: 2.2, 2.3, 7.1, 7.2_

- [x] 2. Implement simple Normalization Engine





  - [x] 2.1 Create exact matching system for vehicle make/model names


    - Build simple case-insensitive exact matching against known make/model list
    - Return "manual search needed" error for unrecognized makes/models
    - _Requirements: 2.1, 2.4_
  
  - [x] 2.2 Implement field name normalization and validation


    - Create closed enum validation for field names (curb_weight, aluminum_engine, aluminum_rims, catalytic_converters)
    - Implement sub-5ms rejection for invalid field names
    - _Requirements: 2.2, 2.3_
  
  - [x] 2.3 Add year range validation


    - Implement year bounds checking with immediate rejection
    - _Requirements: 2.5_

- [x] 3. Create Source Router with deterministic routing





  - [x] 3.1 Build make-specific source mapping system


    - Create static routing tables mapping vehicle makes to primary sources
    - Implement priority system for official manufacturer pages
    - _Requirements: 3.1, 3.4, 3.5_
  
  - [x] 3.2 Implement fallback source selection


    - Add logic to select up to 2 fallback sources when primary sources unavailable
    - Ensure routing completion within 150ms
    - _Requirements: 3.2, 3.3_

- [x] 4. Develop Parallel HTTP Fetcher





  - [x] 4.1 Implement concurrent HTTP request handling


    - Create parallel request executor with maximum 3 concurrent requests
    - Add 2.5 second timeout enforcement per request
    - _Requirements: 4.1, 4.2_
  
  - [x] 4.2 Build structured data extraction system


    - Implement CSS/XPath selectors for known sources
    - Add early termination when primary sources provide all required fields
    - _Requirements: 4.4, 4.5_
  
  - [x] 4.3 Add primary source success optimization


    - Skip fallback requests when primary sources succeed
    - _Requirements: 4.3_

- [x] 5. Create Evidence Store with intelligent caching





  - [x] 5.1 Implement cache key generation and lookup system


    - Create composite cache keys using (year, make, model, drivetrain, engine)
    - Build fast lookup mechanism for cached results
    - _Requirements: 5.4_
  
  - [x] 5.2 Add TTL-based caching with different policies

    - Implement 30-day TTL for positive results
    - Add 6-hour TTL for negative results (404 responses)
    - _Requirements: 5.1, 5.2_
  
  - [x] 5.3 Build evidence payload storage system

    - Store complete evidence payloads with source quotes and URLs
    - Implement source attribution tracking
    - _Requirements: 5.3, 5.5_

- [x] 6. Implement Micro LLM Resolver





  - [x] 6.1 Create structured conflict resolution system


    - Implement single LLM call per resolution request with 400ms timeout
    - Use temperature 0 for deterministic outputs
    - _Requirements: 6.1, 6.2, 6.3_
  
  - [x] 6.2 Add intelligent value selection logic


    - Only resolve conflicts between structured candidates
    - Echo clear primary source values without modification
    - _Requirements: 6.4, 6.5_

- [-] 7. Build comprehensive error handling and validation





  - [x] 7.1 Implement input validation and bounds checking




    - Add unit stripping and formatting for numeric values
    - Implement vehicle-type-specific curb weight validation
    - _Requirements: 7.1, 7.2_
  
  - [ ] 7.2 Create timeout and failure handling system
    - Return partial results with confidence indicators on timeouts
    - Implement structured error logging with error codes
    - _Requirements: 7.3, 7.4_
  
  - [ ] 7.3 Add fallback value system
    - Provide fallback values when primary sources fail completely
    - _Requirements: 7.5_

- [x] 8. Create main resolution orchestrator





  - [x] 8.1 Build end-to-end resolution pipeline


    - Integrate all components into single resolution flow
    - Ensure P50 < 8s and P95 < 15s performance targets
    - _Requirements: 1.1, 1.2, 1.3_
  
  - [x] 8.2 Add deterministic result guarantee


    - Ensure identical inputs produce identical outputs
    - _Requirements: 1.5_
  
  - [x] 8.3 Implement primary source fast path


    - Return results within 5 seconds when primary sources available
    - _Requirements: 1.4_

- [ ]* 9. Add performance monitoring and testing
  - [ ]* 9.1 Create performance benchmarking suite
    - Build load testing for 100 requests/second sustained load
    - Add response time percentile tracking (P50, P90, P95, P99)
    - _Requirements: 1.1, 1.2, 1.3_
  
  - [ ]* 9.2 Implement integration tests for source reliability
    - Create mock HTTP response testing framework
    - Add real source integration tests
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [ ]* 9.3 Add data quality validation tests
    - Test bounds checking accuracy
    - Validate unit conversion precision
    - Test fuzzy matching precision/recall
    - _Requirements: 2.1, 2.4, 7.1, 7.2_