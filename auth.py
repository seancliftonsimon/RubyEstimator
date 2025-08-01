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
        if hash_password(st.session_state["password"]) == st.secrets.get("password_hash", ""):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

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
    
    # Check if password protection is enabled
    if not st.secrets.get("password_hash"):
        return True  # No password protection enabled
    
    # Show login form
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1>🔒 RubyEstimator</h1>
        <p>Please enter the password to access the application.</p>
    </div>
    """, unsafe_allow_html=True)
    
    return check_password() 