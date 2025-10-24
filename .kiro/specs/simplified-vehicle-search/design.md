# Design Document - Simplified Vehicle Search

## Overview

The Simplified Vehicle Search feature adds a visual progress indicator below the existing search input to provide real-time feedback about what specifications are being searched and their current status. This design maintains the existing interface structure while adding transparency to the search process.

The design leverages the existing resolver system (GroundedSearchClient, ConsensusResolver, ProvenanceTracker) by adding a lightweight progress tracking layer that monitors and displays the search process without modifying the core functionality or result presentation.

## Architecture

### System Components

The progress tracking feature integrates with the existing architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                       │
├─────────────────────────────────────────────────────────────┤
│  Existing UI Components (Unchanged)                        │
│  ├── Search Input Field                                    │
│  ├── Results Display                                       │
│  ├── confidence_ui.py (render_confidence_badge, etc.)      │
│  └── render_detailed_provenance_panel                      │
├─────────────────────────────────────────────────────────────┤
│  New Progress Tracking Layer                               │
│  ├── Search Progress Tracker (New)                         │
│  ├── Progress Status Display (New)                         │
│  └── Real-time Update Handler (New)                        │
├─────────────────────────────────────────────────────────────┤
│  Business Logic Layer (Enhanced)                           │
│  ├── vehicle_data.py (process_vehicle + progress hooks)    │
│  ├── resolver.py (GroundedSearchClient, ConsensusResolver) │
│  └── app.py (cost calculation functions)                   │
├─────────────────────────────────────────────────────────────┤
│  Data Layer (Existing)                                     │
│  ├── PostgreSQL Database                                   │
│  ├── Resolution Cache (resolutions table)                  │
│  └── Vehicle Data Cache (vehicles table)                   │
└─────────────────────────────────────────────────────────────┘
```

### Design Patterns

**Minimal UI Addition**: Add progress tracking without modifying existing interface elements
**Real-time Feedback**: Live progress indicators during search operations
**Non-intrusive Integration**: Progress area appears only during active searches
**Status Transparency**: Clear visual communication of search progress and current activity

## Components and Interfaces

### 1. Search Progress Tracker Component

**Purpose**: Provides real-time feedback during vehicle specification resolution

**Interface**:
```python
class SearchProgressTracker:
    def __init__(self, specifications: List[str])
    def update_status(self, spec: str, status: SearchStatus)
    def render(self) -> None
    def clear(self) -> None
    
enum SearchStatus:
    SEARCHING = "🔍"
    FOUND = "✅" 
    PARTIAL = "⚠️"
    FAILED = "❌"
```

**Visual Design**:
- Compact horizontal list below the existing search input
- Each item shows: status icon + specification name
- Minimal vertical space usage (single line when possible)
- Auto-clears when search completes
- Example: `🔍 Weight  ✅ Engine Material  🔍 Catalytic Converters`

### 2. Progress Status Display Component

**Purpose**: Shows overall search progress and current phase

**Interface**:
```python
class ProgressStatusDisplay:
    def __init__(self, container: st.container)
    def update_phase(self, phase: str) -> None
    def update_completion(self, completed: int, total: int) -> None
    def show_completion_message(self) -> None
    def hide(self) -> None
```

**Visual Design**:
- Single line status message (e.g., "Searching specifications... (3 of 5 found)")
- Current phase indicator (e.g., "Resolving conflicts...", "Saving to database...")
- Minimal, non-intrusive text display
- Automatically hides when search completes

### 3. Progress Integration Hook

**Purpose**: Integrates progress tracking with existing resolver system

**Interface**:
```python
class ProgressIntegrationHook:
    def __init__(self, progress_tracker: SearchProgressTracker)
    def on_specification_start(self, spec_name: str) -> None
    def on_specification_complete(self, spec_name: str, status: SearchStatus) -> None
    def on_phase_change(self, phase: str) -> None
```

**Integration Points**:
- Hooks into existing resolver methods without modifying core logic
- Monitors GroundedSearchClient and ConsensusResolver progress
- Provides callbacks for UI updates during search process

## Data Models

### Search Progress Model

```python
@dataclass
class SearchProgress:
    vehicle_key: str
    specifications: Dict[str, SearchStatus]
    current_phase: str
    total_specifications: int
    completed_specifications: int
    start_time: datetime
    is_active: bool
    
    def get_progress_percentage(self) -> float:
        """Calculate completion percentage"""
        
    def get_status_summary(self) -> str:
        """Get human-readable progress summary"""
        
    def is_complete(self) -> bool:
        """Check if all specifications are processed"""
```

### Progress Event Model

```python
@dataclass
class ProgressEvent:
    event_type: str  # "spec_start", "spec_complete", "phase_change"
    specification: Optional[str]
    status: Optional[SearchStatus]
    phase: Optional[str]
    timestamp: datetime
    
    def to_ui_update(self) -> Dict[str, Any]:
        """Convert to UI update format"""
```

## Error Handling

### Progress Tracking Error Handling

1. **Search Timeout**: Show timeout indicator and allow user to continue or retry
2. **Specification Failure**: Mark individual specifications as failed (❌) while continuing others
3. **System Error**: Display error message and gracefully hide progress area
4. **Network Issues**: Show connection status and retry options

### Error Recovery Patterns

```python
class ProgressErrorHandler:
    def handle_specification_error(self, spec: str, error: Exception) -> None
    def handle_system_error(self, error: Exception) -> None
    def reset_progress_state(self) -> None
```

**Recovery Actions**:
- Mark failed specifications with appropriate status indicators
- Continue processing remaining specifications
- Provide clear error messaging without disrupting existing UI
- Allow manual retry of failed specifications

## Testing Strategy

### Unit Testing Focus Areas

1. **Progress Component Rendering**: Verify progress tracker displays correctly
2. **Status Updates**: Test real-time status update functionality
3. **State Management**: Validate progress state transitions and cleanup
4. **Error Handling**: Test error scenarios and recovery mechanisms

### Integration Testing Scenarios

1. **End-to-End Progress Flow**: Complete vehicle search with progress tracking
2. **Resolver Integration**: Progress hooks integration with existing resolver system
3. **UI Integration**: Progress area integration with existing interface
4. **Error Recovery**: Failed searches with progress error handling

### User Experience Testing

1. **Progress Clarity**: User understanding of search progress and status
2. **Non-intrusive Design**: Verify progress area doesn't disrupt existing workflow
3. **Performance Impact**: Measure any performance impact of progress tracking
4. **Visual Integration**: Ensure progress area matches existing design language

## Implementation Considerations

### Performance Optimizations

1. **Lightweight Updates**: Minimize DOM updates during progress tracking
2. **Debounced Rendering**: Prevent excessive re-renders during rapid status changes
3. **Memory Management**: Clean up progress state after search completion
4. **Minimal Overhead**: Ensure progress tracking doesn't impact search performance

### Accessibility Features

1. **Screen Reader Support**: Proper ARIA labels for progress indicators and status updates
2. **Live Regions**: Use ARIA live regions for real-time progress announcements
3. **High Contrast Mode**: Ensure progress indicators are visible in high contrast mode
4. **Keyboard Navigation**: Progress area should not interfere with existing keyboard navigation

### Mobile Considerations

1. **Responsive Design**: Progress area adapts to mobile screen sizes
2. **Touch Compatibility**: Progress indicators work well on touch devices
3. **Reduced Motion**: Respect user preferences for reduced motion
4. **Compact Display**: Optimize progress display for smaller screens

## Integration Points

### Existing System Integration

**Resolver System**: 
- Add progress hooks to existing GroundedSearchClient without modifying core logic
- Monitor ConsensusResolver progress through callback mechanisms
- Integrate with ProvenanceTracker to show resolution phases

**UI Components**:
- Insert progress area below existing search input field
- Maintain existing result display and confidence UI components unchanged
- Use existing CSS framework with minimal progress-specific additions

**Database Layer**:
- No changes required to existing database schema or operations
- Progress tracking operates in-memory during search process
- Maintain full compatibility with current caching mechanisms

### API Compatibility

The progress tracking feature maintains full compatibility with existing API endpoints and data structures. No breaking changes are introduced to the underlying system, ensuring existing functionality remains intact.

## Design Rationale

### Minimal UI Addition Approach
Adding only a progress area below the search input preserves the existing user experience while providing valuable transparency. This approach minimizes disruption to established workflows while addressing the need for search visibility.

### Real-Time Progress Feedback
Live progress indicators help users understand system activity and set appropriate expectations for completion time. This reduces perceived wait times and provides confidence that the system is actively working on their request.

### Non-Intrusive Integration
The progress area appears only during active searches and automatically clears when complete, ensuring it doesn't add permanent visual clutter to the interface. This maintains the clean, focused design of the existing system.

### Status Transparency Design
Clear visual indicators (icons + text) provide immediate understanding of what specifications are being searched and their current status, giving users insight into the search process without requiring technical knowledge of the underlying system.