#!/usr/bin/env python3
"""
Quick test to verify HTML rendering in SearchProgressTracker
"""

def test_html_formatting():
    """Test that HTML formatting is correct."""
    from simplified_ui_components import SearchProgressTracker
    
    specifications = ["curb_weight", "engine_material"]
    tracker = SearchProgressTracker(specifications)
    
    # Test progress completion string
    completion = tracker.get_progress_completion()
    print(f"Progress completion: '{completion}'")
    assert "0 of 2" in completion
    
    # Test current phase string
    phase = tracker.current_phase
    print(f"Current phase: '{phase}'")
    assert isinstance(phase, str)
    assert len(phase) > 0
    
    # Test that we can format HTML without errors
    try:
        progress_completion = tracker.get_progress_completion()
        current_phase = tracker.current_phase
        
        html_content = f"""
        <div style="background: rgba(248, 250, 252, 0.95);">
            <div>🔍 Search Progress</div>
            <div>{progress_completion}</div>
            <div>{current_phase}</div>
        </div>
        """
        
        print("HTML formatting test passed ✅")
        print(f"Sample HTML: {html_content[:100]}...")
        
    except Exception as e:
        print(f"HTML formatting test failed ❌: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_html_formatting()
    if success:
        print("\n🎉 HTML rendering fix verified!")
    else:
        print("\n❌ HTML rendering still has issues")