# Design Document

## Overview

The comprehensive logging system will add detailed, timestamped logging throughout the vehicle search and resolution process to provide complete transparency into system operations. The design focuses on adding logging components that capture API interactions, processing steps, and performance metrics without disrupting the existing architecture.

## Architecture

The logging system will be implemented as a lightweight set of logging utilities that integrate into the existing codebase with minimal changes. The system will enhance the current print statements with structured logging that includes timestamps and detailed information.

### Core Components

1. **API Call Logger** - Captures Gemini API interactions with timing
2. **Process Step Logger** - Logs internal processing steps with timestamps  
3. **Simple Performance Timer** - Basic timing for operations
4. **Enhanced Console Output** - Structured, readable console output

## Components and Interfaces

### 1. Enhanced Logging Module (`enhanced_logging.py`)

```python
class VehicleLogger:
    """Simple logging utility for vehicle processing operations"""
    
    def log_api_call_start(self, operation: str, vehicle_info: str, prompt: str)
    def log_api_call_end(self, operation: str, response: str, duration_ms: float)
    def log_process_step(self, step: str, details: str, duration_ms: float = None)
    def log_timing(self, operation: str, duration_ms: float)

class SimpleTimer:
    """Basic timing utility for performance measurement"""
    
    def start(self, operation_name: str) -> float
    def end(self, start_time: float, operation_name: str) -> float
```

### 2. Direct Integration Approach

The system will directly integrate logging calls into existing functions rather than using decorators, keeping the implementation simple and transparent.

### 3. Process Step Integration Points

Key integration points in the existing codebase:

- `process_vehicle()` function - Main orchestration logging
- `validate_vehicle_existence()` - Vehicle validation logging  
- `search_extract_orchestrator.resolve_vehicle()` - Two-pass system logging
- `single_call_resolver.resolve_all_specifications()` - Single-call logging
- Database operations in `vehicle_data.py`

## Data Models

The logging system will use simple string formatting rather than complex data structures to keep implementation lightweight and focused on console output readability.

## Error Handling

The logging system will implement graceful error handling to ensure that logging failures don't impact the main application:

1. **Fallback Logging** - If enhanced logging fails, fall back to basic print statements
2. **Error Isolation** - Logging errors are caught and logged separately
3. **Performance Protection** - Logging operations are designed to be lightweight
4. **Configuration Validation** - Validate logging configuration on startup

## Testing Strategy

### Basic Testing
- Test logging output during vehicle processing
- Verify timing accuracy for major operations
- Ensure logging doesn't break existing functionality

## Implementation Plan

### Phase 1: Create Logging Utility
1. Create `vehicle_logger.py` module with simple logging class
2. Implement timestamp formatting and console output
3. Add basic timing utilities

### Phase 2: Integrate API Call Logging
1. Add logging to Gemini API calls in existing resolvers
2. Log request prompts and response content
3. Add timing measurements for API calls

### Phase 3: Add Process Step Logging
1. Add detailed logging to `process_vehicle()` function
2. Log cache operations, database queries, and validation steps
3. Add timing for major processing phases

### Phase 4: Enhance Console Output
1. Improve formatting and readability of log output
2. Add visual separators between vehicles
3. Ensure compatibility with existing progress indicators

## Configuration Options

The logging system will use simple boolean flags to enable/disable detailed logging:

```python
ENABLE_DETAILED_LOGGING = True  # Enable/disable enhanced logging
ENABLE_API_LOGGING = True       # Enable/disable API call details
```

## Performance Considerations

1. **Minimal Overhead** - Simple string operations and timing calls
2. **Efficient Timing** - Use `time.time()` for basic timing measurements
3. **No Complex Storage** - Direct console output without intermediate storage

## Security and Privacy

1. **API Key Protection** - Never log API keys or sensitive credentials
2. **Response Truncation** - Limit response logging to reasonable lengths