import streamlit as st
import hashlib
import os

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password():
    """Returns `True` if the user had the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        try:
            # Try to get password hash from environment variable first
            stored_hash = os.getenv("PASSWORD_HASH", "")
            if not stored_hash:
                # Fallback to secrets (for local development)
                try:
                    stored_hash = st.secrets.get("password_hash", "")
                except:
                    # If secrets are not available, allow access
                    stored_hash = ""
            
            if hash_password(st.session_state["password"]) == stored_hash:
                st.session_state["password_correct"] = True
                del st.session_state["password"]  # Don't store password
            else:
                st.session_state["password_correct"] = False
        except:
            # If no password protection is configured, allow access
            st.session_state["password_correct"] = True
            del st.session_state["password"]

    # First run, show inputs for username + password.
    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    
    # Password correct.
    elif st.session_state["password_correct"]:
        return True
    
    # Password incorrect, show input + error.
    else:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False

def setup_password_protection():
    """Setup password protection for the app"""
    
    try:
        # Check if password protection is enabled via environment variable
        password_hash = os.getenv("PASSWORD_HASH")
        if not password_hash:
            # Fallback to secrets (for local development)
            try:
                password_hash = st.secrets.get("password_hash", "")
            except:
                # If secrets are not available, allow access
                password_hash = ""
        
        if not password_hash:
            return True  # No password protection enabled
    except:
        # If no password protection is configured, allow access
        return True
    
    # Show login form
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1>🔒 RubyEstimator</h1>
        <p>Please enter the password to access the application.</p>
    </div>
    """, unsafe_allow_html=True)
    
    return check_password() 