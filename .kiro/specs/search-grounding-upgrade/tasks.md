# Implementation Plan

- [x] 1. Set up new SDK and dependencies











  - Install google-genai SDK version 1.0.0 or higher
  - Update requirements.txt with new dependency
  - Remove or deprecate google.generativeai dependency
  - Test SDK installation and basic functionality
  - _Requirements: 1.1, 1.2, 4.2_

- [ ] 2. Create enhanced grounding metadata handler
  - Implement GroundingMetadataHandler class for metadata extraction
  - Add methods for extracting search queries, grounding chunks, and source URLs
  - Implement comprehensive logging for grounding information
  - Create utility functions for metadata processing
  - _Requirements: 3.1, 5.1, 5.2, 5.3_



- [ ] 3. Upgrade GroundedSearchClient in resolver.py
  - Replace google.generativeai imports with google genai imports
  - Update client initialization to use genai.Client() pattern
  - Convert all API calls to use client.models.generate_content() method
  - Update tool specification to use config-based pattern: config={"tools": [{"google_search": {}}]}


  - Integrate grounding metadata extraction into search methods

  - _Requirements: 1.1, 1.2, 2.1, 2.3, 3.1_

- [ ] 4. Upgrade vehicle data functions in vehicle_data.py
  - Replace SHARED_GEMINI_MODEL with SHARED_GEMINI_CLIENT using new SDK
  - Update all vehicle data functions to use client-based API calls
  - Convert tool specifications to config-based pattern in all functions
  - Add grounding metadata logging to all search operations
  - Update error handling for new SDK error types
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 5.1, 5.4_

- [ ] 5. Implement enhanced error handling
  - Create SDK-specific error handling functions
  - Update existing error handling to work with new SDK error types
  - Implement graceful fallback mechanisms for API failures
  - Add detailed logging with SDK version and error context
  - Test error scenarios and fallback behavior
  - _Requirements: 1.4, 2.4, 5.4_

- [ ] 6. Update model configuration and selection
  - Upgrade to Gemini 2.0+ models (gemini-2.5-flash recommended)
  - Update model selection logic to use new model IDs
  - Implement configuration management for model selection
  - Test compatibility with different Gemini model versions
  - _Requirements: 1.3, 4.4_

- [ ] 7. Enhance SearchCandidate data model
  - Add new fields for grounding metadata (grounding_chunk_id, search_query, source_url)
  - Update candidate parsing to include metadata information
  - Ensure backward compatibility with existing candidate processing
  - Test data model changes with existing resolution logic
  - _Requirements: 3.1, 3.2_

- [ ] 8. Implement comprehensive testing suite
  - Create tests for new SDK integration and client initialization
  - Test config-based tool specification across all functions
  - Verify grounding metadata extraction and logging
  - Test error handling and fallback mechanisms
  - Create performance comparison tests between old and new implementations
  - _Requirements: 1.4, 2.4, 4.1, 5.5_

- [ ] 9. Add configuration and environment management
  - Update environment variable handling for new SDK
  - Add configuration options for model selection and grounding features
  - Implement feature flags for gradual rollout
  - Create configuration validation and error checking
  - _Requirements: 4.2, 4.4_

- [ ] 10. Update logging and monitoring
  - Enhance logging to include search queries and source information
  - Add performance metrics tracking for search grounding operations
  - Implement debugging capabilities with grounding metadata
  - Create monitoring dashboards for new SDK usage
  - _Requirements: 5.1, 5.2, 5.3, 5.5_

- [ ] 11. Create migration documentation
  - Document SDK upgrade process and breaking changes
  - Create troubleshooting guide for common migration issues
  - Document new features and capabilities
  - Provide rollback procedures if needed
  - _Requirements: 4.3_

- [ ] 12. Perform integration testing and validation
  - Test complete vehicle data resolution workflows with new SDK
  - Validate search grounding functionality across all vehicle data types
  - Perform load testing to ensure performance meets requirements
  - Test real-world scenarios with actual vehicle data queries
  - Verify elimination of "Unknown field for FunctionDeclaration" errors
  - _Requirements: 1.4, 1.5, 3.3, 3.4_