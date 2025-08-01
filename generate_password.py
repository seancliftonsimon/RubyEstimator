#!/usr/bin/env python3
"""
Script to generate password hashes for RubyEstimator authentication
"""

import hashlib
import getpass

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def main():
    print("🔐 RubyEstimator Password Generator")
    print("=" * 40)
    
    # Get password from user
    password = getpass.getpass("Enter the password you want to use: ")
    confirm_password = getpass.getpass("Confirm the password: ")
    
    if password != confirm_password:
        print("❌ Passwords don't match!")
        return
    
    if len(password) < 6:
        print("❌ Password must be at least 6 characters long!")
        return
    
    # Generate hash
    password_hash = hash_password(password)
    
    print("\n✅ Password hash generated successfully!")
    print("=" * 40)
    print("Add this to your Railway environment variables:")
    print(f"PASSWORD_HASH = {password_hash}")
    print("\nOr add this to your .streamlit/secrets.toml for local development:")
    print(f'password_hash = "{password_hash}"')
    print("\n🔒 Your password is now ready to use!")

if __name__ == "__main__":
    main() 