import streamlit as st
import hashlib
import os
import re
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import text

from database_config import create_database_engine
from persistence import ensure_schema

try:  # bcrypt is optional at import-time; required if any user uses passwords
    import bcrypt  # type: ignore
except Exception:  # pragma: no cover
    bcrypt = None  # type: ignore

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


# -----------------------------------------------------------------------------
# Buyer/user auth (DB-backed, per-session; no global "current user" in DB)
# -----------------------------------------------------------------------------

_USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z0-9@$!%*?&#^_+=\-]{8,64}$")


def normalize_username(username: str) -> str:
    return (username or "").strip().lower()


def is_valid_username(username: str) -> bool:
    u = normalize_username(username)
    return bool(u) and bool(_USERNAME_RE.match(u))


def _is_valid_password(password: str) -> bool:
    return bool(_PASSWORD_RE.match((password or "").strip()))


def _bcrypt_hash_password(password: str) -> str:
    if bcrypt is None:  # pragma: no cover
        raise RuntimeError("bcrypt is required for password support but is not installed.")
    pw_bytes = password.encode("utf-8")
    hashed = bcrypt.hashpw(pw_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def _bcrypt_verify_password(password: str, password_hash: str) -> bool:
    if bcrypt is None:  # pragma: no cover
        raise RuntimeError("bcrypt is required for password support but is not installed.")
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def create_user(
    username: str,
    display_name: Optional[str] = None,
    password: Optional[str] = None,
    is_admin: bool = False,
) -> Tuple[bool, str]:
    """
    Create a new user (buyer).

    Rules:
    - username must be unique and match [A-Za-z0-9_-]+ (stored normalized to lowercase)
    - password is required and must be 8-64 chars with letters + numbers
    """
    try:
        ensure_schema()
    except (ConnectionError, RuntimeError) as e:
        return False, f"Database connection error: {str(e)}. Please check your database configuration."

    username_norm = normalize_username(username)
    if not is_valid_username(username_norm):
        return False, "Invalid username. Use only letters, numbers, dot, underscore, or hyphen."

    if not password or not password.strip():
        return False, "Password is required."

    pw = password.strip()
    if not _is_valid_password(pw):
        return False, "Password must be 8-64 chars and include letters and numbers."
    pw_hash = _bcrypt_hash_password(pw)

    try:
        engine = create_database_engine()
        with engine.connect() as conn:
        try:
            conn.execute(
                text(
                    """
                    INSERT INTO users (username, display_name, password_hash, is_admin, created_at)
                    VALUES (:username, :display_name, :password_hash, :is_admin, CURRENT_TIMESTAMP)
                    """
                ),
                {
                    "username": username_norm,
                    "display_name": (display_name or "").strip() or None,
                    "password_hash": pw_hash,
                    "is_admin": bool(is_admin),
                },
            )
            conn.commit()
            return True, f"Created user '{username_norm}'"
        except Exception as exc:
            # Likely uniqueness violation; keep message generic.
            return False, f"Could not create user: {exc}"


def ensure_admin_user(username: str, passcode: str) -> Tuple[bool, str]:
    """
    Ensure the admin user exists in the database.
    Creates the user if it doesn't exist, or updates it to be admin if it exists but isn't admin.
    
    Args:
        username: Admin username
        passcode: Admin password
    
    Returns:
        Tuple[bool, str]: (success, message)
    """
    ensure_schema()
    username_norm = normalize_username(username)
    
    # Check if user already exists
    existing_user = get_user_by_username(username_norm)
    
    if existing_user:
        # User exists - check if they're already admin
        if existing_user.get("is_admin"):
            return True, f"Admin user '{username_norm}' already exists"
        
        # User exists but isn't admin - update to make them admin
        engine = create_database_engine()
        with engine.connect() as conn:
            try:
                conn.execute(
                    text("UPDATE users SET is_admin = TRUE WHERE username = :username"),
                    {"username": username_norm},
                )
                conn.commit()
                return True, f"Updated user '{username_norm}' to admin"
            except Exception as exc:
                return False, f"Could not update user to admin: {exc}"
    else:
        # User doesn't exist - create as admin
        return create_user(
            username=username_norm,
            display_name=None,
            password=passcode,
            is_admin=True,
        )


def list_users(limit: int = 200) -> list[Dict[str, Any]]:
    ensure_schema()
    engine = create_database_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, username, display_name, password_hash, is_admin, created_at
                FROM users
                ORDER BY created_at DESC
                LIMIT :limit
                """
            ),
            {"limit": int(limit)},
        ).fetchall()
    users = []
    for row in rows:
        user_id, username, display_name, password_hash, is_admin, created_at = row
        users.append(
            {
                "id": user_id,
                "username": username,
                "display_name": display_name,
                "has_password": bool(password_hash),
                "is_admin": bool(is_admin),
                "created_at": created_at,
            }
        )
    return users


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    try:
        ensure_schema()
    except (ConnectionError, RuntimeError) as e:
        raise ConnectionError(f"Database connection error: {str(e)}. Please check your database configuration.") from e
    
    username_norm = normalize_username(username)
    if not username_norm:
        return None

    try:
        engine = create_database_engine()
        with engine.connect() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT id, username, display_name, password_hash, is_admin, created_at
                    FROM users
                    WHERE username = :username
                    """
                ),
                {"username": username_norm},
            ).fetchone()

        if not row:
            return None

        user_id, uname, display_name, password_hash, is_admin, created_at = row
        return {
            "id": user_id,
            "username": uname,
            "display_name": display_name,
            "password_hash": password_hash,
            "has_password": bool(password_hash),
            "is_admin": bool(is_admin),
            "created_at": created_at,
        }
    except (ConnectionError, RuntimeError) as e:
        raise ConnectionError(f"Database connection error: {str(e)}. Please check your database configuration.") from e
    except Exception as e:
        raise RuntimeError(f"Database error: {str(e)}. Please contact support.") from e


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    ensure_schema()
    engine = create_database_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT id, username, display_name, password_hash, is_admin, created_at
                FROM users
                WHERE id = :id
                """
            ),
            {"id": int(user_id)},
        ).fetchone()

    if not row:
        return None

    uid, uname, display_name, password_hash, is_admin, created_at = row
    return {
        "id": uid,
        "username": uname,
        "display_name": display_name,
        "password_hash": password_hash,
        "has_password": bool(password_hash),
        "is_admin": bool(is_admin),
        "created_at": created_at,
    }


def login_user(username: str, password: Optional[str] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Login rules:
    - Password is always required and verified against bcrypt hash.
    """
    try:
        user = get_user_by_username(username)
    except (ConnectionError, RuntimeError) as e:
        # Database connection error
        return False, f"Database connection error: {str(e)}. Please check your database configuration.", None
    except Exception as e:
        # Other database errors
        return False, f"Database error: {str(e)}. Please contact support.", None
    
    if not user:
        return False, "Unknown username. Ask admin to create it.", None

    pw_hash = user.get("password_hash")
    if not pw_hash:
        return False, "Password is required. Ask admin to reset this account.", None

    if not password:
        return False, "Password required.", None

    ok = _bcrypt_verify_password(password, pw_hash)
    if not ok:
        return False, "Incorrect password.", None

    user.pop("password_hash", None)
    return True, "Logged in", user


def render_login_ui(session_key: str = "buyer_user") -> bool:
    """
    Streamlit-native login UI. Stores user dict in st.session_state[session_key].

    Returns True when logged in.
    """
    if st.session_state.get(session_key):
        return True

    # Centered, wider login "card"
    left, center, right = st.columns([1.0, 1.8, 1.0])
    with center:
        st.subheader("Buyer Login")

        with st.form("buyer_login_form", clear_on_submit=False):
            username = st.text_input("Username", key="buyer_login_username")
            passcode = st.text_input(
                "Password",
                type="password",
                key="buyer_login_passcode",
            )
            submitted = st.form_submit_button("Log in", use_container_width=True)

        if submitted:
            if passcode and not _is_valid_password(passcode):
                st.error("Password must be 8-64 chars and include letters and numbers.")
            else:
                ok, msg, user = login_user(username=username, password=passcode)
                if ok and user:
                    st.session_state[session_key] = user
                    # Clear passcode field from state
                    if "buyer_login_passcode" in st.session_state:
                        del st.session_state["buyer_login_passcode"]
                    st.rerun()
                else:
                    st.error(msg)

        st.caption("Need an account?")

        # Smaller option below the login card
        with st.expander("Create user", expanded=False):
            with st.form("buyer_create_user_form", clear_on_submit=False):
                new_username = st.text_input("Username", key="buyer_signup_username")
                new_display_name = st.text_input("Display name (optional)", key="buyer_signup_display_name")
                new_passcode = st.text_input(
                    "Create a password",
                    type="password",
                    key="buyer_signup_passcode",
                )
                new_passcode2 = st.text_input(
                    "Confirm password",
                    type="password",
                    key="buyer_signup_passcode_confirm",
                )
                create_submitted = st.form_submit_button("Create user")

            if create_submitted:
                if not new_username:
                    st.error("Username is required.")
                elif not _is_valid_password(new_passcode or ""):
                    st.error("Password must be 8-64 chars and include letters and numbers.")
                elif new_passcode != new_passcode2:
                    st.error("Passwords do not match.")
                else:
                    ok, msg = create_user(
                        username=new_username,
                        display_name=new_display_name,
                        password=new_passcode,
                        is_admin=False,
                    )
                    if ok:
                        # Auto-login after successful signup
                        ok2, msg2, user = login_user(username=new_username, password=new_passcode)
                        if ok2 and user:
                            st.session_state[session_key] = user
                            # Clear sensitive fields
                            for k in [
                                "buyer_signup_passcode",
                                "buyer_signup_passcode_confirm",
                                "buyer_login_passcode",
                            ]:
                                if k in st.session_state:
                                    del st.session_state[k]
                            st.rerun()
                        else:
                            st.success(msg)
                            st.info(msg2)
                    else:
                        st.error(msg)

    return False

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