# Requirements Document

## Introduction

This feature implements a simplified staged vehicle specification resolution pipeline that replaces the current single-call and multi-call approaches with a focused 2-3 stage process. The system breaks down vehicle specification resolution into targeted searches: critical specifications (curb weight and catalytic converters) and material specifications (engine block and wheel materials). This approach prioritizes accuracy through consensus validation while maintaining simplicity and performance.

## Glossary

- **Staged Resolution Pipeline**: A multi-stage vehicle specification resolution system where each stage focuses on specific vehicle specifications
- **Critical Specifications Stage**: Stage that resolves curb weight and catalytic converter count with consensus validation
- **Material Specifications Stage**: Stage that determines engine block and wheel rim materials
- **Consensus Validation**: Statistical analysis of multiple data candidates to determine accuracy and confidence
- **Statistical Confidence**: Confidence scores calculated from actual data agreement rather than AI self-assessment
- **Vehicle Specification Bundle**: Complete set of resolved vehicle specifications with confidence scores

## Requirements

### Requirement 1

**User Story:** As a system administrator, I want a reliable vehicle specification resolution system that provides accurate data through consensus validation, so that the Ruby GEM Estimator produces trustworthy scrap value calculations.

#### Acceptance Criteria

1. THE Staged Resolution Pipeline SHALL implement 2-3 focused API calls per new vehicle search
2. THE Staged Resolution Pipeline SHALL resolve critical specifications (curb weight and catalytic converter count) with consensus validation in the first stage
3. THE Staged Resolution Pipeline SHALL determine material specifications (engine block and wheel materials) with cross-validation in the second stage
4. THE Staged Resolution Pipeline SHALL calculate statistical confidence scores based on data source agreement rather than AI self-assessment
5. THE Staged Resolution Pipeline SHALL store all specifications with confidence scores in the vehicle database

### Requirement 2

**User Story:** As a user searching for vehicle specifications, I want accurate curb weight and catalytic converter data with proven reliability, so that I can trust the scrap value estimates for business decisions.

#### Acceptance Criteria

1. WHEN multiple data sources provide curb weight candidates within 50 pounds, THE Staged Resolution Pipeline SHALL assign high confidence (0.90-0.95) and use the median value
2. WHEN catalytic converter count sources agree completely, THE Staged Resolution Pipeline SHALL assign high confidence (0.85-0.90) to the consensus value
3. THE Staged Resolution Pipeline SHALL flag suspicious results for review when data sources disagree significantly
4. THE Staged Resolution Pipeline SHALL provide detailed source attribution for all specifications with confidence scores
5. THE Staged Resolution Pipeline SHALL display confidence scores in the user interface alongside each specification

### Requirement 3

**User Story:** As a developer maintaining the vehicle resolution system, I want clear separation of concerns and predictable performance, so that the system is maintainable and debuggable.

#### Acceptance Criteria

1. THE Staged Resolution Pipeline SHALL complete typical resolutions in 2-3 API calls with predictable response times
2. THE Staged Resolution Pipeline SHALL provide graceful degradation when individual stages fail without blocking the entire resolution process
3. THE Staged Resolution Pipeline SHALL enable independent testing and debugging of each resolution stage
4. THE Staged Resolution Pipeline SHALL maintain compatibility with existing database schema and UI components
5. THE Staged Resolution Pipeline SHALL make fresh API calls for each new vehicle search without rate limiting concerns

### Requirement 4

**User Story:** As a system operator monitoring resolution quality, I want detailed confidence metrics and validation warnings, so that I can identify and address data quality issues proactively.

#### Acceptance Criteria

1. THE Staged Resolution Pipeline SHALL provide weighted overall confidence scores emphasizing critical specifications (curb weight 40%, catalytic converters 30%, engine material 15%, rim material 15%)
2. THE Staged Resolution Pipeline SHALL generate validation warnings for suspicious combinations (lightweight vehicles with iron engines, luxury brands with steel wheels)
3. THE Staged Resolution Pipeline SHALL maintain detailed provenance tracking for all specification sources and confidence calculations
4. THE Staged Resolution Pipeline SHALL store confidence scores in the database alongside each vehicle specification
5. THE Staged Resolution Pipeline SHALL enable manual review workflows for low-confidence resolutions below configurable thresholds