#!/usr/bin/env python3
"""Initialize database schema - creates all required tables."""

import os
import sys

try:
    from persistence import ensure_schema
    from database_config import test_database_connection
except ImportError as e:
    print(f"[ERROR] Failed to import required modules: {e}")
    sys.exit(1)


def main():
    """Initialize the database schema."""
    print("=" * 70)
    print("DATABASE SCHEMA INITIALIZATION")
    print("=" * 70)
    
    # Check database connection first
    print("\n[1] Testing database connection...")
    try:
        success, message = test_database_connection()
        if not success:
            print(f"   [FAIL] {message}")
            print("\n   Make sure DATABASE_URL is set correctly.")
            return 1
        print(f"   [OK] {message}")
    except Exception as e:
        print(f"   [FAIL] Connection failed: {e}")
        return 1
    
    # Initialize schema
    print("\n[2] Creating database schema (tables)...")
    try:
        ensure_schema()
        print("   [OK] Schema initialized successfully!")
        print("\n   All required tables have been created:")
        print("     - users")
        print("     - vehicles")
        print("     - field_values")
        print("     - evidence")
        print("     - runs")
        return 0
    except Exception as e:
        print(f"   [FAIL] Failed to initialize schema: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Allow DATABASE_URL to be passed as command line arg
    if len(sys.argv) > 1:
        os.environ['DATABASE_URL'] = sys.argv[1]
    
    sys.exit(main())
