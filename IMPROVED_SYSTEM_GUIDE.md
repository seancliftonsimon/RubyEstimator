# Improved Vehicle Data System Guide

## Overview

This document describes the comprehensive improvements to the Ruby GEM Estimator's vehicle data resolution system. The improvements address key issues with data quality, decision-making, and user experience.

## What Changed and Why

### Before: Issues with the Current System

1. **Single values without context**: Only stored one number (e.g., 3500 lbs) without ranges or uncertainty indication
2. **No source quality distinction**: Treated OEM specs and forum posts equally
3. **Ad-hoc decision making**: Inconsistent logic scattered throughout code
4. **Silent low-quality writes**: Database filled with possibly-wrong values without clear indicators
5. **Verbose scattered warnings**: Hard to scan, repeated paragraphs of warnings

### After: Improved System

1. **Ranges with metadata**: Store `{low: 3450, high: 3550, chosen: 3500}` with `estimate_type: "median_of_trusted"`
2. **Evidence scoring**: Source taxonomy with trust weights (OEM=1.0, KBB/Edmunds=0.7, forums=0.4)
3. **Clear decision rules**: Predictable, consistent rules per attribute
4. **Confidence gates**: Only write to DB if confidence ≥ 0.7 AND evidence_weight ≥ 0.7
5. **Consolidated reports**: One compact report per vehicle with all metadata

## Key Components

### 1. New Data Models (`improved_data_models.py`)

#### SourceTrust Enum

```python
class SourceTrust(Enum):
    HIGH = 1.0      # OEM specs, owner's manual, official parts catalogs
    MEDIUM = 0.7    # KBB, Edmunds, Cars.com, MotorTrend
    LOW = 0.4       # Dealer listings, parts retailers, forums
    UNKNOWN = 0.2   # Unverified sources
```

**Automatic classification**: Sources are automatically classified based on URL/name patterns.

#### ValueRange

Stores numeric fields with ranges:

```python
@dataclass
class ValueRange:
    low: Optional[float]           # Minimum value found
    high: Optional[float]          # Maximum value found
    chosen: Optional[float]        # Selected value (median, consensus, etc.)
    estimate_type: str             # "median_of_trusted", "single_source", etc.
    variant_needed_for_exact: bool # True if range exists due to trim/engine variants
```

#### EvidenceScore

Tracks evidence quality:

```python
@dataclass
class EvidenceScore:
    weighted_score: float          # Sum of (source_trust × confidence)
    source_count: int              # Number of sources
    highest_trust: SourceTrust     # Best source quality
    sources: List[Dict]            # Detailed source info
```

#### FieldResolution

Complete resolution metadata for one field:

```python
@dataclass
class FieldResolution:
    field_name: str
    value_range: Optional[ValueRange]
    conditional_values: List[ConditionalFact]  # Trim/engine-specific values
    evidence: Optional[EvidenceScore]
    confidence: float
    status: Literal["ok", "needs_review", "insufficient_data"]
    decision_rule_applied: str
    warnings: List[str]
```

#### ResolutionReport

Consolidated report for entire vehicle:

```python
@dataclass
class ResolutionReport:
    vehicle_key: str
    strategy: str                  # "single_call", "multi_call", "cached"
    outcome: Literal["complete", "partial", "failed"]

    # Field resolutions
    curb_weight: Optional[FieldResolution]
    aluminum_engine: Optional[FieldResolution]
    aluminum_rims: Optional[FieldResolution]
    catalytic_converters: Optional[FieldResolution]

    # Overall status
    overall_confidence: float
    fields_resolved: List[str]
    fields_needing_review: List[str]
    action_needed: bool
```

**Compact report format**: Replaces verbose warnings with scannable summary.

### 2. Decision Rules (`improved_data_models.py` - DecisionRules class)

#### Curb Weight

```python
def resolve_curb_weight(candidates) -> FieldResolution:
    # Rule: Take median of HIGH and MEDIUM trust sources
    # Store {low, high, chosen}
    # Require min_evidence_weight ≥ 0.7
```

**Logic**:

- Only use HIGH/MEDIUM trust sources for calculation
- Calculate median as chosen value
- Flag `variant_needed_for_exact=True` if range > 10% of median
- Set `status="ok"` only if confidence ≥ 0.7 AND evidence_weight ≥ 0.7

#### Aluminum Engine

```python
def resolve_aluminum_engine(candidates) -> FieldResolution:
    # Rule: Boolean with high evidence bar (prefer OEM docs)
    # Once true with high confidence, it's variant-stable
```

**Logic**:

- Weight votes by source trust (HIGH source vote = 1.0, MEDIUM = 0.7, etc.)
- Require strong agreement (≥75%) for high confidence
- Prefer HIGH trust sources for boolean decisions
- Set `status="ok"` only if confidence ≥ 0.7

#### Aluminum Rims

```python
def resolve_aluminum_rims(candidates) -> FieldResolution:
    # Rule: Trim-dependent with market default
    # Store exceptions as conditional facts
```

**Logic**:

- Track trim-specific values in `conditional_values`
- Default to most common across all trims
- Flag `variant_needed_for_exact=True` if multiple trim variants exist
- Set `estimate_type="most_common_in_market"` when trim unknown

#### Catalytic Converters

```python
def resolve_catalytic_converters(candidates) -> FieldResolution:
    # Rule: Engine-dependent with range
    # If engine unknown, store range without choosing
```

**Logic**:

- Track engine-specific counts in `conditional_values`
- Store range (e.g., low=1, high=2) when variant unknown
- Set `chosen=None` if evidence insufficient (don't guess)
- Set `estimate_type="unknown_pending_variant"` when uncertain
- Lower threshold (0.6) due to difficulty obtaining exact data

### 3. Enhanced Database Schema (`enhanced_database_schema.py`)

New table: `enhanced_resolutions`

**Key columns**:

- `final_value`, `value_low`, `value_high`: Store ranges
- `estimate_type`: How value was determined
- `variant_needed`: Whether exact value needs trim/engine info
- `evidence_weight`: Weighted evidence score
- `evidence_sources`: JSON array of source details with trust levels
- `conditional_facts`: JSON array of trim/engine-specific values
- `decision_rule`: Which rule was applied
- `status`: "ok", "needs_review", or "insufficient_data"

**Migration**: Automatically migrates data from old `resolutions` table.

### 4. Integration Layer (`improved_resolution_integration.py`)

Bridges existing code with new models:

- **Converters**: `convert_search_candidates_to_dict()`, `convert_single_call_result_to_resolutions()`
- **Storage**: `store_resolution_report()`, `get_cached_resolution_report()`
- **Write control**: `should_write_to_database()` - enforces confidence and evidence thresholds
- **Legacy support**: `extract_values_for_legacy_db()` - gets simple values for old `vehicles` table

### 5. Improved Processor (`improved_vehicle_processor.py`)

Drop-in replacement for `process_vehicle()`:

```python
processor = ImprovedVehicleProcessor(
    api_key=api_key,
    confidence_threshold=0.7,
    use_cache=True
)

report = processor.process_vehicle(year, make, model, progress_callback)

# Get values approved for database write
db_values = processor.get_values_for_database(report)
```

**Strategy**:

1. Check cache for complete high-confidence data
2. Try single-call resolution
3. Fallback to multi-call with decision rules
4. Generate consolidated report
5. Only write to DB if thresholds met

## Benefits

### 1. Honest Data Model

- **Range storage**: `{low: 3450, high: 3550, chosen: 3500}` shows uncertainty
- **Variant awareness**: `variant_needed_for_exact=True` flags trim-dependent fields
- **Conditional facts**: Store "base trim = steel, sport trim = aluminum" explicitly

### 2. Quality Control

- **Source taxonomy**: Automatic trust weighting (OEM > KBB > forums)
- **Evidence scoring**: `evidence_weight` combines source trust and confidence
- **Write gates**: Only write if `confidence ≥ 0.7` AND `evidence_weight ≥ 0.7`

### 3. Predictable Decisions

- **Per-field rules**: Curb weight = median_of_trusted, Engine = OEM_preferred, etc.
- **Consistent behavior**: Same inputs always produce same outputs
- **Clear provenance**: `decision_rule_applied` field shows which rule was used

### 4. Better UX

- **Compact reports**: One-page summary replaces verbose warnings
- **Clear status**: "ok" / "needs_review" / "insufficient_data"
- **Action items**: `action_needed` flag highlights issues
- **Confidence visible**: Show users when data is uncertain

## Example Output

### Consolidated Resolution Report

```
=== Resolution Report: 2022 Toyota Camry ===
Strategy: single_call | Outcome: complete | Confidence: 0.85

• curb_weight:
  Value: 3310
  Confidence: 0.85 | Status: ok
  Range: [3280 - 3340] (median_of_trusted)
  Evidence: 3 sources (trust: HIGH, score: 2.55)
    - Toyota.com official specs
    - KBB.com
    - Edmunds.com

• aluminum_engine:
  Value: True
  Confidence: 0.90 | Status: ok
  Evidence: 2 sources (trust: HIGH, score: 1.8)
    - Toyota.com official specs
    - MotorTrend technical review

• aluminum_rims:
  Value: True
  Confidence: 0.80 | Status: ok
  ⚠ Trim-dependent: 3 variants found - default set to most common
  Evidence: 4 sources (trust: MEDIUM, score: 2.24)
    - Cars.com trim comparison
    - KBB.com features
    - Edmunds.com

• catalytic_converters:
  Value: 2
  Confidence: 0.70 | Status: ok
  Range: [2 - 2] (engine_dependent)
  Evidence: 2 sources (trust: MEDIUM, score: 1.4)
    - EPA emissions data
    - MotorTrend specs

Action needed: NO
```

**Compare to current system**: ~20 lines vs ~100+ lines of warnings and logs.

## Migration Strategy

### Phase 1: Run in Parallel (Recommended)

Keep existing system, add new system alongside:

1. Initialize enhanced database:

   ```python
   from improved_resolution_integration import initialize_enhanced_database
   initialize_enhanced_database()
   ```

2. Update `process_vehicle()` to use improved processor:

   ```python
   from improved_vehicle_processor import ImprovedVehicleProcessor

   processor = ImprovedVehicleProcessor(api_key=GEMINI_API_KEY)
   report = processor.process_vehicle(year, make, model, progress_callback)

   if report:
       # Write to enhanced DB
       store_resolution_report(report)

       # Also write to legacy DB for compatibility
       legacy_values = processor.get_values_for_database(report)
       if legacy_values.get('curb_weight_lbs'):
           update_vehicle_data_in_db(
               year, make, model,
               legacy_values['curb_weight_lbs'],
               legacy_values.get('aluminum_engine'),
               legacy_values.get('aluminum_rims'),
               legacy_values.get('catalytic_converters')
           )
   ```

3. Monitor both systems, compare results

### Phase 2: Full Migration

Once confident in new system:

1. Update UI to show resolution reports instead of simple values
2. Expose ranges and confidence scores to users
3. Add "needs review" queue for fields with `status="needs_review"`
4. Retire old `process_vehicle()` function

## Configuration

### Confidence Thresholds

```python
# In improved_data_models.py - DecisionRules class
MIN_CONFIDENCE_FOR_WRITE = 0.7      # Minimum confidence to write to DB
MIN_EVIDENCE_WEIGHT_FOR_WRITE = 0.7 # Minimum evidence quality
MIN_SOURCES_FOR_WRITE = 1           # Minimum number of sources
```

### Per-Field Thresholds

- Curb weight: 0.7 (standard)
- Aluminum engine: 0.7 (high bar for OEM-level certainty)
- Aluminum rims: 0.7 (standard, but track trim variants)
- Catalytic converters: 0.6 (lower due to data availability challenges)

### Source Classification

Customize in `improved_data_models.py - SourceTrust.classify_source()`:

```python
high_indicators = [
    'manufacturer', 'official', 'oem', 'owner', 'manual',
    'parts catalog', 'service manual', 'window sticker'
]
medium_indicators = [
    'kbb', 'edmunds', 'cars.com', 'autotrader',
    'motortrend', 'caranddriver', 'nhtsa', 'epa'
]
low_indicators = [
    'forum', 'dealer', 'listing', 'aftermarket', 'ebay'
]
```

## Testing

Run demonstration:

```bash
python improved_vehicle_processor.py
```

Run tests:

```bash
python -m pytest test_improved_system.py
```

## Files Summary

| File                                 | Purpose                                           |
| ------------------------------------ | ------------------------------------------------- |
| `improved_data_models.py`            | Core data models, decision rules, source taxonomy |
| `enhanced_database_schema.py`        | Enhanced database schema with ranges and metadata |
| `improved_resolution_integration.py` | Integration layer, converters, storage functions  |
| `improved_vehicle_processor.py`      | Improved processor with new logic                 |
| `IMPROVED_SYSTEM_GUIDE.md`           | This documentation                                |

## Future Enhancements

1. **Variant resolution**: Integrate with VIN decoding to resolve trim/engine automatically
2. **Learning system**: Track which sources consistently provide accurate data
3. **User feedback**: Allow users to confirm/correct values, improve evidence weights
4. **Admin dashboard**: Review queue for `needs_review` fields
5. **API exposing uncertainty**: Let clients see ranges and confidence scores

## Questions?

For implementation questions, see inline documentation in each module.
For decision rule customization, see `DecisionRules` class in `improved_data_models.py`.
For database schema details, see `enhanced_database_schema.py`.
