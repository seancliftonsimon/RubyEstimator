# Admin UI Guide

## Overview

The Ruby GEM application now includes a comprehensive admin interface for managing all configuration values. This allows you to easily customize prices, costs, weights, and other settings without editing code.

## Accessing Admin Mode

### Admin Button

- A **⚙️ Admin** button is located in the top-right corner of the main page
- Click it to enter admin mode
- The button changes to **✕ Close Admin** when in admin mode
- Click again to return to the main application

## Admin Interface Features

### Navigation

The admin interface uses a tabbed layout with 7 main sections:

1. **💰 Prices** - Commodity prices per pound
2. **💵 Costs** - Flat costs (purchase, tow, etc.)
3. **⚖️ Weights** - Component weights
4. **📊 Assumptions** - Calculation assumptions and factors
5. **🔍 Heuristics** - Keywords and rules for cat counts
6. **🌐 Grounding** - Gemini search grounding settings
7. **🤝 Consensus** - Source weighting and preferences

### Restore to Default Functionality

Each section has a **🔄 Restore to Default** button in the top-right corner:

- Click to reset **only that section** to factory defaults
- Other sections remain unchanged
- Changes take effect immediately in the form

### Saving Changes

- After editing values, click **💾 Save All Changes** at the bottom
- All changes are saved to the database
- Configuration is reloaded automatically
- Changes persist across sessions

## Configuration Sections

### 1. Prices ($/lb)

Editable table of commodity prices:

- ELV (End-of-Life Vehicle)
- Aluminum Engine
- Iron Engine
- Wiring Harness
- Iron Radiator
- Breakage
- Alternator
- Starter
- A/C Compressor
- Fuse Box
- Battery
- Aluminum Rims
- Catalytic Converters
- Tires
- ECM (Engine Control Module)

### 2. Flat Costs

Fixed cost values:

- **PURCHASE** - Vehicle purchase price
- **TOW** - Towing cost
- **LEAD_PER_CAR** - Lead cost per vehicle
- **NUT_PER_LB** - Nut fee per pound

### 3. Component Weights (lbs)

Fixed weights for various components:

- Aluminum Rims Weight
- Battery Baseline
- Wiring Harness
- FE Radiator
- Breakage
- Alternator
- Starter
- A/C Compressor
- Fuse Box

### 4. Assumptions / Factors

Calculation factors (0-1 for percentages):

- **Engine % of curb** - Engine weight as percentage of curb weight
- **Battery Recovery** - Battery recovery factor
- **Default Cats per Car** - Average catalytic converters per vehicle
- **Unknown Engine Al Split** - Aluminum percentage for unknown engine types

### 5. Heuristics

Keywords and rules:

- **Performance Indicators** - Keywords that indicate performance vehicles (one per line)
- **V8 Keywords** - Keywords that indicate V8 engines (one per line)
- **Fallback Cats** - Default cat count when no match found

### 6. Grounding Settings

Gemini search configuration:

- **Target Candidates** - Number of search candidates to retrieve
- **Clustering Tolerance** - Tolerance for clustering similar values
- **Confidence Threshold** - Minimum confidence score
- **Outlier Threshold** - Threshold for outlier detection
- **Nut Fee Applies To** - Whether nut fee applies to curb weight or ELV weight

### 7. Consensus Settings

Source weighting and preferences:

- **Min Agreement Ratio** - Minimum agreement ratio for consensus
- **Preferred Sources** - List of preferred sources (one per line)
- **Source Weights** - Weight multipliers for different sources:
  - KBB.com
  - Edmunds.com
  - Manufacturer
  - Default

## How Defaults Work

### Default Values

All default values are defined in the application code:

- `DEFAULT_PRICE_PER_LB`
- `DEFAULT_FLAT_COSTS`
- `DEFAULT_WEIGHTS_FIXED`
- `DEFAULT_ASSUMPTIONS`
- `DEFAULT_HEURISTICS`
- `DEFAULT_GROUNDING_SETTINGS`
- `DEFAULT_CONSENSUS_SETTINGS`

### Database Override

- When you save changes, they're stored in the `app_config` database table
- The application merges database values with defaults
- Database values take precedence over code defaults
- Restore to Default removes the database override for that section

### Configuration Cache

- Configuration is cached for performance
- Cache is automatically cleared when you save changes
- This ensures new values are used immediately

## Best Practices

1. **Test Changes** - After updating values, test with a few vehicles to ensure calculations are correct
2. **Document Changes** - Keep notes on why you changed specific values
3. **Backup** - The database stores all changes with timestamps and user info
4. **Restore Carefully** - Restore to Default is immediate - there's no undo
5. **One Section at a Time** - Focus on one section when making changes

## Technical Details

### Database Schema

```sql
CREATE TABLE app_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by TEXT
)
```

### Configuration Keys

- `price_per_lb` - JSON object with price data
- `flat_costs` - JSON object with cost data
- `weights_fixed` - JSON object with weight data
- `assumptions` - JSON object with assumption data
- `heuristics` - JSON object with heuristic data
- `grounding_settings` - JSON object with grounding data
- `consensus_settings` - JSON object with consensus data

### Update Tracking

Each configuration update records:

- **key** - Configuration section
- **value** - JSON-encoded configuration data
- **description** - Human-readable description
- **updated_at** - Timestamp of last update
- **updated_by** - User who made the update (from environment variables)

## Troubleshooting

### Changes Not Saving

- Check browser console for errors
- Verify database connection
- Ensure write permissions on database file

### Values Reverting

- Check if another admin is editing simultaneously
- Verify database isn't being reset
- Check application logs

### Restore Not Working

- Refresh the page
- Check session state
- Try closing and reopening admin mode

## Security Note

This admin interface has **no authentication** by design (as requested). In a production environment, you should:

- Add password protection
- Implement role-based access control
- Log all configuration changes
- Implement change approval workflow


