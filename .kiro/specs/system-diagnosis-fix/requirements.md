# Requirements Document

## Introduction

The Ruby GEM Estimator system is experiencing critical failures in both database operations and Google AI API integration that prevent the vehicle search and valuation functionality from working correctly. The system is designed for online hosting with PostgreSQL in production environments like Railway, while using SQLite as a local testing environment for development. The system needs comprehensive diagnosis and fixes to ensure reliable operation across both environments.

## Glossary

- **SQLite**: Local testing database for development environment using file-based storage
- **PostgreSQL**: Production database system for online hosting on platforms like Railway
- **Google AI API**: Google's Generative AI service for grounded search functionality
- **SQL Syntax Compatibility**: Ensuring queries work across different database systems
- **API Model Versioning**: Correct model names and API endpoints for Google AI services
- **Environment Configuration**: Proper setup of database connections and API credentials
- **Cross-Platform Deployment**: System working consistently across local and cloud environments

## Requirements

### Requirement 1

**User Story:** As a system administrator, I want to diagnose and fix the critical database syntax errors that are preventing the system from working, so that vehicle search functionality operates correctly in both local testing and online production environments.

#### Acceptance Criteria

1. THE System SHALL replace the failing "NOW() - INTERVAL '24 hours'" PostgreSQL syntax with database-agnostic alternatives
2. THE System SHALL use datetime functions compatible with both SQLite (local testing) and PostgreSQL (online production)
3. THE System SHALL successfully execute resolution queries without syntax errors in both database environments
4. THE System SHALL handle database connection configuration automatically based on environment detection
5. THE System SHALL provide proper error handling for database operations to prevent cascading failures

### Requirement 2

**User Story:** As a system user, I want to fix the "404 models/gemini-1.5-flash-latest is not found" error that is breaking vehicle validation and search functionality, so that the Google AI integration works correctly.

#### Acceptance Criteria

1. THE System SHALL identify and use the correct current Google AI model names instead of "gemini-1.5-flash-latest"
2. THE System SHALL successfully make API calls to Google AI without receiving 404 model not found errors
3. THE System SHALL validate API credentials and configuration before attempting vehicle searches
4. THE System SHALL provide proper fallback mechanisms when API calls fail to prevent complete system failure
5. THE System SHALL successfully resolve vehicle data for valid vehicles like "2013 Toyota Camry"

### Requirement 3

**User Story:** As a developer, I want comprehensive error handling and logging throughout the system, so that I can quickly identify and resolve issues in both development and production.

#### Acceptance Criteria

1. THE System SHALL provide detailed error logging for all database operations
2. THE System SHALL log API call failures with request details and response codes
3. WHEN critical errors occur, THE System SHALL provide user-friendly error messages
4. THE System SHALL implement proper exception handling to prevent application crashes
5. THE System SHALL maintain error logs that can be used for system monitoring and debugging

### Requirement 4

**User Story:** As a system administrator, I want the application to detect and configure itself correctly for different deployment environments, so that it works seamlessly in local testing and online production hosting.

#### Acceptance Criteria

1. THE System SHALL automatically detect whether it's running in local testing or online production environment
2. THE System SHALL configure database connections appropriately for online hosting platforms based on available environment variables
3. THE System SHALL provide environment-specific configuration validation for production deployments
4. THE System SHALL handle missing environment variables gracefully with appropriate defaults for local testing
5. THE System SHALL display clear status information about the current environment configuration for both testing and production

### Requirement 5

**User Story:** As a system user, I want the vehicle search and validation functionality to work correctly without encountering the current API and database errors, so that I can get accurate vehicle valuations for "2013 Toyota Camry" and other vehicles.

#### Acceptance Criteria

1. THE System SHALL resolve the "404 models/gemini-1.5-flash-latest is not found" error by using correct Google AI model names
2. THE System SHALL fix the SQLite syntax error "near '24 hours': syntax error" by using database-compatible date/time functions
3. THE System SHALL successfully validate vehicle existence and return proper weight data for valid vehicles like "2013 Toyota Camry"
4. THE System SHALL handle the transition from "Vehicle validation inconclusive" to successful data resolution
5. THE System SHALL prevent the cascade of failures that leads to marking valid vehicles as "not found"

## Error Analysis

Based on the provided error output, the system is failing due to:

**Database Syntax Errors:**
```
(sqlite3.OperationalError) near "'24 hours'": syntax error
[SQL:SELECT field_name, final_value, confidence_score, created_at
FROM resolutions
WHERE vehicle_key = ?
AND created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC]
```

**Google AI API Errors:**
```
404 models/gemini-1.5-flash-latest is not found for API version v1beta, 
or is not supported for generateContent
```

**Cascading Failures:**
- Vehicle validation fails due to API error
- Database queries fail due to SQL syntax incompatibility
- System incorrectly marks valid vehicle "2013 Toyota Camry" as not found
- All resolution attempts fail leading to complete system failure


# Error message:


  You can now view your Streamlit app in your browser.

  Network URL: http://192.168.1.158:8501
  External URL: http://108.51.151.161:8501

✅ Resolutions table created successfully
=== DATABASE SETUP ===
DATABASE_URL: Not set
PGHOST: Not set
PGPORT: Not set
PGDATABASE: Not set
PGUSER: Not set
PGPASSWORD: Not set
Database connection: Database connection successful
✅ Database tables created successfully
✅ Database connection successful
Processing: 2013 Toyota Camry
Error getting resolution data from database: (sqlite3.OperationalError) near "'24 hours'": syntax error
[SQL:
                SELECT field_name, final_value, confidence_score, created_at
                FROM resolutions
                WHERE vehicle_key = ?
                AND created_at > NOW() - INTERVAL '24 hours'
                ORDER BY created_at DESC
            ]
[parameters: ('2013_Toyota_Camry',)]
(Background on this error at: https://sqlalche.me/e/20/e3q8)
  -> Not in DB or missing data. Validating vehicle existence first...
An error occurred during the vehicle validation API call: 404 models/gemini-1.5-flash-latest is not found for API version v1beta, or is not supported for generateContent. Call ListModels to see the list of available models and their supported methods.
  -> Vehicle validation inconclusive for: 2013 Toyota Camry
  -> Proceeding with resolver-based queries...
Error getting cached resolution: (sqlite3.OperationalError) near "'24 hours'": syntax error     
[SQL:
                    SELECT final_value, confidence_score, method, candidates_json, warnings_json, created_at
                    FROM resolutions
                    WHERE vehicle_key = ? AND field_name = ?
                    AND created_at > NOW() - INTERVAL '24 hours'
                    ORDER BY created_at DESC
                    LIMIT 1
                ]
[parameters: ('2013_Toyota_Camry', 'curb_weight')]
(Background on this error at: https://sqlalche.me/e/20/e3q8)
ERROR:root:Error in grounded search for curb_weight: 404 models/gemini-1.5-flash-latest is not fERROR:root:Error in grounded search for curb_weight: 404 models/gemini-1.5-flash-latest is not found for API version v1beta, or is not supported for generateContent. Call ListModels to see the list of available models and their supported methods.
Error in grounded search for curb_weight: 404 models/gemini-1.5-flash-latest is not found for API version v1beta, or is not supported for generateContent. Call ListModels to see the list of available models and their supported methods.
  -> No candidates found for curb weight via grounded search
  -> No candidates found for curb weight via grounded search
  -> Resolver approach failed for curb weight resolution, attempting fallback...
  -> Resolver approach failed for curb weight resolution, attempting fallback...
  -> Attempt 1 failed: 404 models/gemini-1.5-flash-latest is not found for API version v1beta, or is not supported for theitheirththeir supported methods.. Retrying in 1.1s...
  -> All 2 attempts failed. Last error: 404 models/gemini-1.5-flash-latest is not found for API version v1beta, or is not supported for generateContent. Call ListModels to see the list of available models and their supported methods.
  -> Both resolver and fallback failed for curb weight resolution
  -> No weight found and vehicle existence inconclusive - likely fake vehicle
✅ Marked vehicle as not found in session: 2013 Toyota Camry

