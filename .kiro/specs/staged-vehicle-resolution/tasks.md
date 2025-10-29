# Implementation Plan

- [x] 1. Create core staged resolution infrastructure






- [x] 1.1 Implement StagedVehicleResolver class with two-stage pipeline


  - Create main resolver class that orchestrates Stage 1 and Stage 2
  - Add basic error handling and graceful degradation
  - Use existing ConsensusResolver for validation logic
  - _Requirements: 1.1, 1.2, 3.1, 3.2_

- [x] 1.2 Create VehicleSpecificationBundle data model


  - Extend existing VehicleSpecificationBundle with confidence scores
  - Add source attribution and validation warnings
  - Include overall confidence calculation
  - _Requirements: 1.5, 2.4, 4.1_



- [x] 2. Implement Stage 1: Critical Specifications Resolution




- [x] 2.1 Create focused API calls for critical specifications


  - Implement curb weight resolution using existing grounded search
  - Implement catalytic converter count resolution
  - Use existing consensus validation with 50-pound weight tolerance
  - _Requirements: 1.2, 2.1, 2.2_

- [x] 2.2 Add confidence scoring for critical specifications


  - Assign high confidence (0.90-0.95) for weight agreement within 50 pounds
  - Assign high confidence (0.85-0.90) for catalytic converter agreement
  - Flag suspicious results for manual review


  - _Requirements: 2.1, 2.2, 2.3_

- [x] 3. Implement Stage 2: Material Specifications Resolution




- [x] 3.1 Create focused API calls for material specifications


  - Implement engine block material resolution using existing methods
  - Implement wheel material resolution using existing methods
  - Add basic cross-validation against vehicle patterns
  - _Requirements: 1.3, 4.2_

- [x] 3.2 Add material specification validation


  - Check for suspicious combinations (light

weight + iron engine)
  - Validate luxury brands with steel wheels
  - Use existing validation logic from current system
  - _Requirements: 1.3, 4.2_

- [ ] 4. Implement confidence calculation and storage






- [x] 4.1 Create weighted overall confidence scoring


  - Calculate weighted confidence (curb weight 40%, catalytic 30%, engine 15%, rim 15%)
  - Use existing confidence calculation methods
  - Add manual review flagging for low confidence
  - _Requirements: 4.1, 4.5_

- [x] 4.2 Extend database schema for confidence tracking



  - Add confidence_scores JSON column to existing tables

  - Add source_attribution JSON column

  - Add validation_warnings JSON column
  - Maintain compatibility with existing schema
  - _Requirements: 1.5, 2.4, 3.4_

- [x] 5. Integrate with existing system






- [x] 5.1 Update vehicle_data.py to use staged resolution


  - Replace single-call resolver with StagedVehicleResolver
  - Maintain backward compatibility with existing functions
  - Keep existing error handling and fallback logic
  - _Requirements: 3.4, 3.5_

- [x] 5.2 Update UI to display confidence scores


  - Show confidence indicators alongside specifications
  - Display validation warnings when present
  - Add source attribution in expandable details
  - _Requirements: 2.5_

- [x] 5.3 Add progress feedback for two-stage pipeline


  - Update progress callbacks to show "Stage 1/2" and "Stage 2/2"
  - Display confidence scores as they become available
  - Show total API calls used (target: 2-3 calls)
  - _Requirements: 3.1_

- [ ]* 6. Add basic testing
- [ ]* 6.1 Write unit tests for staged resolution
  - Test two-stage pipeline with successful resolution
  - Test graceful degradation when stages fail
  - Test confidence calculation and validation
  - _Requirements: 3.2, 3.3_

- [ ]* 6.2 Write integration tests for existing system compatibility
  - Test backward compatibility with existing vehicle_data functions
  - Test UI integration with confidence display
  - Test database schema compatibility
  - _Requirements: 3.4_