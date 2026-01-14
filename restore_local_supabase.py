#!/usr/bin/env python3
"""Helper script to prepare and restore Supabase backup locally."""

import os
import sys
import gzip
import subprocess
from pathlib import Path

# Backup file paths
BACKUP_GZ = r"C:\Users\Sean\GameDev\RubyEstimator\db_cluster-07-08-2025@14-52-47.backup.gz"
BACKUP_DECOMPRESSED = r"C:\Users\Sean\GameDev\RubyEstimator\db_cluster.backup"
PROJECT_DIR = r"C:\Users\Sean\GameDev\RubyEstimator"


def check_supabase_cli():
    """Check if Supabase CLI is installed."""
    try:
        result = subprocess.run(['supabase', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"[OK] Supabase CLI found: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[ERROR] Supabase CLI not found!")
        print("\n   Please install Supabase CLI:")
        print("   https://supabase.com/docs/guides/cli/getting-started")
        return False


def decompress_backup():
    """Decompress the .gz backup file."""
    print("=" * 70)
    print("DECOMPRESSING BACKUP FILE")
    print("=" * 70)
    
    if not os.path.exists(BACKUP_GZ):
        print(f"[ERROR] Backup file not found: {BACKUP_GZ}")
        return False
    
    if os.path.exists(BACKUP_DECOMPRESSED):
        print(f"[INFO] Decompressed backup already exists: {BACKUP_DECOMPRESSED}")
        response = input("   Overwrite? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("[INFO] Using existing decompressed file.")
            return True
    
    print(f"\n[INFO] Decompressing: {BACKUP_GZ}")
    try:
        with gzip.open(BACKUP_GZ, 'rb') as f_in:
            with open(BACKUP_DECOMPRESSED, 'wb') as f_out:
                f_out.write(f_in.read())
        
        size = os.path.getsize(BACKUP_DECOMPRESSED)
        print(f"[OK] Decompressed to: {BACKUP_DECOMPRESSED}")
        print(f"[INFO] Size: {size:,} bytes ({size / 1024 / 1024:.2f} MB)")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to decompress: {e}")
        return False


def init_supabase_project():
    """Initialize Supabase project if not already initialized."""
    print("\n" + "=" * 70)
    print("INITIALIZING SUPABASE PROJECT")
    print("=" * 70)
    
    supabase_dir = os.path.join(PROJECT_DIR, 'supabase')
    if os.path.exists(supabase_dir):
        print(f"[INFO] Supabase project already exists at: {supabase_dir}")
        response = input("   Re-initialize? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            return True
    
    print(f"\n[INFO] Initializing Supabase project in: {PROJECT_DIR}")
    try:
        os.chdir(PROJECT_DIR)
        result = subprocess.run(['supabase', 'init'], 
                              capture_output=True, text=True, check=True)
        print("[OK] Supabase project initialized")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to initialize: {e.stderr}")
        return False
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False


def set_postgres_version():
    """Set PostgreSQL version for restore."""
    print("\n[INFO] Setting PostgreSQL version to 15.6.1.115")
    try:
        temp_dir = os.path.join(PROJECT_DIR, 'supabase', '.temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        version_file = os.path.join(temp_dir, 'postgres-version')
        with open(version_file, 'w') as f:
            f.write('15.6.1.115')
        
        print(f"[OK] Version file created: {version_file}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to set version: {e}")
        return False


def restore_database():
    """Restore database from backup."""
    print("\n" + "=" * 70)
    print("RESTORING DATABASE FROM BACKUP")
    print("=" * 70)
    
    backup_path = os.path.join(PROJECT_DIR, 'db_cluster.backup')
    if not os.path.exists(backup_path):
        print(f"[ERROR] Backup file not found: {backup_path}")
        return False
    
    print(f"\n[INFO] Starting database restore from: {backup_path}")
    print("[INFO] This may take several minutes...")
    
    try:
        os.chdir(PROJECT_DIR)
        # Use relative path for backup
        result = subprocess.run(
            ['supabase', 'db', 'start', '--from-backup', 'db_cluster.backup'],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            print("[OK] Database restored successfully!")
            print("\n[INFO] You can now connect with:")
            print("   psql 'postgresql://postgres:postgres@localhost:54322/postgres'")
            return True
        else:
            print(f"[ERROR] Restore failed:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"[ERROR] Error during restore: {e}")
        return False


def main():
    """Main function."""
    print("=" * 70)
    print("SUPABASE LOCAL DATABASE RESTORE")
    print("=" * 70)
    print("\nThis script will:")
    print("  1. Check for Supabase CLI")
    print("  2. Decompress the backup file")
    print("  3. Initialize Supabase project")
    print("  4. Set PostgreSQL version")
    print("  5. Restore database from backup")
    print()
    
    # Check CLI
    if not check_supabase_cli():
        return 1
    
    # Decompress backup
    if not decompress_backup():
        return 1
    
    # Initialize project
    if not init_supabase_project():
        return 1
    
    # Set version
    if not set_postgres_version():
        return 1
    
    # Restore
    print("\n" + "=" * 70)
    response = input("Ready to restore database. Continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("[INFO] Restore cancelled.")
        return 0
    
    if restore_database():
        print("\n[SUCCESS] Local database restore completed!")
        print("\nNext steps:")
        print("  1. Verify data: psql 'postgresql://postgres:postgres@localhost:54322/postgres'")
        print("  2. Start full stack: supabase stop && supabase start")
        print("  3. Extract data and restore to new Supabase project")
        return 0
    else:
        print("\n[ERROR] Restore failed. Check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
