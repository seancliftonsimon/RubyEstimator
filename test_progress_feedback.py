#!/usr/bin/env python3
"""
Test suite for the enhanced search interface with progress feedback.
Tests the core functionality without requiring Streamlit session state.
"""

import sys
import time
from typing import Dict, Any, List
from unittest.mock import Mock, patch

# Import the components we want to test
from simplified_ui_components import (
    SearchProgressTracker, SearchStatus, SearchProgress,
    SimplifiedVehicleSpec, ConfidenceAggregator
)

def test_search_progress_tracker_basic():
    """Test basic SearchProgressTracker functionality."""
    print("Testing SearchProgressTracker basic functionality...")
    
    specifications = ["curb_weight", "engine_material", "rim_material", "catalytic_converters"]
    tracker = SearchProgressTracker(specifications)
    
    # Test initial state
    assert len(tracker.progress.specifications) == 4
    assert all(status == SearchStatus.SEARCHING for status in tracker.progress.specifications.values())
    assert tracker.progress.completed_steps == 0
    assert tracker.current_phase == "Initializing search..."
    
    print("✅ Basic initialization test passed")

def test_search_progress_tracker_status_updates():
    """Test status updates with enhanced feedback."""
    print("Testing SearchProgressTracker status updates...")
    
    specifications = ["curb_weight", "engine_material"]
    tracker = SearchProgressTracker(specifications)
    
    # Test successful update with confidence
    tracker.update_status("curb_weight", SearchStatus.FOUND, confidence=0.85)
    assert tracker.progress.specifications["curb_weight"] == SearchStatus.FOUND
    assert tracker.progress.completed_steps == 1
    assert "curb_weight" not in tracker.low_confidence_warnings
    
    # Test low confidence update
    tracker.update_status("engine_material", SearchStatus.PARTIAL, confidence=0.45)
    assert tracker.progress.specifications["engine_material"] == SearchStatus.PARTIAL
    assert tracker.progress.completed_steps == 2
    assert "engine_material" in tracker.low_confidence_warnings
    
    print("✅ Status updates test passed")

def test_search_progress_tracker_error_handling():
    """Test error handling and recovery options."""
    print("Testing SearchProgressTracker error handling...")
    
    specifications = ["curb_weight", "engine_material"]
    tracker = SearchProgressTracker(specifications)
    
    # Test error message handling
    error_msg = "API timeout occurred"
    tracker.update_status("curb_weight", SearchStatus.FAILED, error_message=error_msg)
    assert tracker.progress.specifications["curb_weight"] == SearchStatus.FAILED
    assert tracker.error_messages["curb_weight"] == error_msg
    
    # Test timeout warning
    tracker.add_timeout_warning("engine_material", 35)
    assert "engine_material" in tracker.timeout_warnings
    
    # Test error recovery options
    tracker.add_error_recovery_options("curb_weight", "timeout")
    assert "timeout" in tracker.error_messages["curb_weight"].lower()
    
    # Test error summary
    summary = tracker.get_error_summary()
    assert summary["error_count"] == 1
    assert summary["timeout_count"] == 1
    assert summary["has_issues"] == True
    assert "curb_weight" in summary["failed_specs"]
    
    print("✅ Error handling test passed")

def test_search_progress_tracker_timing():
    """Test timing and timeout functionality."""
    print("Testing SearchProgressTracker timing...")
    
    specifications = ["curb_weight"]
    tracker = SearchProgressTracker(specifications)
    tracker.timeout_threshold = 1  # 1 second for testing
    
    # Start timing
    tracker.start_spec_timer("curb_weight")
    assert "curb_weight" in tracker.spec_start_times
    
    # Simulate timeout
    time.sleep(1.1)
    tracker.check_timeouts()
    assert "curb_weight" in tracker.timeout_warnings
    
    # Complete timing
    tracker.complete_spec_timer("curb_weight")
    assert "curb_weight" not in tracker.spec_start_times
    assert "curb_weight" not in tracker.timeout_warnings
    
    print("✅ Timing test passed")

def test_search_progress_tracker_retry_functionality():
    """Test retry functionality."""
    print("Testing SearchProgressTracker retry functionality...")
    
    specifications = ["curb_weight", "engine_material"]
    tracker = SearchProgressTracker(specifications)
    
    # Set up failed state
    tracker.update_status("curb_weight", SearchStatus.FAILED, error_message="Test error")
    tracker.add_timeout_warning("curb_weight", 30)
    
    # Test reset for retry
    tracker.reset_spec_for_retry("curb_weight")
    assert tracker.progress.specifications["curb_weight"] == SearchStatus.SEARCHING
    assert "curb_weight" not in tracker.error_messages
    assert "curb_weight" not in tracker.timeout_warnings
    
    print("✅ Retry functionality test passed")

def test_search_progress_completion_indicator():
    """Test progress completion indicator."""
    print("Testing progress completion indicator...")
    
    specifications = ["curb_weight", "engine_material", "rim_material"]
    tracker = SearchProgressTracker(specifications)
    
    # Initial state
    completion = tracker.get_progress_completion()
    assert "0 of 3" in completion
    
    # Update some specifications
    tracker.update_status("curb_weight", SearchStatus.FOUND)
    tracker.update_status("engine_material", SearchStatus.PARTIAL)
    
    completion = tracker.get_progress_completion()
    assert "2 of 3" in completion
    
    print("✅ Progress completion indicator test passed")

def test_simplified_vehicle_spec_enhancements():
    """Test SimplifiedVehicleSpec enhancements."""
    print("Testing SimplifiedVehicleSpec enhancements...")
    
    spec = SimplifiedVehicleSpec(
        year=2020,
        make="Toyota",
        model="Camry",
        curb_weight=3500.0,
        catalytic_converters=2,
        engine_material="Aluminum",
        rim_material="Aluminum"
    )
    
    # Test confidence calculation
    spec.confidence_scores = {
        "curb_weight": 0.9,
        "catalytic_converters": 0.7,
        "engine_material": 0.8,
        "rim_material": 0.85
    }
    
    overall_confidence = spec.calculate_overall_confidence()
    assert 0.7 < overall_confidence < 0.9  # Should be weighted average
    
    # Test data quality summary
    quality_summary = spec.get_data_quality_summary()
    assert quality_summary["available_fields"] == 4
    assert quality_summary["total_fields"] == 4
    assert quality_summary["overall_confidence"] > 0.7
    
    print("✅ SimplifiedVehicleSpec enhancements test passed")

def test_confidence_aggregator():
    """Test ConfidenceAggregator functionality."""
    print("Testing ConfidenceAggregator...")
    
    try:
        # Test weighted average calculation
        scores = {
            "curb_weight": 0.9,
            "catalytic_converters": 0.6,
            "engine_material": 0.8,
            "rim_material": 0.7
        }
        
        weighted_avg = ConfidenceAggregator.calculate_weighted_average(scores)
        assert 0.7 < weighted_avg < 0.9, f"Expected weighted average between 0.7 and 0.9, got {weighted_avg}"
        
        # Test confidence distribution
        distribution = ConfidenceAggregator.get_confidence_distribution(scores)
        assert distribution["high"] == 2, f"Expected 2 high confidence items, got {distribution['high']}"  # curb_weight, engine_material >= 0.8
        assert distribution["medium"] == 1, f"Expected 1 medium confidence item, got {distribution['medium']}"  # rim_material >= 0.6
        assert distribution["low"] == 1, f"Expected 1 low confidence item, got {distribution['low']}"  # catalytic_converters < 0.6
        
        # Test low confidence field identification
        low_confidence = ConfidenceAggregator.identify_low_confidence_fields(scores, threshold=0.7)
        assert "catalytic_converters" in low_confidence, f"Expected catalytic_converters in low confidence, got {low_confidence}"
        assert "rim_material" in low_confidence, f"Expected rim_material in low confidence, got {low_confidence}"
        assert len(low_confidence) == 2, f"Expected 2 low confidence fields, got {len(low_confidence)}"
        
        # Test quality grade
        grade_a = ConfidenceAggregator.get_quality_grade(0.85)
        grade_b = ConfidenceAggregator.get_quality_grade(0.75)
        grade_f = ConfidenceAggregator.get_quality_grade(0.45)
        
        assert grade_a == "A", f"Expected grade A for 0.85, got {grade_a}"
        assert grade_b == "B", f"Expected grade B for 0.75, got {grade_b}"
        assert grade_f == "F", f"Expected grade F for 0.45, got {grade_f}"
        
        print("✅ ConfidenceAggregator test passed")
        
    except Exception as e:
        print(f"❌ ConfidenceAggregator test failed with detailed error: {e}")
        import traceback
        traceback.print_exc()
        raise

def test_search_progress_data_model():
    """Test SearchProgress data model enhancements."""
    print("Testing SearchProgress data model...")
    
    progress = SearchProgress(
        vehicle_key="2020_Toyota_Camry",
        specifications={
            "curb_weight": SearchStatus.FOUND,
            "engine_material": SearchStatus.SEARCHING,
            "rim_material": SearchStatus.FAILED
        },
        total_steps=4,
        completed_steps=2
    )
    
    # Test progress percentage
    percentage = progress.get_progress_percentage()
    assert percentage == 50.0
    
    # Test next specification
    next_spec = progress.get_next_specification()
    assert next_spec == "engine_material"
    
    # Test status summary
    summary = progress.get_status_summary()
    assert summary["total_specifications"] == 3
    assert summary["completed_steps"] == 2
    assert summary["progress_percentage"] == 50.0
    assert summary["error_count"] == 0  # No errors added yet
    
    # Test successful specifications
    successful = progress.get_successful_specifications()
    assert "curb_weight" in successful
    assert len(successful) == 1
    
    # Test failed specifications
    failed = progress.get_failed_specifications()
    assert "rim_material" in failed
    assert len(failed) == 1
    
    print("✅ SearchProgress data model test passed")

def mock_streamlit_components():
    """Mock Streamlit components for testing render methods."""
    print("Testing render methods with mocked Streamlit...")
    
    try:
        with patch('simplified_ui_components.st') as mock_st:
            # Create a proper mock container context manager
            mock_container = Mock()
            mock_container.__enter__ = Mock(return_value=mock_container)
            mock_container.__exit__ = Mock(return_value=None)
            
            # Mock streamlit components
            mock_st.empty.return_value.container.return_value = mock_container
            mock_st.markdown = Mock()
            mock_st.columns = Mock(return_value=[Mock(), Mock()])
            mock_st.button = Mock(return_value=False)
            
            # Test SearchProgressTracker render
            specifications = ["curb_weight", "engine_material"]
            tracker = SearchProgressTracker(specifications)
            tracker.container = Mock()
            
            # This should not raise an exception
            tracker.render()
            print("✅ SearchProgressTracker render test passed")
            
    except Exception as e:
        print(f"❌ SearchProgressTracker render test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def run_all_tests():
    """Run all tests and report results."""
    print("🧪 Running Enhanced Search Interface Progress Feedback Tests")
    print("=" * 60)
    
    tests = [
        test_search_progress_tracker_basic,
        test_search_progress_tracker_status_updates,
        test_search_progress_tracker_error_handling,
        test_search_progress_tracker_timing,
        test_search_progress_tracker_retry_functionality,
        test_search_progress_completion_indicator,
        test_simplified_vehicle_spec_enhancements,
        test_confidence_aggregator,
        test_search_progress_data_model,
        mock_streamlit_components
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Enhanced search interface is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)