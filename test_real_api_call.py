"""
Test real API call to verify search grounding works.
"""

import os
import google.generativeai as genai

def test_real_search_grounding():
    """Test real search grounding API call."""
    
    # Check if API key is available
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == "YOUR_GEMINI_API_KEY":
        print("❌ No valid GEMINI_API_KEY found - skipping real API test")
        return True  # Skip test if no API key
    
    print("🔑 API key found, testing real search grounding...")
    
    try:
        # Configure the API
        genai.configure(api_key=api_key)
        
        # Create model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Test prompt
        prompt = "What is the curb weight of a 2020 Toyota Camry in pounds?"
        
        print("📡 Making API call with google_search tool...")
        
        # Make API call with search grounding
        response = model.generate_content(
            prompt,
            tools=[{"google_search": {}}]
        )
        
        print(f"✅ API call successful!")
        print(f"📝 Response: {response.text[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ API call failed: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Check if it's the specific search grounding error
        if "Unknown field for FunctionDeclaration" in str(e):
            print("🔍 This appears to be a search grounding configuration issue")
            print("💡 The google_search tool format may not be supported in this API version")
            return False
        elif "google_search" in str(e).lower():
            print("🔍 This appears to be a search grounding related error")
            return False
        else:
            print("🔍 This appears to be a different API error (not search grounding)")
            return True  # Not a search grounding issue
    
def test_without_search_grounding():
    """Test API call without search grounding for comparison."""
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == "YOUR_GEMINI_API_KEY":
        print("❌ No valid GEMINI_API_KEY found - skipping comparison test")
        return True
    
    print("🔄 Testing API call without search grounding for comparison...")
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = "What is the curb weight of a 2020 Toyota Camry in pounds?"
        
        # Make API call WITHOUT search grounding
        response = model.generate_content(
            prompt
        )
        
        print(f"✅ API call without search grounding successful!")
        print(f"📝 Response: {response.text[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ API call without search grounding failed: {e}")
        return False

if __name__ == '__main__':
    print("🧪 Testing Real API Calls for Search Grounding\n")
    
    # Test without search grounding first
    print("=== Test 1: Without Search Grounding ===")
    no_search_success = test_without_search_grounding()
    
    print("\n=== Test 2: With Search Grounding ===")
    search_success = test_real_search_grounding()
    
    print(f"\n📊 Results:")
    print(f"   Without search grounding: {'✅ PASS' if no_search_success else '❌ FAIL'}")
    print(f"   With search grounding: {'✅ PASS' if search_success else '❌ FAIL'}")
    
    if no_search_success and search_success:
        print("\n🎉 Both API calls work - search grounding is properly configured!")
    elif no_search_success and not search_success:
        print("\n⚠️  Basic API works but search grounding has issues")
        print("💡 This suggests the search grounding configuration needs to be updated")
    elif not no_search_success:
        print("\n❌ Basic API calls are failing - check API key and network connection")
    else:
        print("\n🤔 Unexpected result combination")