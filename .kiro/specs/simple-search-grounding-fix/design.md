# Design Document

## Overview

This design provides a simple, direct fix for the search grounding issues by updating to the modern `google-genai` SDK and following the cookbook patterns. The goal is to make search grounding work with minimal changes to existing code.

## Architecture

### Simple SDK Migration

**Current (Broken):**
```python
import google.generativeai as genai
model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content(prompt, tools=[{"google_search": {}}])
```

**New (Working):**
```python
from google import genai
client = genai.Client()
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config={"tools": [{"google_search": {}}]}
)
```

## Components and Interfaces

### 1. Update resolver.py

**Key Changes:**
- Replace `import google.generativeai as genai` with `from google import genai`
- Replace `genai.GenerativeModel()` with `genai.Client()`
- Change `tools=[...]` to `config={"tools": [...]}`
- Update model name to `gemini-2.5-flash`

### 2. Update vehicle_data.py

**Key Changes:**
- Replace SDK import
- Update shared model instance to use client
- Update all API calls to use new pattern
- Keep all existing function signatures the same

## Implementation Strategy

### Minimal Change Approach

1. **SDK Replacement**: Simply swap the SDK and update import statements
2. **API Pattern Update**: Change from direct model calls to client-based calls
3. **Tool Configuration**: Move tools from parameter to config
4. **Model Update**: Use newer model that supports search grounding properly
5. **Keep Everything Else**: Maintain all existing logic, error handling, and interfaces

### Backward Compatibility

- All function signatures remain the same
- Response parsing logic stays the same
- Error handling patterns remain unchanged
- Database operations unchanged
- UI integration unchanged

## Testing Strategy

### Simple Validation

1. **Basic Functionality**: Test that search grounding calls complete without errors
2. **Response Format**: Verify responses are parsed correctly
3. **Vehicle Data**: Test actual vehicle data resolution works
4. **Error Handling**: Ensure existing error handling still works

## Deployment

### Simple Rollout

1. Update requirements.txt
2. Update import statements
3. Update API call patterns
4. Test basic functionality
5. Deploy

This approach focuses on the minimum changes needed to make search grounding work reliably.