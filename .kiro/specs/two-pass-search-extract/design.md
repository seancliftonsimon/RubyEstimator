# Two-Pass Search-Extract System Design

## Overview

This design document outlines the complete replacement of the existing search/analyze system with a deterministic two-pass "Search → Extract" pipeline. The system eliminates all prior search stack components (staged/fallback resolvers, consensus/mean/std logic, synthetic sources) and replaces them with a simple, grounded approach that ensures all extracted values are traceable to real web sources.

The two-pass architecture separates concerns: Pass A focuses solely on collecting raw text excerpts from web searches, while Pass B performs structured data extraction strictly from those excerpts. This design ensures complete traceability and eliminates synthetic data generation.

## Architecture

### High-Level Flow

```
User Input (Year, Make, Model)
    ↓
Pass A: Search Phase
    ├── Field-specific web searches (4 parallel searches)
    ├── Raw excerpt collection with URLs
    ├── Trust-weighted source prioritization
    └── Deduplication by URL
    ↓
Pass B: Extract Phase
    ├── Structured extraction from Pass A excerpts only
    ├── Type enforcement and validation
    ├── Evidence tracking with URL/quote pairs
    └── Deterministic collation with confidence scoring
    ↓
Database Persistence
    ├── Final values in vehicles table
    └── Evidence rows in attribute_evidence table
    ↓
UI Display
    └── Values + confidence + citations
```

### System Boundaries

The Search Extract System operates as a complete replacement with clear boundaries:

- **Input**: Vehicle identification (year, make, model)
- **Output**: Four typed specifications with evidence and confidence
- **External Dependencies**: Google AI API for web search, database for persistence
- **Internal Components**: Pass A searcher, Pass B extractor, evidence tracker, UI renderer

## Components and Interfaces

### 1. Pass A: Search Component

**Purpose**: Collect raw text excerpts from grounded web searches without any synthesis or analysis.

```python
class PassASearcher:
    def __init__(self, api_client: GoogleAIClient):
        self.api_client = api_client
        self.trust_weights = {
            "government": 1.0,
            "oem": 1.0, 
            "major_spec": 0.85,
            "parts_retailer": 0.7,
            "forum": 0.4
        }
    
    def collect_excerpts(self, year: int, make: str, model: str) -> Dict[str, List[RawExcerpt]]:
        """Run parallel searches for all four fields, return raw excerpts only."""
        
    def search_single_field(self, year: int, make: str, model: str, field: str) -> List[RawExcerpt]:
        """Execute one grounded web search for a specific field."""
        
    def prioritize_sources(self, excerpts: List[RawExcerpt]) -> List[RawExcerpt]:
        """Apply trust heuristic ordering, keep top 5 unique URLs per field."""
```

**Data Structures**:
```python
@dataclass
class RawExcerpt:
    url: str
    text_content: str
    field: str  # curb_weight, aluminum_engine, aluminum_rims, catalytic_converters
    trust_score: float
    search_timestamp: datetime
```

**Key Design Decisions**:
- No filtering by allowlist during collection (requirement 2.4)
- Deduplication by URL while preserving content (requirement 2.5)
- Trust heuristic applied for reading priority, not filtering
- Top 5 URLs per field to balance coverage and processing time

### 2. Pass B: Extract Component

**Purpose**: Extract structured data strictly from Pass A excerpts with explicit evidence tracking.

```python
class PassBExtractor:
    def __init__(self, api_client: GoogleAIClient):
        self.api_client = api_client
        self.temperature = 0  # Deterministic extraction (requirement 3.5)
    
    def extract_all_fields(self, excerpts_by_field: Dict[str, List[RawExcerpt]]) -> Dict[str, FieldResult]:
        """Extract structured data from excerpts for all fields."""
        
    def extract_single_field(self, field: str, excerpts: List[RawExcerpt]) -> FieldResult:
        """Extract one field with evidence tracking."""
        
    def enforce_type_constraints(self, field: str, raw_value: Any) -> Any:
        """Apply strict type enforcement per requirement 4."""
```

**Data Structures**:
```python
@dataclass
class FieldResult:
    field_name: str
    value: Union[float, int, bool, None]  # Typed per requirement 4
    unit: Optional[str]
    evidence: List[EvidenceItem]
    confidence: float
    needs_review: bool
    extraction_method: str

@dataclass
class EvidenceItem:
    url: str
    quote: str
    parsed_value: Union[float, int, bool]
    trust_weight: float
```

**Key Design Decisions**:
- Temperature 0 for deterministic results (requirement 3.5)
- Strict type enforcement prevents 0/False from missing data (requirement 4.5)
- Every extracted value must include URL and quote evidence (requirement 3.4)
- Unknown returned when explicit data not found (requirement 3.2)

### 3. Deterministic Collation Engine

**Purpose**: Apply mathematical rules for value selection without AI synthesis.

```python
class DeterministicCollator:
    def __init__(self):
        self.confidence_threshold = 0.3  # Minimum confidence
        self.max_confidence = 0.95      # Maximum confidence cap
    
    def collate_numeric_weight(self, evidence: List[EvidenceItem]) -> FieldResult:
        """Use median with 10% trim for curb weight (requirement 5.1)."""
        
    def collate_integer_count(self, evidence: List[EvidenceItem]) -> FieldResult:
        """Use mode for catalytic converters, unknown on ties (requirement 5.2)."""
        
    def collate_boolean_material(self, evidence: List[EvidenceItem]) -> FieldResult:
        """Use majority for aluminum specs, unknown on ties (requirement 5.3)."""
        
    def calculate_confidence(self, evidence: List[EvidenceItem], spread_factor: float, majority_factor: float) -> float:
        """70% spread/majority + 30% average trust weight (requirement 5.5)."""
```

**Mathematical Rules**:
- **Curb Weight**: Median with 10% trim if 3+ values, parse to pounds only
- **Catalytic Converters**: Mode selection, return unknown with 0.4 confidence on ties
- **Aluminum Specs**: Majority of explicit mentions, unknown with 0.4 confidence on ties
- **Confidence**: 70% spread/majority factor + 30% average trust weight, clamped 0.3-0.95

### 4. Evidence Persistence Layer

**Purpose**: Store grounded evidence that maps every row to real URLs.

```python
class EvidenceTracker:
    def store_vehicle_resolution(self, year: int, make: str, model: str, results: Dict[str, FieldResult]) -> bool:
        """Store final values and evidence with integrity constraints."""
        
    def store_evidence_items(self, vehicle_id: int, field_results: Dict[str, FieldResult]) -> bool:
        """Store attribute_evidence rows with URL validation."""
```

**Database Schema**:
```sql
-- Enhanced vehicles table with confidence tracking
ALTER TABLE vehicles ADD COLUMN confidence_curb_weight DECIMAL(3,2);
ALTER TABLE vehicles ADD COLUMN confidence_aluminum_engine DECIMAL(3,2);
ALTER TABLE vehicles ADD COLUMN confidence_aluminum_rims DECIMAL(3,2);
ALTER TABLE vehicles ADD COLUMN confidence_catalytic_converters DECIMAL(3,2);
ALTER TABLE vehicles ADD COLUMN needs_review BOOLEAN DEFAULT FALSE;

-- New evidence table for traceability
CREATE TABLE attribute_evidence (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER REFERENCES vehicles(id),
    field VARCHAR(50) NOT NULL,
    url VARCHAR(500) NOT NULL,
    quote TEXT NOT NULL,
    parsed_value VARCHAR(100),
    unit VARCHAR(20),
    trust_weight DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Key Design Decisions**:
- Every evidence row maps to real Pass-A URL (requirement 6.3)
- No synthetic entries allowed in evidence table
- Confidence stored per field for granular tracking
- needs_review flag for manual review triggers (requirements 6.4, 6.5)

### 5. Orchestrator Component

**Purpose**: Provide single entry point that coordinates both passes and handles errors.

```python
class SearchExtractOrchestrator:
    def __init__(self, pass_a: PassASearcher, pass_b: PassBExtractor, 
                 collator: DeterministicCollator, evidence: EvidenceTracker):
        self.pass_a = pass_a
        self.pass_b = pass_b
        self.collator = collator
        self.evidence = evidence
    
    def resolve_vehicle(self, year: int, make: str, model: str) -> VehicleResolution:
        """Single entry point for complete vehicle resolution (requirement 7.3)."""
        
    def calculate_overall_confidence(self, field_confidences: Dict[str, float]) -> float:
        """Median of individual field confidences (requirement 7.4)."""
```

**Error Handling Strategy**:
- Pass A failure: Return unknown for all fields with 0.3 confidence
- Pass B failure: Return unknown for affected fields, continue with others
- Partial failures: Process available data, flag needs_review
- Network timeouts: Retry with exponential backoff, max 3 attempts

## Data Models

### Core Data Flow

```python
# Input Model
@dataclass
class VehicleQuery:
    year: int
    make: str
    model: str

# Pass A Output
@dataclass
class SearchResults:
    excerpts_by_field: Dict[str, List[RawExcerpt]]
    total_urls_found: int
    search_duration: float

# Pass B Output  
@dataclass
class ExtractionResults:
    field_results: Dict[str, FieldResult]
    extraction_duration: float

# Final Output
@dataclass
class VehicleResolution:
    curb_weight_lbs: Optional[float]
    aluminum_engine: Optional[bool]
    aluminum_rims: Optional[bool]
    catalytic_converters: Optional[int]
    confidence_scores: Dict[str, float]
    overall_confidence: float
    evidence_summary: List[EvidenceSummary]
    needs_review: bool
    processing_metrics: ProcessingMetrics
```

### Type Enforcement Rules

Based on requirement 4, strict type constraints are enforced:

- **curb_weight_lbs**: `float` in pounds only, no zero values from missing data
- **catalytic_converters**: `int` counts only, no zero values from missing data  
- **aluminum_engine**: `bool` true/false/unknown only, no zero/False from missing data
- **aluminum_rims**: `bool` true/false/unknown only, no zero/False from missing data

### Trust Weight Mapping

Source prioritization follows requirement 5.4:

```python
TRUST_WEIGHTS = {
    # Government/OEM sources (1.0)
    "nhtsa.gov": 1.0,
    "epa.gov": 1.0,
    "manufacturer_official": 1.0,
    
    # Major spec sites (0.85)
    "edmunds.com": 0.85,
    "kbb.com": 0.85,
    "cars.com": 0.85,
    
    # Parts retailers (0.7)
    "rockauto.com": 0.7,
    "autozone.com": 0.7,
    "advanceautoparts.com": 0.7,
    
    # Forums (0.4)
    "reddit.com": 0.4,
    "forums.*": 0.4,
    "facebook.com": 0.4
}
```

## Error Handling

### Graceful Degradation Strategy

The system implements multiple fallback levels:

1. **Field-Level Fallbacks**: If one field fails extraction, continue with others
2. **Confidence-Based Warnings**: Low confidence triggers needs_review flag
3. **Evidence Requirements**: Missing evidence results in unknown value, not synthetic data
4. **Timeout Handling**: Network timeouts return partial results with warnings

### Manual Review Triggers

Based on requirements 6.4 and 6.5, the system flags needs_review when:

- Numeric spread exceeds 10% of median for curb weight
- Boolean/count ties exist among high-trust sources
- Only low-trust sources available for any field
- Extraction confidence below 0.4 threshold
- Network errors prevent complete data collection

### Error Response Format

```python
@dataclass
class ErrorResponse:
    success: bool
    error_type: str  # "network", "parsing", "no_data", "timeout"
    message: str
    partial_results: Optional[VehicleResolution]
    retry_recommended: bool
```

## Testing Strategy

### Unit Testing Approach

1. **Pass A Testing**: Mock Google AI responses, verify excerpt collection and deduplication
2. **Pass B Testing**: Test extraction with known excerpt inputs, verify type enforcement
3. **Collation Testing**: Test mathematical rules with various evidence combinations
4. **Integration Testing**: End-to-end tests with real API calls (limited)

### Test Data Strategy

```python
# Mock excerpt data for consistent testing
MOCK_CURB_WEIGHT_EXCERPTS = [
    RawExcerpt(url="edmunds.com/...", text_content="curb weight: 3,245 lbs", ...),
    RawExcerpt(url="kbb.com/...", text_content="weighs 3250 pounds", ...),
    # ... more test data
]

# Expected outputs for validation
EXPECTED_COLLATION_RESULTS = {
    "median_weight": 3247.5,
    "confidence": 0.87,
    "needs_review": False
}
```

### Performance Testing

- **Search Latency**: Target <10 seconds for all four field searches
- **Extraction Speed**: Target <5 seconds for all field extractions  
- **Database Performance**: Target <1 second for evidence storage
- **Memory Usage**: Monitor excerpt storage, implement cleanup after processing

### Integration Points Testing

1. **Google AI API**: Test rate limiting, error responses, timeout handling
2. **Database**: Test transaction rollback, constraint violations, concurrent access
3. **UI Integration**: Test confidence display, citation rendering, error messaging

## Implementation Notes

### Migration from Existing System

The implementation requires complete replacement of existing components:

**Components to Remove**:
- `StagedVehicleResolver` class and all staged resolution logic
- `ConsensusResolver` mean/std calculations and synthetic source generation
- All fallback resolver mechanisms and "±5%" synthetic sources
- Existing confidence rollup calculations in UI

**Components to Preserve**:
- Database schema (enhanced with new evidence table)
- UI framework (modified for new confidence display)
- Authentication and admin configuration systems

### API Integration Patterns

```python
# Google AI integration with grounded search
def create_search_request(self, query: str) -> dict:
    return {
        "model": "gemini-2.5-flash",
        "contents": query,
        "tools": [{"google_search": {}}],
        "generation_config": {
            "temperature": 0,  # Deterministic for Pass B
            "max_output_tokens": 1000
        }
    }
```

### Performance Optimizations

1. **Parallel Processing**: Run all four Pass A searches concurrently
2. **Caching Strategy**: Cache excerpts by vehicle for 24 hours to reduce API calls
3. **Batch Processing**: Group evidence storage operations for better database performance
4. **Connection Pooling**: Reuse database connections across requests

### Monitoring and Observability

```python
@dataclass
class ProcessingMetrics:
    pass_a_duration: float
    pass_b_duration: float
    total_api_calls: int
    excerpts_collected: int
    evidence_items_stored: int
    confidence_distribution: Dict[str, float]
```

The system tracks these metrics for performance monitoring and system health assessment.