"""
Confidence indicator and provenance UI components for the Ruby GEM Estimator.
Provides visual indicators for data confidence levels and source transparency.
"""

import streamlit as st
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ConfidenceInfo:
    """Information about confidence level for a resolved value."""
    score: float  # 0.0 to 1.0
    level: str    # "high", "medium", "low"
    explanation: str
    warnings: List[str]


@dataclass
class ProvenanceInfo:
    """Information about how a value was resolved."""
    method: str
    sources: List[str]
    candidates: List[Dict[str, Any]]
    final_value: float
    confidence: ConfidenceInfo
    resolved_at: Optional[datetime] = None


def get_confidence_level(score: float) -> str:
    """Convert confidence score to level category."""
    if score >= 0.8:
        return "high"
    elif score >= 0.6:
        return "medium"
    else:
        return "low"


def get_confidence_explanation(level: str, score: float) -> str:
    """Get plain-English explanation for confidence level."""
    explanations = {
        "high": f"High confidence ({score:.0%}) - Multiple sources agree closely",
        "medium": f"Medium confidence ({score:.0%}) - Some variation between sources",
        "low": f"Low confidence ({score:.0%}) - Significant disagreement or limited data"
    }
    return explanations.get(level, f"Unknown confidence level ({score:.0%})")


def render_confidence_badge(confidence_info: ConfidenceInfo, size: str = "normal", show_all: bool = False) -> str:
    """
    Render a confidence badge with color-coded status.
    Only shows badges for medium/low confidence unless show_all=True.
    
    Args:
        confidence_info: Confidence information
        size: "small", "normal", or "large"
        show_all: If True, show badges even for high confidence (default: False)
    
    Returns:
        HTML string for the confidence badge (empty string if high confidence and show_all=False)
    """
    # Only show badges for medium/low confidence (< 80%) unless explicitly requested
    if confidence_info.score >= 0.8 and not show_all:
        return ""
    
    colors = {
        "high": {"bg": "#dcfce7", "border": "#16a34a", "text": "#15803d"},
        "medium": {"bg": "#fef3c7", "border": "#d97706", "text": "#92400e"},
        "low": {"bg": "#fee2e2", "border": "#dc2626", "text": "#991b1b"}
    }
    
    sizes = {
        "small": {"padding": "0.25rem 0.5rem", "font_size": "0.75rem"},
        "normal": {"padding": "0.375rem 0.75rem", "font_size": "0.875rem"},
        "large": {"padding": "0.5rem 1rem", "font_size": "1rem"}
    }
    
    color = colors[confidence_info.level]
    size_style = sizes[size]
    
    # Show appropriate icon based on level
    icon = "⚠️" if confidence_info.level == "medium" else "❌" if confidence_info.level == "low" else "✓"
    
    badge_html = f'<span class="confidence-badge confidence-{confidence_info.level}" style="background-color: {color["bg"]}; border: 1px solid {color["border"]}; color: {color["text"]}; padding: {size_style["padding"]}; font-size: {size_style["font_size"]}; font-weight: 600; border-radius: 4px; display: inline-block; margin-left: 0.5rem;" title="{confidence_info.explanation}">{icon} {confidence_info.level.upper()} ({confidence_info.score:.0%})</span>'
    
    return badge_html


def render_warning_banner(warnings: List[str]) -> None:
    """
    Render warning banners for low-confidence estimates or manual review requirements.
    
    Args:
        warnings: List of warning messages
    """
    if not warnings:
        return
    
    for warning in warnings:
        st.markdown(f"""
        <div class="warning-banner" style="
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid #ef4444;
            border-left: 4px solid #ef4444;
            padding: 1rem;
            border-radius: 6px;
            margin: 0.5rem 0;
            color: #dc2626;
            font-weight: 500;
        ">
            ⚠️ {warning}
        </div>
        """, unsafe_allow_html=True)


def render_provenance_panel(provenance_info: ProvenanceInfo, expanded: bool = False) -> None:
    """
    Render an expandable provenance panel showing resolution method and sources.
    
    Args:
        provenance_info: Provenance information
        expanded: Whether to show expanded by default
    """
    with st.expander(f"📋 Source Details - {provenance_info.method}", expanded=expanded):
        # Resolution summary
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Final Value:** {provenance_info.final_value}")
            st.markdown(f"**Method:** {provenance_info.method}")
        with col2:
            st.markdown(f"**Confidence:** {provenance_info.confidence.score:.0%}")
            if provenance_info.resolved_at:
                st.markdown(f"**Resolved:** {provenance_info.resolved_at.strftime('%Y-%m-%d %H:%M')}")
        
        # Sources and candidates
        if provenance_info.sources:
            st.markdown("**Sources:**")
            for i, source in enumerate(provenance_info.sources, 1):
                # Make sources clickable if they look like URLs
                if source.startswith(('http://', 'https://')):
                    st.markdown(f"{i}. [{source}]({source})")
                else:
                    st.markdown(f"{i}. {source}")
        
        # Candidate values if available
        if provenance_info.candidates:
            st.markdown("**Candidate Values:**")
            candidates_df = []
            for candidate in provenance_info.candidates:
                candidates_df.append({
                    "Value": candidate.get("value", "N/A"),
                    "Source": candidate.get("source", "Unknown"),
                    "Confidence": f"{candidate.get('confidence', 0):.0%}" if candidate.get('confidence') else "N/A"
                })
            
            if candidates_df:
                import pandas as pd
                df = pd.DataFrame(candidates_df)
                st.dataframe(df, use_container_width=True)
        
        # Warnings
        if provenance_info.confidence.warnings:
            st.markdown("**Warnings:**")
            for warning in provenance_info.confidence.warnings:
                st.markdown(f"• {warning}")


def render_detailed_provenance_panel(field_name: str, provenance_info: ProvenanceInfo) -> None:
    """
    Render a detailed provenance panel with enhanced source transparency features.
    
    Args:
        field_name: Name of the field being displayed
        provenance_info: Provenance information
    """
    st.markdown(f"""
    <div class="provenance-panel-header" style="
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border: 1px solid #cbd5e1;
        border-radius: 8px 8px 0 0;
        padding: 1rem;
        margin-top: 1rem;
    ">
        <h4 style="margin: 0; color: #334155; font-size: 1.1rem;">
            🔍 {field_name} - Resolution Details
        </h4>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown("""
        <div style="
            border: 1px solid #cbd5e1;
            border-top: none;
            border-radius: 0 0 8px 8px;
            padding: 1rem;
            background: #ffffff;
        ">
        """, unsafe_allow_html=True)
        
        # Method and confidence overview
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div style="text-align: center; padding: 0.5rem;">
                <div style="font-size: 0.875rem; color: #64748b; margin-bottom: 0.25rem;">Resolution Method</div>
                <div style="font-weight: 600; color: #334155;">{provenance_info.method}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            confidence_color = "#16a34a" if provenance_info.confidence.level == "high" else "#d97706" if provenance_info.confidence.level == "medium" else "#dc2626"
            st.markdown(f"""
            <div style="text-align: center; padding: 0.5rem;">
                <div style="font-size: 0.875rem; color: #64748b; margin-bottom: 0.25rem;">Confidence Score</div>
                <div style="font-weight: 600; color: {confidence_color};">{provenance_info.confidence.score:.0%}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="text-align: center; padding: 0.5rem;">
                <div style="font-size: 0.875rem; color: #64748b; margin-bottom: 0.25rem;">Final Value</div>
                <div style="font-weight: 600; color: #334155;">{provenance_info.final_value}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Candidate analysis with outlier detection (only if we have multiple different values)
        if provenance_info.candidates and len(provenance_info.candidates) > 0:
            # Create enhanced candidates table
            candidates_data = []
            values = [c.get("value", 0) for c in provenance_info.candidates if c.get("value") is not None]
            
            if values and len(values) > 0:
                st.markdown("### 📊 Source Analysis")
                import statistics
                median_val = statistics.median(values)
                mean_val = statistics.mean(values)
                
                for i, candidate in enumerate(provenance_info.candidates):
                    value = candidate.get("value", 0)
                    source = candidate.get("source", "Unknown")
                    confidence = candidate.get("confidence", 0)
                    
                    # Detect outliers (values more than 20% from median)
                    is_outlier = abs(value - median_val) / median_val > 0.2 if median_val > 0 else False
                    outlier_indicator = "🔴 Outlier" if is_outlier else "✅ Normal"
                    
                    # Calculate deviation from consensus
                    deviation = ((value - median_val) / median_val * 100) if median_val > 0 else 0
                    
                    candidates_data.append({
                        "Source": source,
                        "Value": f"{value:,.2f}",
                        "Confidence": f"{confidence:.0%}",
                        "Deviation": f"{deviation:+.1f}%",
                        "Status": outlier_indicator
                    })
                
                import pandas as pd
                candidates_df = pd.DataFrame(candidates_data)
                st.dataframe(candidates_df, use_container_width=True, hide_index=True)
                
                # Statistical summary - only show if we have variation in values
                if len(set(values)) > 1:
                    st.markdown("### 📈 Statistical Summary")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Median", f"{median_val:,.2f}")
                    with col2:
                        st.metric("Mean", f"{mean_val:,.2f}")
                    with col3:
                        std_dev = statistics.stdev(values) if len(values) > 1 else 0
                        st.metric("Std Dev", f"{std_dev:,.2f}")
                    with col4:
                        range_val = max(values) - min(values) if values else 0
                        st.metric("Range", f"{range_val:,.2f}")
                else:
                    # All sources agree on the same value
                    st.markdown("**✅ All sources agree on this value**")
        
        # Source reliability and citations
        if provenance_info.sources:
            st.markdown("### 🔗 Source Citations")
            for i, source in enumerate(provenance_info.sources, 1):
                # Determine source reliability indicator
                reliability_indicators = {
                    "kbb.com": "🟢 High Reliability",
                    "edmunds.com": "🟢 High Reliability", 
                    "manufacturer": "🟢 High Reliability",
                    "autotrader.com": "🟡 Medium Reliability",
                    "cars.com": "🟡 Medium Reliability"
                }
                
                reliability = reliability_indicators.get(source.lower(), "🟡 Unknown Reliability")
                
                if source.startswith(('http://', 'https://')):
                    st.markdown(f"""
                    <div style="
                        background: #f8fafc;
                        border: 1px solid #e2e8f0;
                        border-radius: 6px;
                        padding: 0.75rem;
                        margin: 0.5rem 0;
                    ">
                        <div style="font-weight: 600; margin-bottom: 0.25rem;">
                            {i}. <a href="{source}" target="_blank" style="color: #3b82f6; text-decoration: none;">{source}</a>
                        </div>
                        <div style="font-size: 0.875rem; color: #64748b;">{reliability}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="
                        background: #f8fafc;
                        border: 1px solid #e2e8f0;
                        border-radius: 6px;
                        padding: 0.75rem;
                        margin: 0.5rem 0;
                    ">
                        <div style="font-weight: 600; margin-bottom: 0.25rem;">{i}. {source}</div>
                        <div style="font-size: 0.875rem; color: #64748b;">{reliability}</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Resolution timestamp and caching info
        if provenance_info.resolved_at:
            st.markdown("### ⏰ Resolution History")
            time_ago = datetime.now() - provenance_info.resolved_at
            if time_ago.days > 0:
                time_str = f"{time_ago.days} days ago"
            elif time_ago.seconds > 3600:
                time_str = f"{time_ago.seconds // 3600} hours ago"
            else:
                time_str = f"{time_ago.seconds // 60} minutes ago"
            
            st.markdown(f"""
            <div style="
                background: #fef3c7;
                border: 1px solid #f59e0b;
                border-radius: 6px;
                padding: 0.75rem;
                margin: 0.5rem 0;
            ">
                <div style="font-size: 0.875rem;">
                    <strong>Resolved:</strong> {provenance_info.resolved_at.strftime('%Y-%m-%d at %H:%M:%S')} ({time_str})
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)


def create_mock_confidence_info(score: float, warnings: List[str] = None) -> ConfidenceInfo:
    """Create mock confidence info for testing/demo purposes."""
    level = get_confidence_level(score)
    explanation = get_confidence_explanation(level, score)
    return ConfidenceInfo(
        score=score,
        level=level,
        explanation=explanation,
        warnings=warnings or []
    )


def create_mock_provenance_info(field_name: str, value: float, confidence_score: float = 0.85) -> ProvenanceInfo:
    """Create mock provenance info for testing/demo purposes."""
    confidence = create_mock_confidence_info(confidence_score)
    
    # Handle None values by using a default
    if value is None:
        value = 0.0
    
    # Mock candidates based on the field
    candidates = [
        {"value": value * 0.95, "source": "kbb.com", "confidence": 0.9},
        {"value": value, "source": "edmunds.com", "confidence": 0.85},
        {"value": value * 1.05, "source": "manufacturer", "confidence": 0.8}
    ]
    
    return ProvenanceInfo(
        method="grounded_consensus",
        sources=["kbb.com", "edmunds.com", "manufacturer"],
        candidates=candidates,
        final_value=value,
        confidence=confidence,
        resolved_at=datetime.now()
    )


def add_confidence_css() -> None:
    """Add CSS styles for confidence indicators and provenance panels."""
    st.markdown("""
    <style>
    /* Confidence badge animations - only for medium/low */
    .confidence-badge {
        transition: all 0.2s ease;
        cursor: help;
    }
    
    .confidence-badge:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    }
    
    /* Warning banner styling */
    .warning-banner {
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Provenance panel styling */
    .provenance-panel {
        background: rgba(248, 250, 252, 0.8);
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    /* Enhanced table styling for candidates */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(153, 12, 65, 0.08);
    }
    
    /* Enhanced table styling for results with confidence indicators */
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 1rem 0;
        background: white;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(153, 12, 65, 0.08);
    }
    
    table th {
        background: linear-gradient(135deg, #990C41 0%, #c00e4f 100%) !important;
        color: white !important;
        padding: 1rem !important;
        font-weight: 600;
        font-size: 1.1rem;
        text-align: left;
    }
    
    table td {
        padding: 0.875rem 1rem !important;
        border-bottom: 1px solid #e2e8f0;
        vertical-align: middle;
        font-size: 1rem;
    }
    
    table tr:nth-child(even) {
        background: #f8fafc;
    }
    
    table tr:hover {
        background: #f1f5f9;
        box-shadow: 0 2px 4px rgba(153, 12, 65, 0.08);
    }
    
    /* Ensure confidence badges display properly in tables */
    table .confidence-badge {
        display: inline-block;
        vertical-align: middle;
        margin-left: 0.5rem;
    }
    
    /* Tooltip styling for confidence badges */
    .confidence-badge[title]:hover::after {
        content: attr(title);
        position: absolute;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(30, 41, 59, 0.95);
        color: white;
        padding: 0.5rem;
        border-radius: 4px;
        font-size: 0.875rem;
        white-space: nowrap;
        z-index: 1000;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)