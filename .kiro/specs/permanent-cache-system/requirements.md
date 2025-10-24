# Requirements Document

## Introduction

This feature modifies the Ruby GEM Estimator's caching system to use a permanent, evergrowing knowledge base instead of time-limited cache entries. The system currently invalidates cached resolutions after 24 hours, requiring repeated API calls for the same vehicles. The new system will retain all resolution data indefinitely, reducing API costs over time as the database grows and becomes more comprehensive.

## Glossary

- **Resolution System**: The component that uses Google AI with Grounded Search to resolve vehicle specifications
- **Provenance Tracker**: The component that manages resolution history and caching
- **Resolution Record**: A stored database entry containing a resolved vehicle field value with confidence score and metadata
- **Cache Invalidation**: The process of removing or ignoring cached data based on age or other criteria
- **Knowledge Base**: The collection of all resolution records stored in the database
- **API Call**: A request to Google AI API that incurs cost

## Requirements

### Requirement 1

**User Story:** As a system operator, I want all resolution data to be permanently cached, so that the system becomes more cost-effective over time

#### Acceptance Criteria

1. WHEN THE Provenance Tracker checks for cached resolutions, THE Resolution System SHALL retrieve resolution records without time-based filtering
2. THE Resolution System SHALL use cached resolution data regardless of the age of the record
3. THE Resolution System SHALL store every new resolution permanently in the database
4. THE Resolution System SHALL NOT delete or ignore resolution records based on creation timestamp

### Requirement 2

**User Story:** As a system operator, I want the monitoring dashboard to display all historical data, so that I can see the complete knowledge base growth

#### Acceptance Criteria

1. WHEN THE Monitoring Dashboard queries resolution statistics, THE Resolution System SHALL include all resolution records without time filtering
2. THE Monitoring Dashboard SHALL display total resolution count across all time periods
3. THE Monitoring Dashboard SHALL display knowledge base growth metrics
4. WHERE time-based analysis is displayed, THE Monitoring Dashboard SHALL allow user-selectable time ranges

### Requirement 3

**User Story:** As a system operator, I want to manually manage old data if needed, so that I retain control over database size

#### Acceptance Criteria

1. THE Resolution System SHALL NOT automatically delete resolution records
2. WHERE manual data cleanup is needed, THE Resolution System SHALL provide administrative tools for selective deletion
3. THE Resolution System SHALL log all manual data deletion operations
4. THE Resolution System SHALL preserve data integrity when manual deletions occur

### Requirement 4

**User Story:** As a developer, I want the caching logic to be simplified, so that the codebase is easier to maintain

#### Acceptance Criteria

1. THE Provenance Tracker SHALL remove time-based cache invalidation logic
2. THE Provenance Tracker SHALL remove max_age_hours parameters from cache lookup methods
3. THE Resolution System SHALL remove datetime interval queries from cache lookups
4. THE Resolution System SHALL maintain backward compatibility with existing resolution records
