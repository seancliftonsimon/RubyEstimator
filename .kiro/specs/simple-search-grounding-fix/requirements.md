# Requirements Document

## Introduction

The Ruby GEM Estimator application currently uses the legacy `google.generativeai` SDK which causes "Unknown field for FunctionDeclaration: google_search" errors. Based on the Google Gemini cookbook (Search_Grounding.ipynb), the application needs to be updated to use the modern `google-genai` SDK with the correct API patterns to make search grounding work.

## Glossary

- **google-genai SDK**: The modern Python SDK for Google Gemini API that supports search grounding
- **google.generativeai SDK**: The legacy Python SDK causing current errors
- **Search Grounding**: Google AI feature for web search capabilities
- **Client-based API**: Modern API pattern using `genai.Client()`
- **Ruby GEM Estimator**: The vehicle data resolution application

## Requirements

### Requirement 1

**User Story:** As a system administrator, I want the search grounding to work without errors, so that vehicle data resolution can access web information.

#### Acceptance Criteria

1. THE Ruby_GEM_Estimator SHALL use the `google-genai` SDK instead of `google.generativeai`
2. THE Ruby_GEM_Estimator SHALL use the client-based API pattern with `genai.Client()`
3. THE Ruby_GEM_Estimator SHALL use the config-based tool specification: `config={"tools": [{"google_search": {}}]}`
4. THE Ruby_GEM_Estimator SHALL eliminate "Unknown field for FunctionDeclaration" errors
5. THE Ruby_GEM_Estimator SHALL maintain existing vehicle data resolution functionality

### Requirement 2

**User Story:** As a developer, I want the implementation to follow the cookbook patterns, so that it's reliable and maintainable.

#### Acceptance Criteria

1. THE Ruby_GEM_Estimator SHALL use `client.models.generate_content()` method for API calls
2. THE Ruby_GEM_Estimator SHALL use Gemini 2.0+ models (gemini-2.5-flash)
3. THE Ruby_GEM_Estimator SHALL handle API responses in the same format as before
4. THE Ruby_GEM_Estimator SHALL maintain the same function interfaces
5. THE Ruby_GEM_Estimator SHALL work with existing error handling patterns