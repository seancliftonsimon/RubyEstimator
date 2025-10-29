# Requirements Document

## Introduction

This feature implements a complete replacement of the existing search/analyze system with a simple two-pass "Search → Extract" pipeline. The system eliminates all prior search stack components (staged/fallback resolvers, consensus/mean/std logic, synthetic sources) and replaces them with a deterministic two-step process: Pass A collects raw text excerpts from web searches, and Pass B extracts structured data strictly from those excerpts. The system focuses on four specific vehicle specifications with strict type enforcement and grounded evidence requirements.

## Glossary

- **Two-Pass Pipeline**: A replacement search system with distinct Search (Pass A) and Extract (Pass B) phases
- **Pass A (Search)**: Grounded web search that collects raw text excerpts and URLs without synthesis
- **Pass B (Extract)**: Structured data extraction strictly from Pass A excerpts with no additional web queries
- **Grounded Evidence**: All extracted values must reference specific URLs and text quotes from Pass A
- **Trust Weighting**: Source prioritization system favoring official/government sources over forums
- **Deterministic Collation**: Rule-based value selection using median, mode, or majority with no AI synthesis
- **Search Extract System**: The complete two-pass replacement system

## Requirements

### Requirement 1

**User Story:** As a system administrator, I want to completely replace the existing search stack with a two-pass system that eliminates synthetic sources and consensus logic, so that all vehicle specifications are grounded in real web sources.

#### Acceptance Criteria

1. THE Search Extract System SHALL delete all existing staged/fallback resolver code and consensus/mean/std logic
2. THE Search Extract System SHALL disable all synthetic "±5%" source generation and zero/False default coercion
3. THE Search Extract System SHALL implement Pass A as the single entry point for all web searches
4. THE Search Extract System SHALL implement Pass B as the single entry point for all data extraction
5. THE Search Extract System SHALL ensure no other system components may query the web or fabricate sources

### Requirement 2

**User Story:** As a developer maintaining the search system, I want Pass A to collect only raw text excerpts without any synthesis, so that all analysis happens in a separate, controlled extraction phase.

#### Acceptance Criteria

1. WHEN executing Pass A for each field, THE Search Extract System SHALL run one grounded web search per field
2. THE Search Extract System SHALL return only raw excerpts and URLs from Pass A with no synthesis or analysis
3. THE Search Extract System SHALL keep top 5 unique URLs ordered by trust heuristic for reading priority
4. THE Search Extract System SHALL not filter results by allowlist during Pass A collection
5. THE Search Extract System SHALL deduplicate results by URL while preserving excerpt content

### Requirement 3

**User Story:** As a data analyst reviewing vehicle specifications, I want Pass B to extract values strictly from provided text with explicit evidence tracking, so that every result can be traced to specific source quotes.

#### Acceptance Criteria

1. WHEN Pass A excerpts are not available, THE Search Extract System SHALL return unknown with 0.3 confidence and needs_review true
2. WHEN explicit data is not found in excerpts, THE Search Extract System SHALL return unknown rather than inferring values
3. THE Search Extract System SHALL return structured results with value, type, unit, evidence array, confidence, and needs_review flag
4. THE Search Extract System SHALL include URL and quote in evidence for every extracted value
5. THE Search Extract System SHALL use temperature 0 for all extraction calls to ensure deterministic results

### Requirement 4

**User Story:** As a vehicle specification user, I want accurate data for four specific fields with proper type enforcement, so that I receive curb weight in pounds, catalytic converter counts as integers, and aluminum specifications as booleans.

#### Acceptance Criteria

1. THE Search Extract System SHALL resolve curb_weight_lbs as numeric values in pounds only
2. THE Search Extract System SHALL resolve catalytic_converters as integer counts only
3. THE Search Extract System SHALL resolve aluminum_engine as boolean true/false/unknown only
4. THE Search Extract System SHALL resolve aluminum_rims as boolean true/false/unknown only
5. THE Search Extract System SHALL never emit 0 or False values from missing data

### Requirement 5

**User Story:** As a system operator monitoring data quality, I want deterministic collation rules and trust-weighted source prioritization, so that official sources are prioritized and value selection follows consistent mathematical rules.

#### Acceptance Criteria

1. WHEN processing numeric weight data, THE Search Extract System SHALL parse to pounds and use median with 10% trim if 3+ values exist
2. WHEN processing catalytic converter counts, THE Search Extract System SHALL use mode and return unknown with 0.4 confidence for ties
3. WHEN processing boolean aluminum specifications, THE Search Extract System SHALL use majority of explicit mentions and return unknown with 0.4 confidence for ties
4. THE Search Extract System SHALL weight government/OEM sources at 1.0, major spec sites at 0.85, parts retailers at 0.7, and forums at 0.4
5. THE Search Extract System SHALL calculate confidence using 70% spread/majority factor plus 30% average trust weight, clamped between 0.3 and 0.95

### Requirement 6

**User Story:** As a database administrator, I want minimal grounded persistence that maps every evidence row to real URLs, so that the system maintains data integrity without synthetic entries.

#### Acceptance Criteria

1. THE Search Extract System SHALL store final field values with confidence and needs_review flags in vehicles table
2. THE Search Extract System SHALL store attribute_evidence with vehicle_id, field, url, quote, parsed_value, and unit
3. THE Search Extract System SHALL ensure every evidence row maps to a real Pass-A URL with no synthetic entries
4. THE Search Extract System SHALL flag needs_review as true when numeric spread exceeds 10% of median
5. THE Search Extract System SHALL flag needs_review as true when boolean/count ties exist among high-trust sources or only low-trust sources available

### Requirement 7

**User Story:** As an end user viewing vehicle specifications, I want a clean interface showing final values with confidence and citations, so that I can assess data reliability and access source documentation.

#### Acceptance Criteria

1. THE Search Extract System SHALL display final value plus confidence score plus up to 3 citations with URLs
2. WHEN value is unknown, THE Search Extract System SHALL show "Insufficient explicit evidence" message with available citations
3. THE Search Extract System SHALL provide single orchestrator function as the only entry point for vehicle resolution
4. THE Search Extract System SHALL compute overall confidence as median of individual field confidences
5. THE Search Extract System SHALL remove all old "overall confidence" rollup calculations from previous system