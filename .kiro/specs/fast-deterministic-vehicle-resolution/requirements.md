# Requirements Document

## Introduction

A fast, deterministic vehicle specification resolution system that replaces the current slow, unreliable two-pass search architecture. The system must resolve vehicle specifications (curb weight, wheel material, engine block material, catalytic converter count) with sub-15 second response times and zero manual review on the happy path.

## Glossary

- **Vehicle_Resolution_System**: The core system that resolves vehicle specifications from normalized inputs
- **Normalization_Engine**: Component that canonicalizes vehicle make/model/year inputs and field names
- **Source_Router**: Component that deterministically selects primary and fallback data sources
- **Evidence_Store**: Database component that caches resolved specifications with source attribution
- **Micro_LLM_Resolver**: Small language model component for final value selection from structured candidates
- **SLA**: Service Level Agreement defining performance targets (P50 < 8s, P95 < 15s)

## Requirements

### Requirement 1

**User Story:** As a vehicle data analyst, I want to resolve vehicle specifications quickly and reliably, so that I can get accurate data without waiting over 15 seconds or dealing with failed lookups.

#### Acceptance Criteria

1. WHEN a vehicle specification request is submitted, THE Vehicle_Resolution_System SHALL return results within 15 seconds maximum
2. THE Vehicle_Resolution_System SHALL achieve P50 response times under 8 seconds
3. THE Vehicle_Resolution_System SHALL achieve P95 response times under 15 seconds
4. IF primary sources are available, THEN THE Vehicle_Resolution_System SHALL return results within 5 seconds
5. THE Vehicle_Resolution_System SHALL provide deterministic results for identical inputs

### Requirement 2

**User Story:** As a system integrator, I want normalized and validated inputs, so that typos and variations don't cause lookup failures.

#### Acceptance Criteria

1. THE Normalization_Engine SHALL canonicalize vehicle make and model names using fuzzy matching
2. THE Normalization_Engine SHALL normalize field names to a closed enum (curb_weight, aluminum_engine, aluminum_rims, catalytic_converters)
3. WHEN invalid field names are provided, THE Normalization_Engine SHALL reject the request within 5 milliseconds
4. THE Normalization_Engine SHALL map common misspellings to correct model names (e.g., "Sorrento" to "Sorento")
5. THE Normalization_Engine SHALL validate year ranges and reject invalid years immediately

### Requirement 3

**User Story:** As a performance-conscious developer, I want deterministic source routing, so that the system doesn't waste time on broad web searches.

#### Acceptance Criteria

1. THE Source_Router SHALL select primary sources based on vehicle make without LLM involvement
2. THE Source_Router SHALL complete source selection within 150 milliseconds
3. WHEN primary sources are unavailable, THE Source_Router SHALL select up to 2 fallback sources
4. THE Source_Router SHALL prioritize official manufacturer specification pages
5. THE Source_Router SHALL maintain a mapping of make-specific primary sources

### Requirement 4

**User Story:** As a data reliability engineer, I want parallel HTTP fetching with timeouts, so that slow sources don't block the entire resolution process.

#### Acceptance Criteria

1. THE Vehicle_Resolution_System SHALL execute at most 3 parallel HTTP requests
2. THE Vehicle_Resolution_System SHALL enforce 2.5 second timeout per HTTP request
3. WHEN primary sources succeed, THE Vehicle_Resolution_System SHALL skip fallback requests
4. THE Vehicle_Resolution_System SHALL parse responses using CSS/XPath selectors without LLM involvement
5. IF all required fields are resolved from primary sources, THEN THE Vehicle_Resolution_System SHALL return immediately

### Requirement 5

**User Story:** As a system administrator, I want intelligent caching and evidence storage, so that repeated queries are fast and results are auditable.

#### Acceptance Criteria

1. THE Evidence_Store SHALL cache normalized vehicle specifications for 30 days
2. THE Evidence_Store SHALL cache negative results (404 responses) for 6 hours
3. THE Evidence_Store SHALL store complete evidence payloads including source quotes and URLs
4. THE Evidence_Store SHALL use normalized (year, make, model, drivetrain, engine) as cache keys
5. THE Evidence_Store SHALL provide source attribution for all resolved values

### Requirement 6

**User Story:** As a quality assurance engineer, I want minimal LLM usage with structured outputs, so that the system is fast and deterministic.

#### Acceptance Criteria

1. THE Micro_LLM_Resolver SHALL make only one LLM call per resolution request
2. THE Micro_LLM_Resolver SHALL complete processing within 400 milliseconds
3. THE Micro_LLM_Resolver SHALL use temperature 0 for deterministic outputs
4. THE Micro_LLM_Resolver SHALL only resolve conflicts between structured candidates
5. WHEN fields have clear primary source values, THE Micro_LLM_Resolver SHALL echo them without modification

### Requirement 7

**User Story:** As a system operator, I want proper error handling and validation, so that invalid data is caught early and the system fails gracefully.

#### Acceptance Criteria

1. THE Vehicle_Resolution_System SHALL validate units and strip formatting from numeric values
2. THE Vehicle_Resolution_System SHALL bounds-check curb weight values (2,800-6,500 lbs for SUVs)
3. WHEN timeouts occur, THE Vehicle_Resolution_System SHALL return partial results with confidence indicators
4. THE Vehicle_Resolution_System SHALL log all failures with structured error codes
5. THE Vehicle_Resolution_System SHALL provide fallback values when primary sources fail completely