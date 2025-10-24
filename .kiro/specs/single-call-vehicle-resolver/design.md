# Single Call Vehicle Resolver Design

## Overview

This design transforms the current multi-step vehicle specification resolution system into a streamlined single-call approach. The current system uses separate grounded search calls, candidate collection, and consensus algorithms, requiring 4-6 API calls per vehicle. The new design consolidates this into one comprehensive API call that retrieves all vehicle specifications simultaneously while maintaining accuracy and reliability.

## Architecture

### Current System Architecture (To Be Replaced)
- **GroundedSearchClient**: Makes individual API calls for each specification field
- **ConsensusResolver**: Processes multiple candidates using clustering and statistical analysis
- **ProvenanceTracker**: Manages caching and resolution history
- **Multiple API Calls**: Separate calls for curb weight, engine material, rim material, and catalytic converters

### New Single Call Architecture
- **SingleCallVehicleResolver**: Unified resolver that requests all specifications in one API call
- **StructuredResponseParser**: Parses the comprehensive AI response into structured data
- **ProvenanceTracker**: Retained for caching and resolution history (existing functionality preserved)
- **Fallback Resolution**: Maintains existing fallback capabilities for error handling

## Components and Interfaces

### SingleCallVehicleResolver Class
```python
class SingleCallVehicleResolver:
    def __init__(self, api_key: str, confidence_threshold: float = 0.7)
    def resolve_all_specifications(self, year: int, make: str, model: str) -> VehicleSpecificationBundle
    def _create_comprehensive_prompt(self, year: int, make: str, model: str) -> str
    def _parse_structured_response(self, response_text: str) -> VehicleSpecificationBundle
```

### VehicleSpecificationBundle Data Structure
```python
@dataclass
class VehicleSpecificationBundle:
    curb_weight_lbs: Optional[float]
    aluminum_engine: Optional[bool]
    aluminum_rims: Optional[bool]
    catalytic_converters: Optional[int]
    confidence_scores: Dict[str, float]
    source_citations: Dict[str, List[str]]
    resolution_method: str = "single_call_resolution"
    warnings: List[str] = field(default_factory=list)
```

### Integration Points
- **Database Layer**: Maintains existing database schema and storage mechanisms
- **UI Components**: Compatible with existing progress callbacks and error handling
- **Caching System**: Leverages existing ProvenanceTracker for resolution history
- **Error Handling**: Preserves existing fallback and retry mechanisms

## Data Models

### Prompt Structure
The single comprehensive prompt will request all specifications using structured output format:

```
Search the web for complete specifications for a {year} {make} {model}. 
Prioritize authoritative sources (manufacturer websites, KBB, Edmunds).

Return the following information in JSON format:
{
  "curb_weight_lbs": <weight in pounds>,
  "aluminum_engine": <true/false for aluminum vs iron>,
  "aluminum_rims": <true/false for aluminum vs steel>,
  "catalytic_converters": <count as integer>,
  "confidence_scores": {
    "curb_weight": <0.0-1.0>,
    "engine_material": <0.0-1.0>,
    "rim_material": <0.0-1.0>,
    "catalytic_converters": <0.0-1.0>
  },
  "sources": {
    "curb_weight": ["source1", "source2"],
    "engine_material": ["source1"],
    "rim_material": ["source1"],
    "catalytic_converters": ["source1"]
  }
}
```

### Response Processing
- **JSON Parsing**: Extract structured data from AI response
- **Validation**: Ensure values are within reasonable ranges
- **Confidence Assessment**: Use AI-provided confidence scores with source quality weighting
- **Error Recovery**: Handle partial responses and missing fields gracefully

## Error Handling

### Fallback Strategy
1. **Primary**: Single call resolution with structured response
2. **Secondary**: Fallback to existing multi-call resolver system if single call fails
3. **Tertiary**: Database cache lookup for previously resolved vehicles
4. **Final**: Intelligent defaults based on vehicle characteristics

### Error Scenarios
- **API Failures**: Network timeouts, rate limits, authentication errors
- **Parsing Errors**: Malformed JSON, unexpected response format
- **Partial Data**: Some specifications resolved, others missing
- **Low Confidence**: AI indicates uncertainty in results

### Recovery Mechanisms
- **Retry Logic**: Exponential backoff for transient failures
- **Graceful Degradation**: Return partial results with appropriate warnings
- **Fallback Resolution**: Automatic switch to legacy multi-call approach
- **Cache Utilization**: Leverage existing resolution data when available

## Testing Strategy

### Unit Tests
- **SingleCallVehicleResolver**: Test prompt generation and response parsing
- **VehicleSpecificationBundle**: Validate data structure and serialization
- **Response Parser**: Test JSON parsing with various response formats
- **Error Handling**: Test fallback mechanisms and error recovery

### Integration Tests
- **End-to-End Resolution**: Test complete vehicle resolution flow
- **Database Integration**: Verify storage and retrieval of resolution results
- **Cache Behavior**: Test ProvenanceTracker integration and cache hits
- **Fallback Scenarios**: Test graceful degradation to legacy system

### Performance Tests
- **API Call Reduction**: Verify 4-6 calls reduced to 1 call per vehicle
- **Response Time**: Measure improvement in total resolution time
- **Accuracy Comparison**: Compare results with existing multi-call system
- **Confidence Scoring**: Validate AI confidence scores against known data

## Design Decisions and Rationales

### Single Comprehensive Prompt
**Decision**: Use one detailed prompt requesting all specifications simultaneously
**Rationale**: 
- Reduces API calls from 4-6 to 1 per vehicle
- Allows AI to consider relationships between specifications
- Maintains context across all fields for better accuracy
- Simplifies error handling and retry logic

### Structured JSON Response
**Decision**: Request AI to return data in structured JSON format
**Rationale**:
- Enables reliable parsing of multiple data points
- Reduces ambiguity in response interpretation
- Allows for confidence scores and source citations
- Facilitates automated validation and error detection

### Preserve ProvenanceTracker
**Decision**: Maintain existing caching and provenance tracking system
**Rationale**:
- Leverages existing database schema and storage mechanisms
- Preserves resolution history for monitoring and debugging
- Maintains cache performance benefits
- Ensures backward compatibility with existing monitoring systems

### Fallback to Legacy System
**Decision**: Keep existing multi-call resolver as fallback option
**Rationale**:
- Provides safety net for single-call failures
- Maintains system reliability during transition period
- Allows gradual migration and performance comparison
- Preserves existing error handling and recovery mechanisms

### AI-Provided Confidence Scores
**Decision**: Request confidence scores from AI rather than calculating post-hoc
**Rationale**:
- AI has access to source quality and data consistency during search
- Eliminates need for complex consensus algorithms
- Provides more accurate confidence assessment
- Simplifies resolution logic and reduces computational overhead

## Migration Strategy

### Phase 1: Implementation
- Implement SingleCallVehicleResolver class
- Create VehicleSpecificationBundle data structure
- Develop structured response parser
- Add comprehensive unit tests

### Phase 2: Integration
- Integrate with existing vehicle_data.py module
- Maintain backward compatibility with current interfaces
- Implement fallback mechanisms to legacy system
- Add integration tests and performance monitoring

### Phase 3: Deployment
- Deploy with feature flag for gradual rollout
- Monitor performance and accuracy metrics
- Compare results with legacy multi-call system
- Collect feedback and optimize prompt engineering

### Phase 4: Migration Complete
- Remove legacy GroundedSearchClient and ConsensusResolver
- Clean up unused code and dependencies
- Update documentation and monitoring dashboards
- Finalize performance optimizations