#!/usr/bin/env python3
"""
Utility script to generate password hashes for Railway deployment.
"""

import hashlib
import sys

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_password_hash.py <password>")
        print("Example: python generate_password_hash.py mypassword123")
        sys.exit(1)
    
    password = sys.argv[1]
    password_hash = hash_password(password)
    
    print("=" * 50)
    print("Password Hash for Railway")
    print("=" * 50)
    print(f"Password: {password}")
    print(f"Hash: {password_hash}")
    print("=" * 50)
    print()
    print("Add this to your Railway environment variables:")
    print(f"PASSWORD_HASH={password_hash}")
    print()
    print("Or add it to your local .streamlit/secrets.toml file:")
    print(f'password_hash = "{password_hash}"')

if __name__ == "__main__":
    main() 