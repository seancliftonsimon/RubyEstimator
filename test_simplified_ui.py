"""
Test file for simplified UI components.
Run this file to see the components in action.
"""

import streamlit as st
from simplified_ui_components import (
    SearchProgressTracker, ConfidenceCard, ProgressiveDisclosureManager,
    RealTimeStatus, SearchStatus, SimplifiedVehicleSpec, SearchProgress,
    render_simplified_search_interface, add_simplified_ui_css,
    create_mock_simplified_vehicle_spec, create_mock_search_progress,
    ConfidenceAggregator, SessionStateManager, create_confidence_summary_for_display
)
from confidence_ui import add_confidence_css, create_mock_provenance_info
import time

def test_simplified_ui_components():
    """Test all simplified UI components."""
    
    # Configure page
    st.set_page_config(
        page_title="Simplified UI Components Test",
        page_icon="🚗",
        layout="wide"
    )
    
    # Add CSS
    add_confidence_css()
    add_simplified_ui_css()
    
    st.title("🚗 Simplified UI Components Test")
    st.markdown("Testing the new simplified vehicle search interface components.")
    
    # Test 1: Search Progress Tracker
    st.header("1. Search Progress Tracker")
    st.markdown("Shows real-time progress during vehicle specification search.")
    
    if st.button("Test Progress Tracker"):
        specifications = ["curb_weight", "engine_material", "rim_material", "catalytic_converters"]
        tracker = SearchProgressTracker(specifications)
        
        # Initial render
        tracker.render()
        
        # Simulate progress updates
        progress_container = st.empty()
        with progress_container:
            st.info("Simulating search progress...")
            
            time.sleep(1)
            tracker.update_status("curb_weight", SearchStatus.FOUND)
            time.sleep(0.5)
            tracker.update_status("engine_material", SearchStatus.FOUND)
            time.sleep(0.5)
            tracker.update_status("rim_material", SearchStatus.PARTIAL)
            time.sleep(0.5)
            tracker.update_status("catalytic_converters", SearchStatus.FOUND)
            
            st.success("Search progress simulation complete!")
    
    st.divider()
    
    # Test 2: Confidence Card
    st.header("2. Confidence Card Component")
    st.markdown("Displays vehicle specifications with confidence indicators and expandable details.")
    
    # Create mock specification data
    specifications = {
        "Weight": {
            "value": "3,500 lbs",
            "confidence": 0.85,
            "provenance": create_mock_provenance_info("Curb Weight", 3500.0, 0.85)
        },
        "Catalytic Converters": {
            "value": "2",
            "confidence": 0.75,
            "provenance": create_mock_provenance_info("Catalytic Converters", 2.0, 0.75)
        },
        "Engine Material": {
            "value": "Aluminum",
            "confidence": 0.80,
            "provenance": create_mock_provenance_info("Engine Material", 1.0, 0.80)
        },
        "Rim Material": {
            "value": "Aluminum",
            "confidence": 0.90,
            "provenance": create_mock_provenance_info("Rim Material", 1.0, 0.90)
        }
    }
    
    confidence_card = ConfidenceCard("Vehicle Specifications", specifications)
    confidence_card.render()
    
    st.divider()
    
    # Test 3: Progressive Disclosure Manager
    st.header("3. Progressive Disclosure Manager")
    st.markdown("Manages expandable sections for detailed information.")
    
    disclosure_manager = ProgressiveDisclosureManager("test_disclosure")
    
    def render_technical_details():
        st.markdown("""
        **Technical Details:**
        - Resolution method: Grounded consensus
        - Sources: KBB.com, Edmunds.com, Manufacturer
        - Confidence threshold: 0.7
        - Last updated: 2024-01-15 14:30:00
        """)
        
        st.code("""
        {
            "method": "grounded_consensus",
            "sources": ["kbb.com", "edmunds.com", "manufacturer"],
            "confidence": 0.85,
            "candidates": [3450, 3500, 3550]
        }
        """)
    
    def render_source_analysis():
        st.markdown("""
        **Source Analysis:**
        - Primary sources: 3 automotive databases
        - Agreement level: 94%
        - Outlier detection: 1 value flagged
        - Reliability score: High
        """)
        
        import pandas as pd
        df = pd.DataFrame({
            "Source": ["KBB.com", "Edmunds.com", "Manufacturer"],
            "Value": [3450, 3500, 3550],
            "Confidence": ["90%", "85%", "80%"],
            "Status": ["✅ Normal", "✅ Normal", "⚠️ Slight deviation"]
        })
        st.dataframe(df, use_container_width=True)
    
    disclosure_manager.render_expandable_section("technical", "Technical Details", render_technical_details)
    disclosure_manager.render_expandable_section("sources", "Source Analysis", render_source_analysis)
    
    st.divider()
    
    # Test 4: Real-Time Status Component
    st.header("4. Real-Time Status Component")
    st.markdown("Provides live updates during search operations.")
    
    if st.button("Test Real-Time Status"):
        status_container = st.empty()
        real_time_status = RealTimeStatus(status_container)
        
        # Simulate search process
        real_time_status.start_search("2020 Toyota Camry")
        time.sleep(1)
        
        real_time_status.update_progress("curb_weight", "found")
        time.sleep(0.5)
        
        real_time_status.update_progress("engine_material", "found")
        time.sleep(0.5)
        
        real_time_status.update_progress("rim_material", "partial")
        time.sleep(0.5)
        
        real_time_status.update_progress("catalytic_converters", "found")
        time.sleep(0.5)
        
        mock_results = {
            "curb_weight": 3500.0,
            "engine_material": "Aluminum",
            "rim_material": "Aluminum",
            "catalytic_converters": 2
        }
        real_time_status.complete_search(mock_results)
    
    st.divider()
    
    # Test 5: Complete Simplified Search Interface
    st.header("5. Complete Simplified Search Interface")
    st.markdown("The full simplified search interface with all components integrated.")
    
    render_simplified_search_interface()
    
    st.divider()
    
    # Test 6: Simplified Vehicle Spec Data Model
    st.header("6. Simplified Vehicle Spec Data Model")
    st.markdown("Testing the streamlined data structure.")
    
    mock_spec = create_mock_simplified_vehicle_spec()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Critical Specifications")
        critical_specs = mock_spec.get_critical_specs()
        for key, value in critical_specs.items():
            confidence_level = mock_spec.get_confidence_level(key)
            st.write(f"**{key.replace('_', ' ').title()}:** {value} ({confidence_level} confidence)")
    
    with col2:
        st.subheader("Confidence Scores")
        for field, score in mock_spec.confidence_scores.items():
            st.metric(field.replace('_', ' ').title(), f"{score:.0%}")
    
    if mock_spec.warnings:
        st.warning("⚠️ " + "; ".join(mock_spec.warnings))
    
    st.divider()
    
    # Test 7: Enhanced Data Models
    st.header("7. Enhanced Data Models")
    st.markdown("Testing the enhanced SimplifiedVehicleSpec and SearchProgress data models.")
    
    # Test SimplifiedVehicleSpec enhancements
    st.subheader("Enhanced SimplifiedVehicleSpec")
    
    enhanced_spec = create_mock_simplified_vehicle_spec(
        weight=3500.0, cats=2, engine="Aluminum", rims="Aluminum",
        year=2020, make="Toyota", model="Camry"
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Overall Confidence", f"{enhanced_spec.calculate_overall_confidence():.0%}")
        st.metric("Data Completeness", f"{ConfidenceAggregator.calculate_data_completeness(enhanced_spec):.0f}%")
    
    with col2:
        quality_summary = enhanced_spec.get_data_quality_summary()
        st.metric("Available Fields", f"{quality_summary['available_fields']}/{quality_summary['total_fields']}")
        st.metric("High Confidence Fields", quality_summary['high_confidence_fields'])
    
    with col3:
        st.write("**Vehicle Info:**")
        st.write(f"Year: {enhanced_spec.year}")
        st.write(f"Make: {enhanced_spec.make}")
        st.write(f"Model: {enhanced_spec.model}")
        st.write(f"Sufficient Data: {'✅' if enhanced_spec.has_sufficient_data() else '❌'}")
    
    # Test SearchProgress enhancements
    st.subheader("Enhanced SearchProgress")
    
    search_progress = create_mock_search_progress()
    
    # Simulate some progress
    search_progress.update_specification_status("curb_weight", SearchStatus.FOUND)
    search_progress.update_specification_status("engine_material", SearchStatus.PARTIAL)
    search_progress.add_warning("Engine material confidence is medium")
    
    status_summary = search_progress.get_status_summary()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Progress", f"{status_summary['progress_percentage']:.0f}%")
        st.metric("Elapsed Time", f"{status_summary['elapsed_time']:.1f}s")
    
    with col2:
        st.metric("Completed Steps", f"{status_summary['completed_steps']}/{status_summary['total_steps']}")
        st.metric("Error Count", status_summary['error_count'])
    
    with col3:
        st.write("**Status Counts:**")
        for status, count in status_summary['status_counts'].items():
            st.write(f"{status.title()}: {count}")
    
    if search_progress.warnings:
        st.warning("⚠️ Warnings: " + "; ".join(search_progress.warnings))
    
    st.divider()
    
    # Test 8: Confidence Aggregation
    st.header("8. Confidence Score Aggregation")
    st.markdown("Testing confidence score analysis and aggregation methods.")
    
    confidence_summary = create_confidence_summary_for_display(enhanced_spec)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Confidence Analysis")
        st.metric("Overall Confidence", confidence_summary['display_info']['overall_confidence_text'])
        st.metric("Quality Grade", confidence_summary['quality_grade'])
        st.metric("Data Completeness", confidence_summary['display_info']['completion_status'])
        
        if confidence_summary['needs_review']:
            st.warning("⚠️ This vehicle needs manual review")
        else:
            st.success("✅ Vehicle data quality is acceptable")
    
    with col2:
        st.subheader("Confidence Distribution")
        distribution = confidence_summary['confidence_distribution']
        for level, count in distribution.items():
            st.metric(f"{level.title()} Confidence Fields", count)
        
        if confidence_summary['low_confidence_fields']:
            st.warning(f"Low confidence fields: {', '.join(confidence_summary['low_confidence_fields'])}")
    
    st.divider()
    
    # Test 9: Session State Management
    st.header("9. Session State Management")
    st.markdown("Testing session state management for user preferences and vehicle data.")
    
    # Initialize session for test vehicle
    test_vehicle_key = "2020_Toyota_Camry"
    SessionStateManager.initialize_vehicle_session(test_vehicle_key)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Vehicle Session Data")
        vehicle_session = SessionStateManager.get_vehicle_session(test_vehicle_key)
        st.json({
            "vehicle_key": test_vehicle_key,
            "has_search_progress": vehicle_session.get("search_progress") is not None,
            "has_vehicle_spec": vehicle_session.get("vehicle_spec") is not None,
            "search_history_count": len(vehicle_session.get("search_history", [])),
            "user_preferences": vehicle_session.get("user_preferences", {})
        })
    
    with col2:
        st.subheader("Global Preferences")
        global_prefs = SessionStateManager.get_global_preferences()
        st.json(global_prefs)
    
    # Test adding to search history
    if st.button("Add Test Search to History"):
        test_search_result = {
            "vehicle_key": test_vehicle_key,
            "curb_weight": 3500.0,
            "confidence": 0.85,
            "method": "grounded_consensus"
        }
        SessionStateManager.add_to_search_history(test_vehicle_key, test_search_result)
        st.success("Added test search to history!")
        st.rerun()
    
    # Show recent searches
    recent_searches = SessionStateManager.get_recent_searches(3)
    if recent_searches:
        st.subheader("Recent Searches")
        for i, search in enumerate(recent_searches, 1):
            with st.expander(f"Search {i}: {search.get('vehicle_key', 'Unknown')}"):
                st.json(search)
    
    st.divider()
    
    # Test 10: Progressive Disclosure with Confidence
    st.header("10. Enhanced Progressive Disclosure")
    st.markdown("Testing progressive disclosure with confidence-based auto-management.")
    
    enhanced_disclosure = ProgressiveDisclosureManager("enhanced_test")
    
    def render_high_confidence_content():
        st.success("This is high confidence data - auto-expanded!")
        st.write("Curb weight: 3,500 lbs (85% confidence)")
    
    def render_medium_confidence_content():
        st.warning("This is medium confidence data")
        st.write("Engine material: Aluminum (65% confidence)")
    
    def render_low_confidence_content():
        st.error("This is low confidence data - needs review")
        st.write("Catalytic converters: 2 (45% confidence)")
    
    enhanced_disclosure.render_expandable_section(
        "high_conf", "High Confidence Data", render_high_confidence_content, 0.85
    )
    enhanced_disclosure.render_expandable_section(
        "medium_conf", "Medium Confidence Data", render_medium_confidence_content, 0.65
    )
    enhanced_disclosure.render_expandable_section(
        "low_conf", "Low Confidence Data", render_low_confidence_content, 0.45
    )
    
    # Show expansion summary
    expansion_summary = enhanced_disclosure.get_expansion_summary()
    st.subheader("Expansion Summary")
    st.json(expansion_summary)
    
    # Control buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Expand All"):
            enhanced_disclosure.expand_all_sections()
            st.rerun()
    with col2:
        if st.button("Collapse All"):
            enhanced_disclosure.collapse_all_sections()
            st.rerun()
    with col3:
        if st.button("Reset Preferences"):
            enhanced_disclosure.reset_user_preferences()
            st.rerun()
    
    st.success("✅ All enhanced data models and state management features are working correctly!")


if __name__ == "__main__":
    test_simplified_ui_components()