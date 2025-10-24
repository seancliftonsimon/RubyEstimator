# Confidence Indicators and Provenance Display

This document describes the new confidence indicator and provenance display features added to the Ruby GEM Estimator.

## Overview

The confidence UI system provides visual indicators for data quality and source transparency, helping users understand the reliability of vehicle valuations and make informed decisions.

## Components

### 1. Confidence Badges

Color-coded badges that indicate the reliability of each estimate:

- **Green (High)**: 80%+ confidence - Multiple sources agree closely
- **Amber (Medium)**: 60-79% confidence - Some variation between sources  
- **Red (Low)**: <60% confidence - Significant disagreement or limited data

### 2. Warning Banners

Prominent alerts that appear when:
- Confidence levels are low
- Manual review is recommended
- Estimates are based on assumptions rather than direct data

### 3. Provenance Panels

Expandable sections showing:
- Resolution method used (grounded search, database lookup, etc.)
- Source citations with clickable links
- Candidate values and outlier detection
- Statistical analysis of agreement between sources
- Timestamp of when data was resolved

## Implementation Details

### Files Added

- `confidence_ui.py`: Core UI components and data structures
- `test_confidence_ui.py`: Test script for verifying functionality
- `CONFIDENCE_UI_README.md`: This documentation

### Files Modified

- `app.py`: Integrated confidence indicators into results display

### Key Functions

#### `render_confidence_badge(confidence_info, size="normal")`
Renders a color-coded confidence badge with tooltip.

#### `render_warning_banner(warnings)`
Displays warning messages for low-confidence estimates.

#### `render_provenance_panel(provenance_info, expanded=False)`
Shows basic source information in an expandable panel.

#### `render_detailed_provenance_panel(field_name, provenance_info)`
Displays comprehensive source analysis with statistical summaries.

## Data Structures

### `ConfidenceInfo`
```python
@dataclass
class ConfidenceInfo:
    score: float      # 0.0 to 1.0
    level: str        # "high", "medium", "low"
    explanation: str  # Plain-English description
    warnings: List[str]
```

### `ProvenanceInfo`
```python
@dataclass
class ProvenanceInfo:
    method: str                    # Resolution method
    sources: List[str]             # Source URLs/names
    candidates: List[Dict]         # Candidate values
    final_value: float            # Selected value
    confidence: ConfidenceInfo    # Confidence details
    resolved_at: datetime         # When resolved
```

## Usage Examples

### Basic Confidence Badge
```python
confidence = create_mock_confidence_info(0.85, [])
badge_html = render_confidence_badge(confidence, size="small")
st.markdown(f"Curb Weight: 3600 lbs {badge_html}", unsafe_allow_html=True)
```

### Warning Banner
```python
warnings = ["Engine weight estimated from curb weight percentage"]
render_warning_banner(warnings)
```

### Provenance Panel
```python
provenance = create_mock_provenance_info("Curb Weight", 3600.0, 0.85)
render_detailed_provenance_panel("Curb Weight", provenance)
```

## Integration with Resolver System

When the resolver system is fully implemented, the mock data creation functions should be replaced with actual resolution results:

```python
# Instead of:
confidence = create_mock_confidence_info(0.85, [])

# Use:
resolution_result = resolver.resolve_field("curb_weight", year, make, model)
confidence = ConfidenceInfo(
    score=resolution_result.confidence_score,
    level=get_confidence_level(resolution_result.confidence_score),
    explanation=get_confidence_explanation(resolution_result.confidence_score),
    warnings=resolution_result.warnings
)
```

## Testing

Run the test script to verify all components work correctly:

```bash
streamlit run test_confidence_ui.py
```

## Requirements Addressed

This implementation addresses the following requirements from the spec:

- **1.2**: Display source citations next to each resolved field value
- **1.4**: Display confidence indicators using green/amber/red status
- **5.1**: Display the resolution method used for each field value
- **5.2**: Provide a provenance panel showing confidence scores and source lists
- **6.3**: Display prominent warning indicators when confidence is low

## Future Enhancements

1. **Real-time Updates**: Refresh confidence scores when new data becomes available
2. **User Feedback**: Allow users to report incorrect estimates to improve future confidence
3. **Historical Tracking**: Show confidence trends over time for specific vehicle models
4. **Custom Thresholds**: Allow administrators to adjust confidence level thresholds
5. **Export Functionality**: Include confidence scores in exported reports