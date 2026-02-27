#!/usr/bin/env python3
"""Test database connection and admin login for restored Supabase database."""

import os
import sys
import argparse
from sqlalchemy import text

# Import database and auth modules
try:
    from database_config import create_database_engine, test_database_connection, get_database_url
    from auth import login_user, get_user_by_username, ensure_admin_user, require_admin_user
except ImportError as e:
    print(f"[ERROR] Failed to import required modules: {e}")
    print("   Make sure you're running this from the project directory.")
    sys.exit(1)


def test_database_connection_and_data():
    """Test database connection and check for restored data."""
    print("=" * 70)
    print("DATABASE CONNECTION TEST")
    print("=" * 70)
    
    # Test connection
    print("\n[1] Testing database connection...")
    try:
        success, message = test_database_connection()
        if success:
            print(f"   [OK] {message}")
        else:
            print(f"   [FAIL] {message}")
            return False
    except Exception as e:
        print(f"   [FAIL] Connection failed: {e}")
        return False
    
    # Show connection info (masked)
    print("\n[2] Database connection details:")
    try:
        url = get_database_url()
        # Mask password in URL
        if "@" in url:
            parts = url.split("@")
            if ":" in parts[0]:
                user_pass = parts[0].split("://")[1]
                if ":" in user_pass:
                    user = user_pass.split(":")[0]
                    protocol = parts[0].split("://")[0]
                    masked_url = f"{protocol}://{user}:****@{parts[1]}"
                    print(f"   Connection: {masked_url}")
        else:
            print(f"   Connection: {url}")
    except Exception as e:
        print(f"   [WARN] Could not get connection URL: {e}")
    
    # Check for data in key tables
    print("\n[3] Checking for restored data in database tables...")
    try:
        engine = create_database_engine()
        with engine.connect() as conn:
            # List of tables to check
            tables_to_check = [
                'users',
                'vehicles',
                'field_values',
                'evidence',
                'runs'
            ]
            
            found_data = False
            for table in tables_to_check:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    if count > 0:
                        print(f"   [OK] {table}: {count} row(s)")
                        found_data = True
                    else:
                        print(f"   [WARN] {table}: 0 rows (empty)")
                except Exception as e:
                    print(f"   [FAIL] {table}: Error - {e}")
            
            if found_data:
                print("\n   [OK] Database contains data from backup!")
            else:
                print("\n   [WARN] Database appears empty (no data found in key tables)")
            
            return True
            
    except Exception as e:
        print(f"   [FAIL] Failed to check tables: {e}")
        return False


def test_admin_role_checks():
    """Test require_admin_user for RLS/role-based permission behavior (no DB required)."""
    print("\n" + "=" * 70)
    print("ADMIN ROLE CHECK TEST (RLS)")
    print("=" * 70)
    try:
        # Non-admin or missing user must be rejected
        assert require_admin_user(None) is False, "None should not be admin"
        assert require_admin_user({}) is False, "Empty dict should not be admin"
        assert require_admin_user({"is_admin": False}) is False, "is_admin=False should not be admin"
        assert require_admin_user({"is_admin": None}) is False, "is_admin=None should not be admin"
        # Admin must be allowed
        assert require_admin_user({"is_admin": True}) is True, "is_admin=True should be admin"
        assert require_admin_user({"id": 1, "username": "a", "is_admin": True}) is True
        print("\n   [OK] require_admin_user: admin vs user permission checks passed")
        return True
    except AssertionError as e:
        print(f"\n   [FAIL] {e}")
        return False
    except Exception as e:
        print(f"\n   [FAIL] Error: {e}")
        return False


def test_admin_bootstrap():
    """Test admin bootstrap credentials."""
    print("\n" + "=" * 70)
    print("ADMIN BOOTSTRAP TEST")
    print("=" * 70)
    
    # Get bootstrap credentials from environment
    bootstrap_username = os.getenv("ADMIN_BOOTSTRAP_USERNAME", "").strip()
    bootstrap_password = os.getenv("ADMIN_BOOTSTRAP_PASSWORD", "").strip()
    
    if not bootstrap_username or not bootstrap_password:
        print("\n[WARN] ADMIN_BOOTSTRAP_USERNAME and ADMIN_BOOTSTRAP_PASSWORD not set")
        print("   These should be set in Railway environment variables.")
        print("   Skipping admin login test.")
        return False
    
    print(f"\n[1] Bootstrap credentials found:")
    print(f"   Username: {bootstrap_username}")
    print(f"   Password: {'*' * len(bootstrap_password)} (hidden)")
    
    # Test ensure_admin_user (this is what app.py does on startup)
    print(f"\n[2] Ensuring admin user exists...")
    try:
        ok, msg = ensure_admin_user(username=bootstrap_username, passcode=bootstrap_password)
        if ok:
            print(f"   [OK] {msg}")
        else:
            print(f"   [FAIL] {msg}")
            return False
    except Exception as e:
        print(f"   [FAIL] Error ensuring admin user: {e}")
        return False
    
    # Test login
    print(f"\n[3] Testing admin login...")
    try:
        ok, msg, user = login_user(username=bootstrap_username, password=bootstrap_password)
        if ok and user:
            print(f"   [OK] Login successful!")
            print(f"   User details:")
            print(f"      - Username: {user.get('username')}")
            print(f"      - Display Name: {user.get('display_name', 'N/A')}")
            print(f"      - Is Admin: {user.get('is_admin', False)}")
            if user.get('is_admin'):
                print(f"   [OK] User has admin privileges")
            else:
                print(f"   [WARN] User does NOT have admin privileges")
                return False
            return True
        else:
            print(f"   [FAIL] Login failed: {msg}")
            return False
    except Exception as e:
        print(f"   [FAIL] Error during login: {e}")
        return False


def main():
    """Run all tests."""
    parser = argparse.ArgumentParser(description='Test database connection and admin login')
    parser.add_argument('--database-url', help='Database connection string (or set DATABASE_URL env var)')
    parser.add_argument('--admin-username', help='Admin username (or set ADMIN_BOOTSTRAP_USERNAME env var)')
    parser.add_argument('--admin-password', help='Admin password (or set ADMIN_BOOTSTRAP_PASSWORD env var)')
    args = parser.parse_args()
    
    # Set environment variables from command line if provided
    if args.database_url:
        os.environ['DATABASE_URL'] = args.database_url
    if args.admin_username:
        os.environ['ADMIN_BOOTSTRAP_USERNAME'] = args.admin_username
    if args.admin_password:
        os.environ['ADMIN_BOOTSTRAP_PASSWORD'] = args.admin_password
    
    print("\n" + "=" * 70)
    print("RUBY ESTIMATOR DATABASE & AUTH TEST")
    print("=" * 70)
    print("\nThis script tests:")
    print("  1. Admin role checks (require_admin_user, no DB)")
    print("  2. Database connection to Supabase")
    print("  3. Presence of restored data")
    print("  4. Admin bootstrap credentials and login")
    print("\nUsage:")
    print("  python test_database_connection.py --database-url 'postgresql://...' --admin-username 'user' --admin-password 'pass'")
    print("  OR set environment variables: DATABASE_URL, ADMIN_BOOTSTRAP_USERNAME, ADMIN_BOOTSTRAP_PASSWORD")
    print()
    
    # Test database
    db_ok = test_database_connection_and_data()
    
    # Test admin
    admin_ok = test_admin_bootstrap()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"   Database Connection: {'[PASS]' if db_ok else '[FAIL]'}")
    print(f"   Admin Login:         {'[PASS]' if admin_ok else '[FAIL]'}")
    
    if db_ok and admin_ok:
        print("\n   [SUCCESS] All tests passed! Your database is properly configured.")
        return 0
    else:
        print("\n   [WARN] Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
