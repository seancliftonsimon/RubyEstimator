import streamlit as st
import hashlib
import os

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def _get_stored_password_hash() -> str:
    """Return the configured password hash (env first, then secrets). Empty means disabled."""
    stored_hash = os.getenv("PASSWORD_HASH", "") or ""
    if stored_hash:
        return stored_hash
    try:
        return st.secrets.get("password_hash", "") or ""
    except Exception:
        return ""

def clear_admin_auth():
    """Clear admin authentication state from the session."""
    if "admin_authenticated" in st.session_state:
        del st.session_state["admin_authenticated"]
    if "admin_password" in st.session_state:
        del st.session_state["admin_password"]

def require_admin_password() -> bool:
    """
    Gate Admin mode behind a password.
    - Uses a form so Enter submits.
    - Stores only a boolean in session state (never the plaintext password).
    """
    stored_hash = _get_stored_password_hash()
    if not stored_hash:
        st.session_state["admin_authenticated"] = True
        return True

    if st.session_state.get("admin_authenticated", False):
        return True

    st.markdown("### Admin Access")
    st.caption("Enter the admin password to continue.")

    with st.form("admin_login_form", clear_on_submit=False):
        # Streamlit will usually focus the first input on rerun; keep this as the first widget.
        password = st.text_input("Password", type="password", key="admin_password")
        submitted = st.form_submit_button("Log in")

    if submitted:
        if hash_password(password) == stored_hash:
            st.session_state["admin_authenticated"] = True
            if "admin_password" in st.session_state:
                del st.session_state["admin_password"]
            st.rerun()
        else:
            st.session_state["admin_authenticated"] = False
            if "admin_password" in st.session_state:
                del st.session_state["admin_password"]
            st.error("Password incorrect")

    return st.session_state.get("admin_authenticated", False)

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
    
    # Only show login form if password is not correct
    if "password_correct" not in st.session_state or not st.session_state["password_correct"]:
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <h1>Ruby GEM</h1>
            <p>Please enter the password to access the application.</p>
        </div>
        """, unsafe_allow_html=True)
    
    return check_password() 