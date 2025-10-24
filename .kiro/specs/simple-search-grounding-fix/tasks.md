# Implementation Plan

- [ ] 1. Update dependencies
  - Add google-genai>=1.0.0 to requirements.txt
  - Remove or comment out google-generativeai dependency
  - Test that new SDK installs correctly
  - _Requirements: 1.1_

- [ ] 2. Update resolver.py imports and client initialization
  - Replace `import google.generativeai as genai` with `from google import genai`
  - Replace `genai.GenerativeModel()` with `genai.Client()` in GroundedSearchClient.__init__
  - Update model reference to use client-based pattern
  - _Requirements: 1.1, 1.2, 2.1_

- [ ] 3. Update resolver.py API calls
  - Change `self.model.generate_content()` to `self.client.models.generate_content()`
  - Add model parameter: `model="gemini-2.5-flash"`
  - Change `tools=[{"google_search": {}}]` to `config={"tools": [{"google_search": {}}]}`
  - Update both search_vehicle_specs and get_multiple_candidates methods
  - _Requirements: 1.3, 2.1, 2.2_

- [ ] 4. Update vehicle_data.py imports and client initialization
  - Replace `import google.generativeai as genai` with `from google import genai`
  - Replace `SHARED_GEMINI_MODEL` initialization with `genai.Client()`
  - Update all references to use client instead of model
  - _Requirements: 1.1, 1.2, 2.1_

- [ ] 5. Update vehicle_data.py API calls
  - Update validate_vehicle_existence() to use client.models.generate_content()
  - Update get_aluminum_engine_from_api() to use new pattern
  - Update get_aluminum_rims_from_api() to use new pattern
  - Update get_curb_weight_from_api() to use new pattern
  - Update get_catalytic_converter_count_from_api() to use new pattern
  - Change all `tools=[{"google_search": {}}]` to `config={"tools": [{"google_search": {}}]}`
  - Add model="gemini-2.5-flash" to all calls
  - _Requirements: 1.3, 2.1, 2.2_

- [ ] 6. Test basic functionality
  - Test that imports work without errors
  - Test that client initialization works
  - Test that API calls complete without "Unknown field" errors
  - Test that responses are parsed correctly
  - _Requirements: 1.4, 1.5, 2.3, 2.4_

- [ ] 7. Test vehicle data resolution
  - Test vehicle validation with new SDK
  - Test curb weight resolution
  - Test aluminum engine detection
  - Test aluminum rims detection
  - Test catalytic converter count
  - Verify all functions return expected results
  - _Requirements: 1.5, 2.4, 2.5_