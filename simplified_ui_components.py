"""
Simplified UI components for the Ruby GEM vehicle search interface.
Provides streamlined, user-friendly components with progressive disclosure and real-time feedback.
"""

import streamlit as st
import textwrap
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import time

# Import existing confidence UI components
from confidence_ui import ConfidenceInfo, ProvenanceInfo, render_confidence_badge, render_detailed_provenance_panel


class SearchStatus(Enum):
    """Status indicators for search progress tracking."""
    SEARCHING = "🔍"
    FOUND = "✅"
    PARTIAL = "⚠️"
    FAILED = "❌"


@dataclass
class SimplifiedVehicleSpec:
    """Streamlined vehicle specification data structure."""
    # Core specifications (always visible)
    curb_weight: Optional[float] = None
    catalytic_converters: Optional[int] = None
    engine_material: Optional[str] = None  # "Aluminum" or "Iron"
    rim_material: Optional[str] = None     # "Aluminum" or "Steel"
    
    # Confidence information
    confidence_scores: Dict[str, float] = None
    overall_confidence: float = 0.0
    
    # Detailed information (progressive disclosure)
    resolution_details: Dict[str, ProvenanceInfo] = None
    warnings: List[str] = None
    last_updated: Optional[datetime] = None
    
    # Vehicle identification
    year: Optional[int] = None
    make: Optional[str] = None
    model: Optional[str] = None
    
    def __post_init__(self):
        if self.confidence_scores is None:
            self.confidence_scores = {}
        if self.resolution_details is None:
            self.resolution_details = {}
        if self.warnings is None:
            self.warnings = []
        if self.last_updated is None:
            self.last_updated = datetime.now()
    
    def get_critical_specs(self) -> Dict[str, Any]:
        """Return only the specifications needed for immediate decisions."""
        return {
            "curb_weight": self.curb_weight,
            "catalytic_converters": self.catalytic_converters,
            "engine_material": self.engine_material,
            "rim_material": self.rim_material
        }
    
    def get_confidence_level(self, field: str) -> str:
        """Get confidence level for a specific field."""
        score = self.confidence_scores.get(field, 0.0)
        if score >= 0.8:
            return "high"
        elif score >= 0.6:
            return "medium"
        else:
            return "low"
    
    def calculate_overall_confidence(self) -> float:
        """Calculate overall confidence score from individual field scores."""
        if not self.confidence_scores:
            return 0.0
        
        # Weight critical specifications more heavily
        weights = {
            "curb_weight": 0.4,  # Most important for cost calculations
            "catalytic_converters": 0.3,  # Important for commodity calculations
            "engine_material": 0.15,  # Moderate importance
            "rim_material": 0.15   # Moderate importance
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for field, score in self.confidence_scores.items():
            weight = weights.get(field, 0.1)  # Default weight for unknown fields
            weighted_sum += score * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        self.overall_confidence = weighted_sum / total_weight
        return self.overall_confidence
    
    def get_field_display_name(self, field: str) -> str:
        """Get user-friendly display name for a field."""
        display_names = {
            "curb_weight": "Curb Weight",
            "catalytic_converters": "Catalytic Converters",
            "engine_material": "Engine Material",
            "rim_material": "Rim Material"
        }
        return display_names.get(field, field.replace("_", " ").title())
    
    def get_field_display_value(self, field: str) -> str:
        """Get formatted display value for a field."""
        value = getattr(self, field, None)
        if value is None:
            return "Unknown"
        
        if field == "curb_weight":
            return f"{value:,.0f} lbs"
        elif field == "catalytic_converters":
            return str(int(value))
        elif field in ["engine_material", "rim_material"]:
            return str(value)
        else:
            return str(value)
    
    def has_sufficient_data(self) -> bool:
        """Check if we have sufficient data for cost calculations."""
        return (self.curb_weight is not None and 
                self.curb_weight > 0 and
                self.overall_confidence >= 0.5)
    
    def get_data_quality_summary(self) -> Dict[str, Any]:
        """Get summary of data quality for this vehicle."""
        critical_fields = ["curb_weight", "catalytic_converters", "engine_material", "rim_material"]
        
        available_fields = sum(1 for field in critical_fields if getattr(self, field) is not None)
        high_confidence_fields = sum(1 for field in critical_fields 
                                   if self.confidence_scores.get(field, 0) >= 0.8)
        
        return {
            "available_fields": available_fields,
            "total_fields": len(critical_fields),
            "high_confidence_fields": high_confidence_fields,
            "overall_confidence": self.calculate_overall_confidence(),
            "has_warnings": len(self.warnings) > 0,
            "last_updated": self.last_updated
        }
    
    @classmethod
    def from_vehicle_data(cls, vehicle_data: Dict[str, Any], year: int = None, 
                         make: str = None, model: str = None) -> 'SimplifiedVehicleSpec':
        """Create SimplifiedVehicleSpec from vehicle_data dictionary."""
        spec = cls(
            year=year,
            make=make,
            model=model,
            curb_weight=vehicle_data.get('curb_weight_lbs'),
            catalytic_converters=vehicle_data.get('catalytic_converters'),
            engine_material="Aluminum" if vehicle_data.get('aluminum_engine') else "Iron" if vehicle_data.get('aluminum_engine') is False else None,
            rim_material="Aluminum" if vehicle_data.get('aluminum_rims') else "Steel" if vehicle_data.get('aluminum_rims') is False else None
        )
        
        # Set default confidence scores if not provided
        if not spec.confidence_scores:
            spec.confidence_scores = {}
            for field in ["curb_weight", "catalytic_converters", "engine_material", "rim_material"]:
                if getattr(spec, field) is not None:
                    spec.confidence_scores[field] = 0.7  # Default medium confidence
        
        spec.calculate_overall_confidence()
        return spec


@dataclass
@dataclass
class SearchProgress:
    """Search progress tracking data structure."""
    vehicle_key: str
    specifications: Dict[str, SearchStatus] = None
    current_step: str = ""
    total_steps: int = 0
    completed_steps: int = 0
    start_time: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    error_count: int = 0
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.specifications is None:
            self.specifications = {}
        if self.start_time is None:
            self.start_time = datetime.now()
        if self.warnings is None:
            self.warnings = []
    
    def get_progress_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total_steps == 0:
            return 0.0
        return (self.completed_steps / self.total_steps) * 100
    
    def get_next_specification(self) -> Optional[str]:
        """Get next specification to process."""
        for spec, status in self.specifications.items():
            if status == SearchStatus.SEARCHING:
                return spec
        return None
    
    def update_specification_status(self, spec: str, status: SearchStatus) -> None:
        """Update the status of a specification and adjust counters."""
        if spec not in self.specifications:
            return
        
        old_status = self.specifications[spec]
        self.specifications[spec] = status
        
        # Update completed steps counter
        if old_status == SearchStatus.SEARCHING and status != SearchStatus.SEARCHING:
            self.completed_steps += 1
        elif old_status != SearchStatus.SEARCHING and status == SearchStatus.SEARCHING:
            self.completed_steps = max(0, self.completed_steps - 1)
        
        # Update error count
        if status == SearchStatus.FAILED:
            self.error_count += 1
        elif old_status == SearchStatus.FAILED and status != SearchStatus.FAILED:
            self.error_count = max(0, self.error_count - 1)
        
        # Update current step
        if status == SearchStatus.SEARCHING:
            self.current_step = f"Searching for {spec.replace('_', ' ')}"
        elif self.get_next_specification():
            next_spec = self.get_next_specification()
            self.current_step = f"Searching for {next_spec.replace('_', ' ')}"
        else:
            self.current_step = "Finalizing results"
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds since search started."""
        if self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return 0.0
    
    def estimate_remaining_time(self) -> Optional[float]:
        """Estimate remaining time based on current progress."""
        if self.completed_steps == 0 or self.total_steps == 0:
            return None
        
        elapsed = self.get_elapsed_time()
        progress_ratio = self.completed_steps / self.total_steps
        
        if progress_ratio > 0:
            estimated_total = elapsed / progress_ratio
            remaining = estimated_total - elapsed
            return max(0, remaining)
        
        return None
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get summary of search progress status."""
        status_counts = {}
        for status in SearchStatus:
            status_counts[status.name.lower()] = sum(1 for s in self.specifications.values() if s == status)
        
        return {
            "total_specifications": len(self.specifications),
            "completed_steps": self.completed_steps,
            "total_steps": self.total_steps,
            "progress_percentage": self.get_progress_percentage(),
            "elapsed_time": self.get_elapsed_time(),
            "estimated_remaining": self.estimate_remaining_time(),
            "error_count": self.error_count,
            "warning_count": len(self.warnings),
            "status_counts": status_counts,
            "is_complete": self.completed_steps >= self.total_steps,
            "has_errors": self.error_count > 0
        }
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message to the search progress."""
        if warning not in self.warnings:
            self.warnings.append(warning)
    
    def is_search_complete(self) -> bool:
        """Check if the search is complete (all specifications processed)."""
        return all(status != SearchStatus.SEARCHING for status in self.specifications.values())
    
    def get_successful_specifications(self) -> List[str]:
        """Get list of specifications that were successfully found."""
        return [spec for spec, status in self.specifications.items() 
                if status in [SearchStatus.FOUND, SearchStatus.PARTIAL]]
    
    def get_failed_specifications(self) -> List[str]:
        """Get list of specifications that failed to resolve."""
        return [spec for spec, status in self.specifications.items() 
                if status == SearchStatus.FAILED]


class SearchProgressTracker:
    """Component for real-time search progress feedback with enhanced status indicators."""
    
    def __init__(self, specifications: List[str]):
        self.specifications = specifications
        self.progress = SearchProgress(
            vehicle_key="",
            specifications={spec: SearchStatus.SEARCHING for spec in specifications},
            total_steps=len(specifications) + 1  # +1 for database step
        )
        self.container = None
        self.current_phase = "Initializing search..."
        self.timeout_warnings = {}
        self.error_messages = {}
        self.low_confidence_warnings = {}
        self.spec_start_times = {}
        self.timeout_threshold = 30  # seconds
        self.api_calls_used = 0
        self.overall_confidence = 0.0
    
    def update_status(self, spec: str, status: SearchStatus, confidence: float = None, error_message: str = None) -> None:
        """Update the status of a specific specification with enhanced feedback."""
        if spec in self.progress.specifications:
            old_status = self.progress.specifications[spec]
            self.progress.specifications[spec] = status
            
            # Handle timing
            if old_status != SearchStatus.SEARCHING and status == SearchStatus.SEARCHING:
                self.start_spec_timer(spec)
            elif old_status == SearchStatus.SEARCHING and status != SearchStatus.SEARCHING:
                self.complete_spec_timer(spec)
                self.progress.completed_steps += 1
            
            # Handle error messages
            if error_message:
                self.error_messages[spec] = error_message
            elif spec in self.error_messages:
                del self.error_messages[spec]
            
            # Handle low confidence warnings
            if confidence is not None and confidence < 0.6:
                self.low_confidence_warnings[spec] = f"Low confidence result ({confidence:.0%})"
            elif spec in self.low_confidence_warnings:
                del self.low_confidence_warnings[spec]
            
            # Check for timeouts
            self.check_timeouts()
            
            # Update current phase
            self._update_current_phase()
            self.render()
    
    def set_phase(self, phase: str) -> None:
        """Set the current search phase."""
        self.current_phase = phase
        self.render()
    
    def set_api_call_count(self, count: int) -> None:
        """Set the total API calls used."""
        self.api_calls_used = count
        self.render()
    
    def set_overall_confidence(self, confidence: float) -> None:
        """Set the overall confidence score."""
        self.overall_confidence = confidence
        self.render()
    
    def add_timeout_warning(self, spec: str, timeout_seconds: int) -> None:
        """Add a timeout warning for a specification."""
        self.timeout_warnings[spec] = f"Search taking longer than expected ({timeout_seconds}s)"
        self.render()
    
    def clear_timeout_warning(self, spec: str) -> None:
        """Clear timeout warning for a specification."""
        if spec in self.timeout_warnings:
            del self.timeout_warnings[spec]
            self.render()
    
    def start_spec_timer(self, spec: str) -> None:
        """Start timing a specification search."""
        self.spec_start_times[spec] = time.time()
    
    def check_timeouts(self) -> None:
        """Check for specifications that have exceeded timeout threshold."""
        try:
            current_time = time.time()
            for spec, start_time in self.spec_start_times.items():
                if spec in self.progress.specifications and self.progress.specifications[spec] == SearchStatus.SEARCHING:
                    elapsed = current_time - start_time
                    if elapsed > self.timeout_threshold and spec not in self.timeout_warnings:
                        self.add_timeout_warning(spec, int(elapsed))
        except Exception as e:
            # Silently handle any threading context issues
            pass
    
    def complete_spec_timer(self, spec: str) -> None:
        """Complete timing for a specification."""
        if spec in self.spec_start_times:
            del self.spec_start_times[spec]
        self.clear_timeout_warning(spec)
    
    def get_retry_requests(self) -> List[str]:
        """Get list of specifications that have been requested for retry."""
        retry_specs = []
        for spec in self.specifications:
            if st.session_state.get(f'retry_spec_{spec}', False):
                retry_specs.append(spec)
                # Clear the retry flag
                st.session_state[f'retry_spec_{spec}'] = False
        return retry_specs
    
    def reset_spec_for_retry(self, spec: str) -> None:
        """Reset a specification for retry."""
        if spec in self.progress.specifications:
            self.progress.specifications[spec] = SearchStatus.SEARCHING
            if spec in self.error_messages:
                del self.error_messages[spec]
            if spec in self.timeout_warnings:
                del self.timeout_warnings[spec]
            if spec in self.low_confidence_warnings:
                del self.low_confidence_warnings[spec]
            self.start_spec_timer(spec)
            self._update_current_phase()
            self.render()
    
    def _update_current_phase(self) -> None:
        """Update the current phase based on progress state."""
        searching_specs = [spec for spec, status in self.progress.specifications.items() 
                          if status == SearchStatus.SEARCHING]
        
        if searching_specs:
            spec_name = searching_specs[0].replace("_", " ").title()
            self.current_phase = f"Searching for {spec_name}..."
        elif all(status != SearchStatus.SEARCHING for status in self.progress.specifications.values()):
            self.current_phase = "Saving to database..."
        else:
            self.current_phase = "Processing results..."
    
    def get_progress_completion(self) -> str:
        """Get progress completion indicator text."""
        total_specs = len(self.progress.specifications)
        completed_specs = sum(1 for status in self.progress.specifications.values() 
                            if status != SearchStatus.SEARCHING)
        return f"{completed_specs} of {total_specs} specifications found"
    
    def render(self) -> None:
        """Render the enhanced progress tracker component."""
        if self.container is None:
            self.container = st.empty()
        
        with self.container.container():
            # Header with progress completion
            progress_completion = self.get_progress_completion()
            current_phase = self.current_phase
            
            # Build HTML as a single string
            html_parts = []
            html_parts.append(f'''<div style="background: rgba(248, 250, 252, 0.95); border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);">''')
            html_parts.append(f'''<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">''')
            html_parts.append(f'''<div style="font-weight: 600; color: #334155;">🔍 Search Progress</div>''')
            html_parts.append(f'''<div style="font-size: 0.875rem; color: #64748b; font-weight: 500;">{progress_completion}</div>''')
            html_parts.append(f'''</div>''')
            html_parts.append(f'''<div style="font-size: 0.875rem; color: #475569; margin-bottom: 0.75rem; font-style: italic;">{current_phase}</div>''')
            
            # Show API calls and confidence if available
            if self.api_calls_used > 0 or self.overall_confidence > 0:
                html_parts.append(f'''<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; padding: 0.5rem; background: rgba(34, 197, 94, 0.1); border-radius: 4px;">''')
                if self.api_calls_used > 0:
                    html_parts.append(f'''<div style="font-size: 0.875rem; color: #16a34a; font-weight: 500;">📡 API Calls: {self.api_calls_used}</div>''')
                if self.overall_confidence > 0:
                    confidence_color = "#16a34a" if self.overall_confidence >= 0.8 else "#d97706" if self.overall_confidence >= 0.6 else "#dc2626"
                    html_parts.append(f'''<div style="font-size: 0.875rem; color: {confidence_color}; font-weight: 500;">🎯 Confidence: {self.overall_confidence:.0%}</div>''')
                html_parts.append(f'''</div>''')
            
            # Create enhanced progress items
            for spec, status in self.progress.specifications.items():
                status_icon = status.value
                spec_display = spec.replace("_", " ").title()
                
                # Color coding based on status
                if status == SearchStatus.FOUND:
                    color = "#16a34a"
                    bg_color = "rgba(22, 163, 74, 0.1)"
                elif status == SearchStatus.PARTIAL:
                    color = "#d97706"
                    bg_color = "rgba(217, 119, 6, 0.1)"
                elif status == SearchStatus.FAILED:
                    color = "#dc2626"
                    bg_color = "rgba(220, 38, 38, 0.1)"
                else:  # SEARCHING
                    color = "#6b7280"
                    bg_color = "rgba(107, 114, 128, 0.1)"
                
                # Add timeout indicator if present
                timeout_indicator = ""
                if spec in self.timeout_warnings:
                    timeout_indicator = " ⏱️"
                
                # Add low confidence warning if present
                confidence_indicator = ""
                if spec in self.low_confidence_warnings:
                    confidence_indicator = " ⚠️"
                
                html_parts.append(f'''<div style="display: inline-block; margin: 0.25rem 0.5rem 0.25rem 0; padding: 0.5rem 0.75rem; background: {bg_color}; border: 1px solid {color}; border-radius: 6px; font-size: 0.875rem; color: {color}; font-weight: 500;">{status_icon} {spec_display}{timeout_indicator}{confidence_indicator}</div>''')
            
            # Add database step if all specs are complete
            all_complete = all(status != SearchStatus.SEARCHING for status in self.progress.specifications.values())
            if all_complete:
                html_parts.append(f'''<div style="display: inline-block; margin: 0.25rem 0.5rem 0.25rem 0; padding: 0.5rem 0.75rem; background: rgba(22, 163, 74, 0.1); border: 1px solid #16a34a; border-radius: 6px; font-size: 0.875rem; color: #16a34a; font-weight: 500;">✅ Saving to Database</div>''')
            
            # Show error messages if any
            if self.error_messages:
                html_parts.append(f'''<div style="margin-top: 0.75rem; padding: 0.5rem; background: rgba(220, 38, 38, 0.1); border: 1px solid #dc2626; border-radius: 4px; font-size: 0.875rem;">''')
                html_parts.append(f'''<div style="font-weight: 600; color: #dc2626; margin-bottom: 0.25rem;">⚠️ Issues Found:</div>''')
                for spec, error in self.error_messages.items():
                    spec_display = spec.replace("_", " ").title()
                    html_parts.append(f'''<div style="color: #dc2626; margin-left: 1rem;">• {spec_display}: {error}</div>''')
                html_parts.append(f'''</div>''')
            
            # Show timeout warnings if any
            if self.timeout_warnings:
                html_parts.append(f'''<div style="margin-top: 0.5rem; padding: 0.5rem; background: rgba(217, 119, 6, 0.1); border: 1px solid #d97706; border-radius: 4px; font-size: 0.875rem;">''')
                html_parts.append(f'''<div style="font-weight: 600; color: #d97706; margin-bottom: 0.25rem;">⏱️ Timeout Warnings:</div>''')
                for spec, warning in self.timeout_warnings.items():
                    spec_display = spec.replace("_", " ").title()
                    html_parts.append(f'''<div style="color: #d97706; margin-left: 1rem;">• {spec_display}: {warning}</div>''')
                html_parts.append(f'''</div>''')
            
            # Show low confidence warnings if any
            if self.low_confidence_warnings:
                html_parts.append(f'''<div style="margin-top: 0.5rem; padding: 0.5rem; background: rgba(217, 119, 6, 0.1); border: 1px solid #d97706; border-radius: 4px; font-size: 0.875rem;">''')
                html_parts.append(f'''<div style="font-weight: 600; color: #d97706; margin-bottom: 0.25rem;">⚠️ Low Confidence Results:</div>''')
                for spec, warning in self.low_confidence_warnings.items():
                    spec_display = spec.replace("_", " ").title()
                    html_parts.append(f'''<div style="color: #d97706; margin-left: 1rem;">• {spec_display}: {warning}</div>''')
                html_parts.append(f'''</div>''')
            
            # Close the main container
            html_parts.append('</div>')
            
            # Render all HTML in one call
            st.markdown(''.join(html_parts), unsafe_allow_html=True)
            
            # Show retry options for failed specifications (separate from HTML to allow buttons)
            failed_specs = [spec for spec, status in self.progress.specifications.items() 
                          if status == SearchStatus.FAILED]
            
            if failed_specs:
                st.markdown('<div style="margin-top: 0.75rem; padding: 0.5rem; background: rgba(239, 246, 255, 0.8); border: 1px solid #3b82f6; border-radius: 4px; font-size: 0.875rem;"><div style="font-weight: 600; color: #1e40af; margin-bottom: 0.5rem;">🔄 Retry Options:</div></div>', unsafe_allow_html=True)
                
                # Create retry buttons for each failed specification
                cols = st.columns(len(failed_specs))
                for i, spec in enumerate(failed_specs):
                    with cols[i]:
                        spec_display = spec.replace("_", " ").title()
                        # Create a unique key using timestamp and spec name
                        unique_key = f"retry_{spec}_{int(time.time() * 1000)}_{i}"
                        if st.button(f"Retry {spec_display}", key=unique_key, 
                                   help=f"Retry searching for {spec_display}"):
                            # Reset the specification to searching status
                            self.progress.specifications[spec] = SearchStatus.SEARCHING
                            if spec in self.error_messages:
                                del self.error_messages[spec]
                            if spec in self.timeout_warnings:
                                del self.timeout_warnings[spec]
                            self._update_current_phase()
                            # Return the spec name so the caller can retry the search
                            st.session_state[f'retry_spec_{spec}'] = True
                            st.rerun()
    
    def add_error_recovery_options(self, spec: str, error_type: str) -> None:
        """Add error recovery options for a failed specification."""
        recovery_options = {
            "timeout": "Search timed out - try again with extended timeout",
            "api_error": "API error occurred - retry with different approach",
            "validation_failed": "Data validation failed - manual review needed",
            "no_data": "No data found - try alternative sources",
            "low_confidence": "Low confidence result - verify manually"
        }
        
        if error_type in recovery_options:
            self.error_messages[spec] = recovery_options[error_type]
        else:
            self.error_messages[spec] = f"Unknown error ({error_type}) - retry recommended"
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors and warnings."""
        return {
            "error_count": len(self.error_messages),
            "timeout_count": len(self.timeout_warnings),
            "low_confidence_count": len(self.low_confidence_warnings),
            "failed_specs": [spec for spec, status in self.progress.specifications.items() 
                           if status == SearchStatus.FAILED],
            "partial_specs": [spec for spec, status in self.progress.specifications.items() 
                            if status == SearchStatus.PARTIAL],
            "has_issues": len(self.error_messages) > 0 or len(self.timeout_warnings) > 0 or len(self.low_confidence_warnings) > 0
        }
    
    def clear_all_errors(self) -> None:
        """Clear all error messages and warnings."""
        self.error_messages.clear()
        self.timeout_warnings.clear()
        self.low_confidence_warnings.clear()
        self.render()


class ConfidenceCard:
    """Component for organized specification display with confidence indicators."""
    
    def __init__(self, title: str, specifications: Dict[str, Any]):
        self.title = title
        self.specifications = specifications
        self.session_key = f"card_{title.lower().replace(' ', '_')}"
    
    def render(self, show_details: bool = False) -> None:
        """Render the confidence card component."""
        overall_confidence = self.get_overall_confidence()
        
        # Card styling based on overall confidence
        if overall_confidence >= 0.8:
            border_color = "#16a34a"
            bg_color = "rgba(22, 163, 74, 0.05)"
        elif overall_confidence >= 0.6:
            border_color = "#d97706"
            bg_color = "rgba(217, 119, 6, 0.05)"
        else:
            border_color = "#dc2626"
            bg_color = "rgba(220, 38, 38, 0.05)"
        
        st.markdown(f"""
        <div style="
            background: {bg_color};
            border: 2px solid {border_color};
            border-radius: 12px;
            padding: 1rem;
            margin: 0.5rem 0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        ">
            <div style="
                font-size: 1.1rem;
                font-weight: 600;
                color: {border_color};
                margin-bottom: 0.75rem;
                display: flex;
                align-items: center;
                justify-content: space-between;
            ">
                <span>🚗 {self.title}</span>
                <span style="font-size: 0.875rem;">
                    Overall: {overall_confidence:.0%}
                </span>
            </div>
        """, unsafe_allow_html=True)
        
        # Display specifications
        for spec_name, spec_data in self.specifications.items():
            value = spec_data.get("value", "Unknown")
            confidence = spec_data.get("confidence", 0.0)
            
            # Confidence indicator
            if confidence >= 0.8:
                indicator = "✅"
                conf_color = "#16a34a"
            elif confidence >= 0.6:
                indicator = "⚠️"
                conf_color = "#d97706"
            else:
                indicator = "❌"
                conf_color = "#dc2626"
            
            st.markdown(f"""
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0.5rem 0;
                border-bottom: 1px solid rgba(0, 0, 0, 0.1);
            ">
                <span style="font-weight: 500;">{spec_name}:</span>
                <span style="color: {conf_color};">
                    {value} {indicator}
                </span>
            </div>
            """, unsafe_allow_html=True)
        
        # Toggle button for details
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("View Details" if not show_details else "Hide Details", 
                        key=f"{self.session_key}_toggle"):
                st.session_state[f"{self.session_key}_expanded"] = not st.session_state.get(f"{self.session_key}_expanded", False)
        
        # Show detailed information if expanded
        if st.session_state.get(f"{self.session_key}_expanded", False):
            self._render_detailed_view()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    def get_overall_confidence(self) -> float:
        """Calculate overall confidence level for the card."""
        if not self.specifications:
            return 0.0
        
        confidences = [spec.get("confidence", 0.0) for spec in self.specifications.values()]
        return sum(confidences) / len(confidences)
    
    def _render_detailed_view(self) -> None:
        """Render the detailed view with provenance information."""
        st.markdown("""
        <div style="
            background: rgba(248, 250, 252, 0.8);
            border-radius: 6px;
            padding: 0.75rem;
            margin-top: 0.5rem;
        ">
            <div style="font-weight: 600; margin-bottom: 0.5rem; color: #475569;">
                📋 Detailed Information
            </div>
        """, unsafe_allow_html=True)
        
        for spec_name, spec_data in self.specifications.items():
            provenance = spec_data.get("provenance")
            if provenance:
                render_detailed_provenance_panel(spec_name, provenance)
        
        st.markdown("</div>", unsafe_allow_html=True)


class ProgressiveDisclosureManager:
    """Manager for expandable sections and progressive disclosure."""
    
    def __init__(self, session_key: str):
        self.session_key = session_key
        self._init_session_state()
    
    def _init_session_state(self) -> None:
        """Initialize session state for expansion tracking."""
        if f"{self.session_key}_sections" not in st.session_state:
            st.session_state[f"{self.session_key}_sections"] = {}
        if f"{self.session_key}_preferences" not in st.session_state:
            st.session_state[f"{self.session_key}_preferences"] = {
                "auto_expand_high_confidence": True,
                "auto_collapse_low_confidence": False,
                "remember_user_preferences": True
            }
    
    def is_expanded(self, section: str) -> bool:
        """Check if a section is currently expanded."""
        sections = st.session_state.get(f"{self.session_key}_sections", {})
        return sections.get(section, False)
    
    def toggle_section(self, section: str) -> None:
        """Toggle the expansion state of a section."""
        sections = st.session_state.get(f"{self.session_key}_sections", {})
        sections[section] = not sections.get(section, False)
        st.session_state[f"{self.session_key}_sections"] = sections
        
        # Update user preferences if enabled
        preferences = st.session_state.get(f"{self.session_key}_preferences", {})
        if preferences.get("remember_user_preferences", True):
            if f"{self.session_key}_user_expansions" not in st.session_state:
                st.session_state[f"{self.session_key}_user_expansions"] = {}
            st.session_state[f"{self.session_key}_user_expansions"][section] = sections[section]
    
    def set_section_state(self, section: str, expanded: bool) -> None:
        """Programmatically set the expansion state of a section."""
        sections = st.session_state.get(f"{self.session_key}_sections", {})
        sections[section] = expanded
        st.session_state[f"{self.session_key}_sections"] = sections
    
    def expand_all_sections(self) -> None:
        """Expand all tracked sections."""
        sections = st.session_state.get(f"{self.session_key}_sections", {})
        for section in sections:
            sections[section] = True
        st.session_state[f"{self.session_key}_sections"] = sections
    
    def collapse_all_sections(self) -> None:
        """Collapse all tracked sections."""
        sections = st.session_state.get(f"{self.session_key}_sections", {})
        for section in sections:
            sections[section] = False
        st.session_state[f"{self.session_key}_sections"] = sections
    
    def auto_manage_section(self, section: str, confidence_score: float) -> None:
        """Automatically manage section expansion based on confidence score."""
        preferences = st.session_state.get(f"{self.session_key}_preferences", {})
        
        # Check if user has manually interacted with this section
        user_expansions = st.session_state.get(f"{self.session_key}_user_expansions", {})
        if section in user_expansions:
            # Respect user preference
            self.set_section_state(section, user_expansions[section])
            return
        
        # Auto-manage based on confidence
        if preferences.get("auto_expand_high_confidence", True) and confidence_score >= 0.8:
            self.set_section_state(section, True)
        elif preferences.get("auto_collapse_low_confidence", False) and confidence_score < 0.5:
            self.set_section_state(section, False)
    
    def render_toggle_button(self, section: str, label: str, confidence_score: float = None) -> bool:
        """Render a toggle button and return whether it was clicked."""
        # Auto-manage section if confidence score provided
        if confidence_score is not None:
            self.auto_manage_section(section, confidence_score)
        
        is_expanded = self.is_expanded(section)
        
        # Add confidence indicator to button if provided
        confidence_indicator = ""
        if confidence_score is not None:
            if confidence_score >= 0.8:
                confidence_indicator = " ✅"
            elif confidence_score >= 0.6:
                confidence_indicator = " ⚠️"
            else:
                confidence_indicator = " ❌"
        
        button_text = f"▼ {label}{confidence_indicator}" if is_expanded else f"▶ {label}{confidence_indicator}"
        
        if st.button(button_text, key=f"{self.session_key}_{section}_toggle"):
            self.toggle_section(section)
            return True
        return False
    
    def render_expandable_section(self, section: str, title: str, content_func: Callable, 
                                confidence_score: float = None) -> None:
        """Render an expandable section with toggle control."""
        if self.render_toggle_button(section, title, confidence_score):
            st.rerun()
        
        if self.is_expanded(section):
            with st.container():
                content_func()
    
    def get_expansion_summary(self) -> Dict[str, Any]:
        """Get summary of current expansion states."""
        sections = st.session_state.get(f"{self.session_key}_sections", {})
        user_expansions = st.session_state.get(f"{self.session_key}_user_expansions", {})
        preferences = st.session_state.get(f"{self.session_key}_preferences", {})
        
        return {
            "total_sections": len(sections),
            "expanded_sections": sum(1 for expanded in sections.values() if expanded),
            "user_managed_sections": len(user_expansions),
            "auto_managed_sections": len(sections) - len(user_expansions),
            "preferences": preferences,
            "sections": sections
        }
    
    def reset_user_preferences(self) -> None:
        """Reset all user preferences and expansions."""
        if f"{self.session_key}_user_expansions" in st.session_state:
            del st.session_state[f"{self.session_key}_user_expansions"]
        
        # Reset to default preferences
        st.session_state[f"{self.session_key}_preferences"] = {
            "auto_expand_high_confidence": True,
            "auto_collapse_low_confidence": False,
            "remember_user_preferences": True
        }


class RealTimeStatus:
    """Component for managing live updates during search operations."""
    
    def __init__(self, container: st.container):
        self.container = container
        self.current_status = ""
        self.progress_tracker = None
        self.start_time = None
    
    def start_search(self, vehicle: str) -> None:
        """Initialize search status tracking."""
        self.start_time = datetime.now()
        self.current_status = f"Starting search for {vehicle}..."
        
        # Initialize progress tracker with common vehicle specifications
        specifications = [
            "curb_weight",
            "engine_material", 
            "rim_material",
            "catalytic_converters"
        ]
        
        self.progress_tracker = SearchProgressTracker(specifications)
        self._update_display()
    
    def update_progress(self, step: str, status: str) -> None:
        """Update progress for a specific step."""
        self.current_status = f"{step}: {status}"
        
        if self.progress_tracker and step in self.progress_tracker.progress.specifications:
            # Map status strings to SearchStatus enum
            status_mapping = {
                "searching": SearchStatus.SEARCHING,
                "found": SearchStatus.FOUND,
                "partial": SearchStatus.PARTIAL,
                "failed": SearchStatus.FAILED
            }
            
            search_status = status_mapping.get(status.lower(), SearchStatus.SEARCHING)
            self.progress_tracker.update_status(step, search_status)
        
        self._update_display()
    
    def complete_search(self, results: Dict[str, Any]) -> None:
        """Complete the search and show final results."""
        self.current_status = "Search completed successfully!"
        
        # Update all remaining specifications to found/failed based on results
        if self.progress_tracker:
            for spec in self.progress_tracker.progress.specifications:
                if spec in results and results[spec] is not None:
                    self.progress_tracker.update_status(spec, SearchStatus.FOUND)
                else:
                    self.progress_tracker.update_status(spec, SearchStatus.FAILED)
        
        self._update_display()
        
        # Show completion message
        elapsed_time = datetime.now() - self.start_time if self.start_time else None
        if elapsed_time:
            st.success(f"✅ Search completed in {elapsed_time.total_seconds():.1f} seconds")
    
    def _update_display(self) -> None:
        """Update the display with current status."""
        with self.container:
            if self.progress_tracker:
                self.progress_tracker.render()
            
            if self.current_status:
                st.markdown(f"""
                <div style="
                    background: rgba(59, 130, 246, 0.1);
                    border: 1px solid #3b82f6;
                    border-radius: 6px;
                    padding: 0.5rem;
                    margin: 0.25rem 0;
                    font-size: 0.875rem;
                    color: #1e40af;
                ">
                    {self.current_status}
                </div>
                """, unsafe_allow_html=True)


# Integration utilities for connecting with existing systems
def convert_vehicle_data_to_simplified_spec(
    vehicle_data: Dict[str, Any],
    year: int,
    make: str,
    model: str,
    resolution_data: Dict[str, Any] = None
) -> SimplifiedVehicleSpec:
    """Convert existing vehicle_data format to SimplifiedVehicleSpec."""
    spec = SimplifiedVehicleSpec.from_vehicle_data(vehicle_data, year, make, model)
    
    # Add resolution data if available
    if resolution_data:
        for field_name, field_data in resolution_data.items():
            confidence = field_data.get('confidence', 0.7)
            spec.confidence_scores[field_name] = confidence
    
    spec.calculate_overall_confidence()
    return spec


def update_search_progress_from_resolver(
    progress: SearchProgress,
    field_name: str,
    resolution_result: Any,
    success: bool = True
) -> None:
    """Update search progress based on resolver results."""
    if success and resolution_result is not None:
        # Determine status based on confidence if available
        if hasattr(resolution_result, 'confidence_score'):
            if resolution_result.confidence_score >= 0.8:
                status = SearchStatus.FOUND
            elif resolution_result.confidence_score >= 0.5:
                status = SearchStatus.PARTIAL
            else:
                status = SearchStatus.FAILED
        else:
            status = SearchStatus.FOUND
        
        # Add warnings if available
        if hasattr(resolution_result, 'warnings') and resolution_result.warnings:
            for warning in resolution_result.warnings:
                progress.add_warning(f"{field_name}: {warning}")
    else:
        status = SearchStatus.FAILED
        progress.add_warning(f"Failed to resolve {field_name}")
    
    progress.update_specification_status(field_name, status)


def create_confidence_summary_for_display(vehicle_spec: SimplifiedVehicleSpec) -> Dict[str, Any]:
    """Create a confidence summary optimized for UI display."""
    summary = ConfidenceAggregator.generate_confidence_summary(vehicle_spec)
    
    # Add display-friendly information
    summary["display_info"] = {
        "overall_confidence_text": f"{summary['overall_confidence']:.0%}",
        "quality_grade_color": {
            "A+": "#16a34a", "A": "#16a34a", "B": "#d97706", 
            "C": "#d97706", "D": "#dc2626", "F": "#dc2626"
        }.get(summary["quality_grade"], "#6b7280"),
        "needs_attention": summary["needs_review"],
        "completion_status": "Complete" if summary["data_completeness"] == 100 else f"{summary['data_completeness']:.0f}% Complete"
    }
    
    return summary


# Confidence score aggregation and analysis functions
class ConfidenceAggregator:
    """Utility class for aggregating and analyzing confidence scores."""
    
    @staticmethod
    def calculate_weighted_average(scores: Dict[str, float], weights: Dict[str, float] = None) -> float:
        """Calculate weighted average of confidence scores."""
        if not scores:
            return 0.0
        
        if weights is None:
            # Default weights for vehicle specifications
            weights = {
                "curb_weight": 0.4,
                "catalytic_converters": 0.3,
                "engine_material": 0.15,
                "rim_material": 0.15
            }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for field, score in scores.items():
            weight = weights.get(field, 0.1)  # Default weight for unknown fields
            weighted_sum += score * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    @staticmethod
    def get_confidence_distribution(scores: Dict[str, float]) -> Dict[str, int]:
        """Get distribution of confidence levels."""
        distribution = {"high": 0, "medium": 0, "low": 0}
        
        for score in scores.values():
            if score >= 0.8:
                distribution["high"] += 1
            elif score >= 0.6:
                distribution["medium"] += 1
            else:
                distribution["low"] += 1
        
        return distribution
    
    @staticmethod
    def identify_low_confidence_fields(scores: Dict[str, float], threshold: float = 0.6) -> List[str]:
        """Identify fields with confidence below threshold."""
        return [field for field, score in scores.items() if score < threshold]
    
    @staticmethod
    def calculate_data_completeness(vehicle_spec: SimplifiedVehicleSpec) -> float:
        """Calculate data completeness percentage."""
        critical_fields = ["curb_weight", "catalytic_converters", "engine_material", "rim_material"]
        available_fields = sum(1 for field in critical_fields if getattr(vehicle_spec, field) is not None)
        return (available_fields / len(critical_fields)) * 100
    
    @staticmethod
    def generate_confidence_summary(vehicle_spec: SimplifiedVehicleSpec) -> Dict[str, Any]:
        """Generate comprehensive confidence summary."""
        scores = vehicle_spec.confidence_scores
        distribution = ConfidenceAggregator.get_confidence_distribution(scores)
        low_confidence_fields = ConfidenceAggregator.identify_low_confidence_fields(scores)
        
        return {
            "overall_confidence": vehicle_spec.calculate_overall_confidence(),
            "confidence_distribution": distribution,
            "low_confidence_fields": low_confidence_fields,
            "data_completeness": ConfidenceAggregator.calculate_data_completeness(vehicle_spec),
            "field_count": len(scores),
            "needs_review": len(low_confidence_fields) > 0 or vehicle_spec.overall_confidence < 0.6,
            "quality_grade": ConfidenceAggregator.get_quality_grade(vehicle_spec.overall_confidence)
        }
    
    @staticmethod
    def get_quality_grade(confidence_score: float) -> str:
        """Get quality grade based on confidence score."""
        if confidence_score >= 0.9:
            return "A+"
        elif confidence_score >= 0.8:
            return "A"
        elif confidence_score >= 0.7:
            return "B"
        elif confidence_score >= 0.6:
            return "C"
        elif confidence_score >= 0.5:
            return "D"
        else:
            return "F"


# Session state management utilities
class SessionStateManager:
    """Utility class for managing session state across the application."""
    
    @staticmethod
    def initialize_vehicle_session(vehicle_key: str) -> None:
        """Initialize session state for a specific vehicle."""
        if f"vehicle_{vehicle_key}" not in st.session_state:
            st.session_state[f"vehicle_{vehicle_key}"] = {
                "search_progress": None,
                "vehicle_spec": None,
                "last_search_time": None,
                "search_history": [],
                "user_preferences": {
                    "auto_expand_details": True,
                    "show_confidence_badges": True,
                    "highlight_low_confidence": True
                }
            }
    
    @staticmethod
    def get_vehicle_session(vehicle_key: str) -> Dict[str, Any]:
        """Get session data for a specific vehicle."""
        SessionStateManager.initialize_vehicle_session(vehicle_key)
        return st.session_state[f"vehicle_{vehicle_key}"]
    
    @staticmethod
    def update_vehicle_session(vehicle_key: str, data: Dict[str, Any]) -> None:
        """Update session data for a specific vehicle."""
        session_data = SessionStateManager.get_vehicle_session(vehicle_key)
        session_data.update(data)
        st.session_state[f"vehicle_{vehicle_key}"] = session_data
    
    @staticmethod
    def clear_vehicle_session(vehicle_key: str) -> None:
        """Clear session data for a specific vehicle."""
        if f"vehicle_{vehicle_key}" in st.session_state:
            del st.session_state[f"vehicle_{vehicle_key}"]
    
    @staticmethod
    def get_global_preferences() -> Dict[str, Any]:
        """Get global user preferences."""
        if "global_preferences" not in st.session_state:
            st.session_state["global_preferences"] = {
                "default_view_mode": "simplified",  # "simplified" or "detailed"
                "auto_save_searches": True,
                "show_search_progress": True,
                "confidence_threshold": 0.6,
                "max_search_history": 10
            }
        return st.session_state["global_preferences"]
    
    @staticmethod
    def update_global_preferences(preferences: Dict[str, Any]) -> None:
        """Update global user preferences."""
        current_prefs = SessionStateManager.get_global_preferences()
        current_prefs.update(preferences)
        st.session_state["global_preferences"] = current_prefs
    
    @staticmethod
    def add_to_search_history(vehicle_key: str, search_result: Dict[str, Any]) -> None:
        """Add a search result to the history."""
        session_data = SessionStateManager.get_vehicle_session(vehicle_key)
        history = session_data.get("search_history", [])
        
        # Add timestamp to search result
        search_result["timestamp"] = datetime.now()
        history.append(search_result)
        
        # Limit history size
        max_history = SessionStateManager.get_global_preferences().get("max_search_history", 10)
        if len(history) > max_history:
            history = history[-max_history:]
        
        session_data["search_history"] = history
        st.session_state[f"vehicle_{vehicle_key}"] = session_data
    
    @staticmethod
    def get_recent_searches(limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent searches across all vehicles."""
        recent_searches = []
        
        for key in st.session_state:
            if key.startswith("vehicle_"):
                vehicle_data = st.session_state[key]
                history = vehicle_data.get("search_history", [])
                recent_searches.extend(history)
        
        # Sort by timestamp and return most recent
        recent_searches.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
        return recent_searches[:limit]


# CSS for simplified UI components
def add_simplified_ui_css() -> None:
    """Add CSS styles for simplified UI components."""
    st.markdown("""
    <style>
    /* Simplified UI component styles */
    .simplified-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        border: 1px solid rgba(0, 0, 0, 0.1);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
        padding: 1rem;
        margin: 0.5rem 0;
        transition: all 0.2s ease;
    }
    
    .simplified-card:hover {
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }
    
    .progress-item {
        display: inline-block;
        margin: 0.25rem;
        padding: 0.5rem 0.75rem;
        border-radius: 6px;
        font-size: 0.875rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .progress-item.searching {
        background: rgba(107, 114, 128, 0.1);
        border: 1px solid #6b7280;
        color: #6b7280;
    }
    
    .progress-item.found {
        background: rgba(22, 163, 74, 0.1);
        border: 1px solid #16a34a;
        color: #16a34a;
    }
    
    .progress-item.partial {
        background: rgba(217, 119, 6, 0.1);
        border: 1px solid #d97706;
        color: #d97706;
    }
    
    .progress-item.failed {
        background: rgba(220, 38, 38, 0.1);
        border: 1px solid #dc2626;
        color: #dc2626;
    }
    
    .confidence-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .confidence-high {
        color: #16a34a;
    }
    
    .confidence-medium {
        color: #d97706;
    }
    
    .confidence-low {
        color: #dc2626;
    }
    
    .toggle-button {
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid #3b82f6;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        color: #1e40af;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .toggle-button:hover {
        background: rgba(59, 130, 246, 0.2);
        transform: translateY(-1px);
    }
    </style>
    """, unsafe_allow_html=True)