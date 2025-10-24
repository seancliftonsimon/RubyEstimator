"""
Simple test script to verify confidence UI components work correctly.
This can be run independently to test the confidence indicator functionality.
"""

import streamlit as st
from confidence_ui import (
    render_confidence_badge, render_warning_banner, render_provenance_panel,
    render_detailed_provenance_panel, create_mock_confidence_info, 
    create_mock_provenance_info, add_confidence_css
)

def test_confidence_ui():
    """Test the confidence UI components."""
    st.title("Confidence UI Components Test")
    
    # Add CSS
    add_confidence_css()
    
    st.header("1. Confidence Badges")
    
    # Test different confidence levels
    high_confidence = create_mock_confidence_info(0.9, [])
    medium_confidence = create_mock_confidence_info(0.7, ["Some variation between sources"])
    low_confidence = create_mock_confidence_info(0.4, ["Significant disagreement", "Limited data available"])
    
    st.markdown("High Confidence: " + render_confidence_badge(high_confidence), unsafe_allow_html=True)
    st.markdown("Medium Confidence: " + render_confidence_badge(medium_confidence), unsafe_allow_html=True)
    st.markdown("Low Confidence: " + render_confidence_badge(low_confidence), unsafe_allow_html=True)
    
    st.header("2. Warning Banners")
    
    render_warning_banner(["This is a test warning message"])
    render_warning_banner(["Multiple warnings can be displayed", "Each gets its own banner"])
    
    st.header("3. Basic Provenance Panel")
    
    provenance = create_mock_provenance_info("Test Field", 3500.0, 0.85)
    render_provenance_panel(provenance, expanded=True)
    
    st.header("4. Detailed Provenance Panel")
    
    detailed_provenance = create_mock_provenance_info("Curb Weight", 3600.0, 0.75)
    render_detailed_provenance_panel("Curb Weight", detailed_provenance)
    
    st.header("5. Table with Confidence Indicators")
    
    # Test table display with confidence badges
    import pandas as pd
    
    test_data = [
        {"Commodity": "ELV " + render_confidence_badge(high_confidence, "small"), "Weight": "2,500 lb", "Price": "$0.12", "Value": "$300.00"},
        {"Commodity": "Engine " + render_confidence_badge(medium_confidence, "small"), "Weight": "500 lb", "Price": "$0.35", "Value": "$175.00"},
        {"Commodity": "Catalytic Converters " + render_confidence_badge(low_confidence, "small"), "Count": "1.5", "Price": "$92.25", "Value": "$138.38"}
    ]
    
    df = pd.DataFrame(test_data)
    st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
    
    st.success("All confidence UI components are working correctly!")

if __name__ == "__main__":
    test_confidence_ui()