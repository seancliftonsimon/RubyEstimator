# Requirements Document

## Introduction

This feature simplifies the vehicle specification resolution process by replacing the current multi-step grounded search and consensus resolution system with a single, comprehensive Gemini API call. The goal is to reduce complexity, improve performance, and maintain accuracy while eliminating the need for multiple API calls, candidate collection, and consensus algorithms.

## Glossary

- **Vehicle Resolver System**: The application component that determines vehicle specifications using AI-powered search
- **Single Call Resolution**: A unified API approach that retrieves all vehicle specifications in one request
- **Specification Bundle**: All required vehicle data (curb weight, engine material, rim material, catalytic converter count) returned together
- **Trusted Source Validation**: AI-powered verification that prioritizes authoritative automotive sources
- **Fallback Resolution**: Backup resolution method used when the primary single-call approach fails

## Requirements

### Requirement 1

**User Story:** As a system administrator, I want to reduce the complexity of vehicle specification resolution, so that the system is more maintainable and performs better.

#### Acceptance Criteria

1. THE Vehicle Resolver System SHALL replace the multi-step grounded search process with a single comprehensive API call
2. THE Vehicle Resolver System SHALL eliminate the need for candidate collection and consensus resolution algorithms
3. THE Vehicle Resolver System SHALL reduce the total number of API calls from 4-6 calls per vehicle to 1 call per vehicle
4. THE Vehicle Resolver System SHALL maintain the existing database storage and caching mechanisms
5. THE Vehicle Resolver System SHALL preserve all existing error handling and fallback capabilities

### Requirement 2

**User Story:** As a user searching for vehicle specifications, I want faster and more reliable results, so that I can get accurate vehicle data quickly.

#### Acceptance Criteria

1. THE Vehicle Resolver System SHALL return all vehicle specifications (weight, engine material, rim material, catalytic converters) in a single response
2. THE Vehicle Resolver System SHALL prioritize authoritative sources (manufacturer websites, KBB, Edmunds) in the AI prompt
3. THE Vehicle Resolver System SHALL provide confidence indicators based on source reliability and data consistency
4. THE Vehicle Resolver System SHALL return structured data that can be directly stored in the database
5. THE Vehicle Resolver System SHALL complete resolution in significantly less time than the current multi-call approach

### Requirement 3

**User Story:** As a developer maintaining the system, I want simplified code architecture, so that the system is easier to understand and modify.

#### Acceptance Criteria

1. THE Vehicle Resolver System SHALL eliminate the GroundedSearchClient, ConsensusResolver, and complex candidate management code
2. THE Vehicle Resolver System SHALL use a single, well-structured prompt that requests all specifications at once
3. THE Vehicle Resolver System SHALL parse the AI response into the existing data structures
4. THE Vehicle Resolver System SHALL maintain compatibility with existing UI components and database schema
5. THE Vehicle Resolver System SHALL preserve the existing ProvenanceTracker for resolution history and caching