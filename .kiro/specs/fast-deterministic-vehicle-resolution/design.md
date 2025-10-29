# Fast Deterministic Vehicle Resolution System Design

## Overview

The Fast Deterministic Vehicle Resolution System is a high-performance replacement for the current two-pass search architecture. It provides sub-15 second vehicle specification resolution with deterministic routing, intelligent caching, and minimal LLM usage. The system prioritizes speed and reliability through parallel processing, structured data extraction, and evidence-based caching.

## Architecture

### System Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Gateway   │───▶│ Normalization    │───▶│  Source Router  │
│                 │    │    Engine        │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Evidence Store  │◀───│ Micro LLM        │◀───│ Parallel HTTP   │
│   (Cache)       │    │   Resolver       │    │   Fetcher       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Design Rationale

**Deterministic Architecture**: Unlike the current two-pass system that relies on broad web searches, this design uses predetermined source routing based on vehicle make. This eliminates the unpredictability of web search results and ensures consistent performance.

**Minimal LLM Usage**: The system restricts LLM calls to a single conflict resolution step, using structured data extraction for the majority of processing. This dramatically reduces latency and improves determinism.

**Parallel Processing**: HTTP requests are executed in parallel with strict timeouts, preventing slow sources from blocking the entire resolution process.

## Components and Interfaces

### 1. Normalization Engine

**Purpose**: Simple validation and normalization with conservative rejection of ambiguous inputs.

**Interface**:
```python
class NormalizationEngine:
    def normalize_vehicle(self, make: str, model: str, year: int) -> Union[NormalizedVehicle, ValidationError]
    def normalize_field_names(self, fields: List[str]) -> Union[List[FieldEnum], ValidationError]
    def validate_year_range(self, year: int) -> bool
```

**Key Features**:
- Simple case-insensitive exact matching for make/model names
- Closed enum validation for field names (curb_weight, aluminum_engine, aluminum_rims, catalytic_converters)
- Immediate rejection of unrecognized makes/models with "manual search needed" message
- Sub-5ms rejection of invalid inputs

**Design Decision**: Conservative approach that rejects ambiguous inputs rather than attempting fuzzy matching. This ensures high precision and fast response times, with clear user feedback when manual intervention is needed.

### 2. Source Router

**Purpose**: Deterministically select primary and fallback data sources based on vehicle make.

**Interface**:
```python
class SourceRouter:
    def get_primary_sources(self, make: str) -> List[DataSource]
    def get_fallback_sources(self, make: str) -> List[DataSource]
    def complete_routing(self, normalized_vehicle: NormalizedVehicle) -> RoutingPlan
```

**Routing Strategy**:
- Make-specific primary sources (e.g., Toyota → toyota.com specs)
- Maximum 2 fallback sources per request
- Official manufacturer pages prioritized over third-party sources
- 150ms maximum routing time

**Design Decision**: Static routing tables are maintained instead of dynamic source discovery to ensure deterministic behavior and meet timing requirements.

### 3. Parallel HTTP Fetcher

**Purpose**: Execute concurrent HTTP requests with strict timeout controls.

**Interface**:
```python
class ParallelHTTPFetcher:
    def fetch_sources(self, routing_plan: RoutingPlan) -> List[SourceResponse]
    def parse_structured_data(self, response: SourceResponse) -> StructuredData
```

**Key Features**:
- Maximum 3 concurrent requests
- 2.5 second timeout per request
- CSS/XPath selectors for data extraction (no LLM parsing)
- Early termination when primary sources provide all required fields

**Design Decision**: Fixed concurrency limit prevents overwhelming target servers while maintaining performance. CSS/XPath selectors are pre-configured for known sources to avoid LLM parsing overhead.

### 4. Evidence Store

**Purpose**: Intelligent caching with source attribution and evidence preservation.

**Interface**:
```python
class EvidenceStore:
    def get_cached_result(self, cache_key: CacheKey) -> Optional[CachedResult]
    def store_result(self, cache_key: CacheKey, result: ResolutionResult) -> None
    def store_negative_result(self, cache_key: CacheKey, error: ResolutionError) -> None
```

**Caching Strategy**:
- Cache key: (year, make, model, drivetrain, engine)
- Positive results: 30-day TTL
- Negative results (404s): 6-hour TTL
- Complete evidence payloads with source quotes and URLs

**Design Decision**: Separate TTLs for positive and negative results balance performance with data freshness. Negative result caching prevents repeated failed lookups.

### 5. Micro LLM Resolver

**Purpose**: Final value selection and conflict resolution using minimal LLM processing.

**Interface**:
```python
class MicroLLMResolver:
    def resolve_conflicts(self, candidates: StructuredCandidates) -> ResolvedValues
    def validate_and_format(self, raw_values: Dict) -> FormattedResult
```

**Processing Rules**:
- Single LLM call per resolution request
- Temperature 0 for deterministic outputs
- 400ms maximum processing time
- Only processes conflicting values between structured candidates
- Direct echo for clear primary source values

**Design Decision**: Structured input format and temperature 0 ensure deterministic behavior. Processing is limited to conflict resolution only, avoiding unnecessary LLM overhead.

## Data Models

### Core Data Structures

```python
@dataclass
class NormalizedVehicle:
    year: int
    make: str
    model: str
    drivetrain: Optional[str] = None
    engine: Optional[str] = None

@dataclass
class VehicleSpecification:
    curb_weight: Optional[float]  # pounds
    aluminum_engine: Optional[bool]
    aluminum_rims: Optional[bool]
    catalytic_converters: Optional[int]

@dataclass
class ResolutionResult:
    specifications: VehicleSpecification
    confidence_scores: Dict[str, float]
    source_attribution: Dict[str, str]
    processing_time_ms: int
    evidence_payload: Dict[str, Any]

@dataclass
class CacheKey:
    year: int
    make: str
    model: str
    drivetrain: Optional[str]
    engine: Optional[str]
    
    def __hash__(self) -> int:
        return hash((self.year, self.make, self.model, self.drivetrain, self.engine))
```

### Validation Rules

**Curb Weight Validation**:
- SUVs: 2,800-6,500 lbs
- Sedans: 2,500-4,500 lbs
- Trucks: 4,000-8,000 lbs

**Unit Normalization**:
- Strip formatting (commas, units)
- Convert kg to lbs (multiply by 2.20462)
- Round to nearest pound

## Error Handling

### Error Categories

1. **Input Validation Errors** (< 5ms response)
   - Invalid year ranges
   - Unrecognized field names
   - Malformed vehicle identifiers

2. **Source Timeout Errors** (2.5s timeout)
   - HTTP request timeouts
   - DNS resolution failures
   - Connection refused

3. **Data Quality Errors**
   - Out-of-bounds values
   - Conflicting source data
   - Missing required fields

### Fallback Strategy

```python
class FallbackStrategy:
    def handle_primary_failure(self, error: SourceError) -> FallbackAction
    def provide_partial_results(self, available_data: Dict) -> PartialResult
    def generate_confidence_indicators(self, sources: List[Source]) -> ConfidenceMap
```

**Fallback Hierarchy**:
1. Primary manufacturer sources
2. Trusted third-party databases (Edmunds, KBB)
3. Cached historical data (if available)
4. Conservative estimates with low confidence scores

**Design Decision**: Partial results with confidence indicators are preferred over complete failures, allowing downstream systems to make informed decisions about data quality.

## Testing Strategy

### Performance Testing

**Load Testing Requirements**:
- Sustained 100 requests/second
- P50 < 8 seconds, P95 < 15 seconds
- Memory usage < 512MB under load

**Benchmark Scenarios**:
- Cache hit scenarios (< 50ms expected)
- Primary source success (< 5s expected)
- Fallback scenarios (< 15s expected)
- Timeout scenarios (2.5s + processing time)

### Integration Testing

**Source Reliability Testing**:
- Mock HTTP responses for deterministic testing
- Real source integration tests (daily)
- Fallback chain validation
- Cache invalidation testing

**Data Quality Testing**:
- Bounds checking validation
- Unit conversion accuracy
- Fuzzy matching precision/recall
- LLM output consistency

### Monitoring and Observability

**Key Metrics**:
- Response time percentiles (P50, P90, P95, P99)
- Cache hit rates by source type
- Source success rates and failure modes
- LLM processing time and token usage

**Alerting Thresholds**:
- P95 response time > 15 seconds
- Cache hit rate < 60%
- Primary source failure rate > 10%
- LLM timeout rate > 5%

## Performance Optimizations

### Caching Strategy

**Multi-Level Caching**:
1. In-memory LRU cache (1000 entries)
2. Database evidence store (30-day TTL)
3. CDN caching for static source mappings

### Connection Pooling

**HTTP Client Configuration**:
- Connection pool size: 50 connections
- Keep-alive timeout: 30 seconds
- DNS caching: 5 minutes
- Retry policy: 2 retries with exponential backoff

### Database Optimization

**Evidence Store Schema**:
```sql
CREATE INDEX idx_cache_key ON evidence_store (year, make, model, drivetrain, engine);
CREATE INDEX idx_created_at ON evidence_store (created_at);
CREATE INDEX idx_source_type ON evidence_store (primary_source_type);
```

**Design Decision**: Composite index on cache key components enables fast lookups, while temporal and source-type indexes support cache management and analytics queries.