# Design Document

## Overview

This design addresses the comprehensive upgrade of the Ruby GEM Estimator's search grounding implementation from the legacy `google.generativeai` SDK to the modern `google-genai` SDK (v1.0.0+). Based on the official Google Gemini cookbook patterns, this upgrade will resolve current API compatibility issues and provide enhanced search grounding capabilities with better error handling, debugging features, and future-proof architecture.

The design follows the cookbook's recommended patterns including client-based API usage, config-based tool specification, and proper grounding metadata handling.

## Architecture

### Current vs. New Architecture

**Current (Legacy) Architecture:**
```python
import google.generativeai as genai
model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content(prompt, tools=[{"google_search": {}}])
```

**New (Modern) Architecture:**
```python
from google import genai
client = genai.Client()
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config={"tools": [{"google_search": {}}]}
)
```

### Key Architectural Changes

1. **SDK Migration**: Replace `google.generativeai` with `google-genai`
2. **Client Pattern**: Use centralized client instead of direct model instantiation
3. **Config-based Tools**: Move tool specification to config parameter
4. **Enhanced Models**: Upgrade to Gemini 2.0+ models with better search capabilities
5. **Metadata Access**: Implement grounding metadata extraction for transparency

## Components and Interfaces

### 1. Enhanced GroundedSearchClient (resolver.py)

**New Implementation Pattern:**
```python
from google import genai

class GroundedSearchClient:
    def __init__(self):
        self.client = genai.Client()
        self.model_id = "gemini-2.5-flash"
        
    def search_vehicle_specs(self, year, make, model, field):
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=self._create_search_prompt(year, make, model, field),
            config={"tools": [{"google_search": {}}]}
        )
        
        # Extract grounding metadata
        metadata = self._extract_grounding_metadata(response)
        
        # Parse candidates with enhanced information
        candidates = self._parse_search_response(response.text, field, metadata)
        
        return candidates
```

**Interface Changes:**
- Constructor now initializes `genai.Client()` instead of model directly
- All methods use client-based API calls
- Enhanced metadata extraction and logging
- Improved error handling for new SDK patterns

### 2. Enhanced Vehicle Data Functions (vehicle_data.py)

**New Implementation Pattern:**
```python
from google import genai

# Shared client instance
SHARED_GEMINI_CLIENT = genai.Client()
MODEL_ID = "gemini-2.5-flash"

def validate_vehicle_existence(year: int, make: str, model: str):
    prompt = f"Does the {year} {make} {model} exist as a real vehicle?"
    
    response = SHARED_GEMINI_CLIENT.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config={"tools": [{"google_search": {}}]}
    )
    
    # Log grounding metadata
    _log_grounding_metadata(response, f"{year} {make} {model}")
    
    return _parse_validation_response(response.text)
```

**Interface Changes:**
- Replace `SHARED_GEMINI_MODEL` with `SHARED_GEMINI_CLIENT`
- Update all function calls to use client-based pattern
- Add grounding metadata logging
- Enhanced error handling and debugging

### 3. New Grounding Metadata Handler

**New Component:**
```python
class GroundingMetadataHandler:
    @staticmethod
    def extract_metadata(response):
        """Extract grounding metadata from API response."""
        if not hasattr(response, 'candidates') or not response.candidates:
            return None
            
        candidate = response.candidates[0]
        if not hasattr(candidate, 'grounding_metadata'):
            return None
            
        metadata = candidate.grounding_metadata
        return {
            'search_queries': getattr(metadata, 'web_search_queries', []),
            'grounding_chunks': getattr(metadata, 'grounding_chunks', []),
            'search_entry_point': getattr(metadata, 'search_entry_point', None)
        }
    
    @staticmethod
    def log_grounding_info(metadata, context):
        """Log grounding information for debugging."""
        if not metadata:
            return
            
        logging.info(f"Search grounding for {context}:")
        logging.info(f"  Queries: {metadata.get('search_queries', [])}")
        logging.info(f"  Sources: {len(metadata.get('grounding_chunks', []))} chunks")
```

## Data Models

### Enhanced SearchCandidate

```python
@dataclass
class SearchCandidate:
    value: float
    source: str
    citation: str
    confidence: float
    raw_text: str
    # New fields for enhanced metadata
    grounding_chunk_id: Optional[str] = None
    search_query: Optional[str] = None
    source_url: Optional[str] = None
```

### New GroundingMetadata

```python
@dataclass
class GroundingMetadata:
    search_queries: List[str]
    source_urls: List[str]
    grounding_chunks: List[Dict[str, Any]]
    search_entry_point: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
```

## Error Handling

### Enhanced Error Handling Strategy

1. **SDK-Specific Errors**: Handle new error types from `google-genai` SDK
2. **Graceful Degradation**: Fallback to non-search methods when search grounding fails
3. **Detailed Logging**: Log SDK version, model version, and specific error details
4. **Retry Logic**: Implement exponential backoff for transient API errors

```python
def handle_search_grounding_error(error, context):
    """Enhanced error handling for new SDK."""
    error_type = type(error).__name__
    error_message = str(error)
    
    logging.error(f"Search grounding error in {context}:")
    logging.error(f"  Error type: {error_type}")
    logging.error(f"  Error message: {error_message}")
    logging.error(f"  SDK version: google-genai {genai.__version__}")
    
    # Specific handling for common new SDK errors
    if "quota" in error_message.lower():
        return handle_quota_error(context)
    elif "authentication" in error_message.lower():
        return handle_auth_error(context)
    else:
        return handle_generic_error(error, context)
```

## Testing Strategy

### Comprehensive Testing Approach

1. **SDK Migration Tests**: Verify all API calls work with new SDK
2. **Functionality Tests**: Ensure all vehicle data resolution functions work correctly
3. **Metadata Tests**: Verify grounding metadata extraction and logging
4. **Error Handling Tests**: Test error scenarios and fallback mechanisms
5. **Performance Tests**: Compare performance with legacy implementation

### Test Categories

```python
class TestSearchGroundingUpgrade:
    def test_sdk_migration(self):
        """Test that new SDK works correctly."""
        
    def test_client_initialization(self):
        """Test client-based API initialization."""
        
    def test_config_based_tools(self):
        """Test config-based tool specification."""
        
    def test_grounding_metadata_extraction(self):
        """Test metadata extraction and logging."""
        
    def test_enhanced_error_handling(self):
        """Test new error handling patterns."""
        
    def test_performance_comparison(self):
        """Compare performance with legacy implementation."""
```

## Implementation Considerations

### Migration Strategy

1. **Phased Rollout**: Implement changes incrementally to minimize risk
2. **Backward Compatibility**: Maintain fallback to legacy SDK during transition
3. **Configuration Management**: Use environment variables to control SDK selection
4. **Monitoring**: Implement comprehensive logging to track migration success

### Dependencies

**New Dependencies:**
```
google-genai>=1.0.0
```

**Removed Dependencies:**
```
google-generativeai  # Legacy SDK
```

### Configuration Updates

**Environment Variables:**
```
GEMINI_API_KEY=your_api_key
GEMINI_MODEL_ID=gemini-2.5-flash  # New default model
SEARCH_GROUNDING_ENABLED=true
GROUNDING_METADATA_LOGGING=true
```

## Performance Optimizations

### Enhanced Performance Features

1. **Model Efficiency**: Gemini 2.0+ models provide better performance
2. **Client Reuse**: Single client instance reduces initialization overhead
3. **Metadata Caching**: Cache grounding metadata to reduce redundant logging
4. **Batch Processing**: Support for batch requests where applicable

### Monitoring and Metrics

```python
class SearchGroundingMetrics:
    def __init__(self):
        self.api_calls = 0
        self.successful_searches = 0
        self.failed_searches = 0
        self.average_response_time = 0
        self.grounding_metadata_extracted = 0
        
    def log_search_attempt(self, success, response_time, has_metadata):
        """Log metrics for each search attempt."""
        self.api_calls += 1
        if success:
            self.successful_searches += 1
        else:
            self.failed_searches += 1
            
        if has_metadata:
            self.grounding_metadata_extracted += 1
            
        self.average_response_time = (
            (self.average_response_time * (self.api_calls - 1) + response_time) 
            / self.api_calls
        )
```

## Security Considerations

### Enhanced Security Features

1. **API Key Management**: Secure handling of API keys with new SDK
2. **Request Validation**: Validate all inputs before API calls
3. **Response Sanitization**: Sanitize grounding metadata before logging
4. **Rate Limiting**: Implement proper rate limiting for new API patterns

## Deployment Strategy

### Rollout Plan

1. **Development Environment**: Test new SDK integration thoroughly
2. **Staging Environment**: Deploy with feature flags for gradual testing
3. **Production Rollout**: Phased deployment with monitoring and rollback capability
4. **Legacy Cleanup**: Remove old SDK dependencies after successful migration

### Rollback Strategy

```python
# Feature flag for SDK selection
USE_NEW_SDK = os.getenv('USE_NEW_SEARCH_GROUNDING_SDK', 'false').lower() == 'true'

if USE_NEW_SDK:
    from google import genai
    client = genai.Client()
else:
    import google.generativeai as genai
    # Legacy implementation
```

This design provides a comprehensive upgrade path that follows Google's latest recommendations while maintaining system reliability and providing enhanced capabilities for vehicle data resolution.