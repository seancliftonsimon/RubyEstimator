# Requirements Document

## Introduction

The Ruby GEM Estimator is a vehicle valuation system that uses Google AI with Grounded Search to estimate vehicle component values for scrap/salvage operations. The system provides structured results with consensus-based estimates, full provenance tracking, and administrative controls for pricing assumptions.

## Glossary

- **Grounded Search**: Google AI search that returns results with citations and source links
- **Consensus Selection**: Algorithm that identifies the most reliable estimate from multiple candidate values
- **ELV**: End of Life Vehicle - the total weight used for steel pricing calculations
- **Provenance**: Complete tracking of how each value was obtained, including sources and methods
- **Resolver Layer**: Component that orchestrates search queries and processes structured responses
- **Nut Fee**: Administrative fee applied to either ELV or curb weight based on admin settings
- **Confidence Score**: Metric reflecting agreement level and data spread for estimates

## Requirements

### Requirement 1

**User Story:** As a vehicle appraiser, I want to get accurate component valuations with source citations, so that I can make informed purchasing decisions with confidence in the data quality.

#### Acceptance Criteria

1. WHEN a vehicle search is initiated, THE Ruby_GEM_Estimator SHALL retrieve at least 3 candidate values per key field using Google AI Grounded Search
2. THE Ruby_GEM_Estimator SHALL display source citations next to each resolved field value
3. WHEN consensus cannot be reached, THE Ruby_GEM_Estimator SHALL flag the field for manual review with clear warning indicators
4. THE Ruby_GEM_Estimator SHALL compute confidence scores based on candidate agreement and data spread
5. THE Ruby_GEM_Estimator SHALL display confidence indicators using green/amber/red status with plain-English explanations

### Requirement 2

**User Story:** As a vehicle appraiser, I want consensus-based estimates from multiple sources, so that I get the most reliable valuation possible rather than relying on a single data point.

#### Acceptance Criteria

1. THE Ruby_GEM_Estimator SHALL collect multiple grounded candidates per field from different sources
2. THE Ruby_GEM_Estimator SHALL identify the densest cluster of agreeing values for consensus selection
3. THE Ruby_GEM_Estimator SHALL output the median value from the consensus cluster as the final estimate
4. WHEN candidate values deviate heavily from the consensus, THE Ruby_GEM_Estimator SHALL flag them as outliers
5. WHEN agreement is low or spread is wide, THE Ruby_GEM_Estimator SHALL display warning banners indicating manual review is needed

### Requirement 3

**User Story:** As a business administrator, I want to edit pricing assumptions and thresholds directly in the application, so that I can adjust business rules without requiring code changes.

#### Acceptance Criteria

1. THE Ruby_GEM_Estimator SHALL provide a password-protected admin interface for editing business assumptions
2. THE Ruby_GEM_Estimator SHALL allow modification of price per pound, flat fees, ELV factors, and engine weight percentages
3. WHEN admin settings are changed, THE Ruby_GEM_Estimator SHALL apply the new values to calculations immediately
4. THE Ruby_GEM_Estimator SHALL persist admin settings in the app_settings database table
5. THE Ruby_GEM_Estimator SHALL allow toggling whether Nut fee applies to ELV weight or curb weight

### Requirement 4

**User Story:** As a vehicle appraiser, I want clear revenue and cost breakdowns with proper accounting, so that I can understand the complete financial picture of each vehicle.

#### Acceptance Criteria

1. THE Ruby_GEM_Estimator SHALL calculate revenues from ELV steel, engine materials, aluminum rims, catalytic converters, and tires
2. THE Ruby_GEM_Estimator SHALL calculate costs including tow fees, lead costs, nut fees, and purchase prices
3. THE Ruby_GEM_Estimator SHALL enforce positive values for revenues and negative values for costs
4. THE Ruby_GEM_Estimator SHALL display Gross revenue, total Costs, and Net profit with clear mathematical relationships
5. THE Ruby_GEM_Estimator SHALL treat tires as revenue items in all calculations

### Requirement 5

**User Story:** As a vehicle appraiser, I want complete provenance tracking for every estimate, so that I can verify the source and method used for each valuation component.

#### Acceptance Criteria

1. THE Ruby_GEM_Estimator SHALL display the resolution method used for each field value
2. THE Ruby_GEM_Estimator SHALL provide a provenance panel showing confidence scores and source lists
3. THE Ruby_GEM_Estimator SHALL link each estimate back to its original grounded search sources
4. THE Ruby_GEM_Estimator SHALL store resolution history including final values, confidence scores, and citations
5. THE Ruby_GEM_Estimator SHALL never fabricate values when source data is unavailable

### Requirement 6

**User Story:** As a system user, I want a clean and intuitive interface that clearly presents results and warnings, so that I can quickly assess vehicle valuations and identify areas needing attention.

#### Acceptance Criteria

1. THE Ruby_GEM_Estimator SHALL display vehicle inputs on the left side of the interface
2. THE Ruby_GEM_Estimator SHALL show results in two tables on the right side covering Sale Value and Costs
3. WHEN confidence is low or ranges are wide, THE Ruby_GEM_Estimator SHALL display prominent warning indicators
4. THE Ruby_GEM_Estimator SHALL provide a dedicated provenance panel for detailed source information
5. THE Ruby_GEM_Estimator SHALL use minimal dependencies and maintain fast response times