#!/usr/bin/env python3
"""Restore Supabase storage objects from backup zip file."""

import os
import sys
import zipfile
import json
from pathlib import Path

try:
    from supabase import create_client, Client
except ImportError:
    print("[ERROR] supabase-py not installed. Run: pip install supabase")
    sys.exit(1)

# Storage backup file path
STORAGE_BACKUP_FILE = r"C:\Users\Sean\GameDev\RubyEstimator\wlqozdiatwixejdgjaux.storage.zip"

# Supabase credentials (you'll need to set these)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")  # Service role key for admin access


def examine_storage_backup():
    """Examine the structure of the storage backup zip file."""
    print("=" * 70)
    print("EXAMINING STORAGE BACKUP")
    print("=" * 70)
    
    if not os.path.exists(STORAGE_BACKUP_FILE):
        print(f"[ERROR] Storage backup file not found: {STORAGE_BACKUP_FILE}")
        return None
    
    print(f"\n[INFO] Reading storage backup: {STORAGE_BACKUP_FILE}")
    
    try:
        with zipfile.ZipFile(STORAGE_BACKUP_FILE, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            print(f"[OK] Found {len(file_list)} items in backup")
            
            # Group by type
            buckets = []
            objects = []
            metadata = []
            
            for item in file_list:
                if item.endswith('/'):
                    continue
                elif 'bucket' in item.lower() or item.endswith('.json'):
                    if 'bucket' in item.lower():
                        buckets.append(item)
                    else:
                        metadata.append(item)
                else:
                    objects.append(item)
            
            print(f"\n[INFO] Backup structure:")
            print(f"   - Bucket definitions: {len(buckets)}")
            print(f"   - Storage objects: {len(objects)}")
            print(f"   - Metadata files: {len(metadata)}")
            
            # Show first few items
            print(f"\n[INFO] Sample items:")
            for item in file_list[:10]:
                size = zip_ref.getinfo(item).file_size if not item.endswith('/') else 0
                print(f"   - {item} ({size} bytes)")
            
            if len(file_list) > 10:
                print(f"   ... and {len(file_list) - 10} more items")
            
            return {
                'zip_file': STORAGE_BACKUP_FILE,
                'items': file_list,
                'buckets': buckets,
                'objects': objects,
                'metadata': metadata
            }
            
    except Exception as e:
        print(f"[ERROR] Failed to read storage backup: {e}")
        import traceback
        traceback.print_exc()
        return None


def restore_storage_objects(backup_info):
    """Restore storage objects to Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("\n[ERROR] Supabase credentials not set!")
        print("   Please set environment variables:")
        print("   - SUPABASE_URL (e.g., https://your-project.supabase.co)")
        print("   - SUPABASE_SERVICE_ROLE_KEY (service role key from Supabase dashboard)")
        return False
    
    print("\n" + "=" * 70)
    print("RESTORING STORAGE OBJECTS")
    print("=" * 70)
    
    try:
        # Initialize Supabase client
        print(f"\n[INFO] Connecting to Supabase: {SUPABASE_URL}")
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[OK] Connected successfully")
        
        # Extract and restore
        with zipfile.ZipFile(backup_info['zip_file'], 'r') as zip_ref:
            # First, restore bucket definitions if any
            bucket_defs = {}
            for bucket_file in backup_info['buckets']:
                try:
                    content = zip_ref.read(bucket_file).decode('utf-8')
                    bucket_data = json.loads(content)
                    bucket_defs[bucket_data.get('name')] = bucket_data
                    print(f"[INFO] Found bucket definition: {bucket_data.get('name')}")
                except Exception as e:
                    print(f"[WARN] Could not parse bucket file {bucket_file}: {e}")
            
            # Restore objects
            restored = 0
            failed = 0
            
            for obj_path in backup_info['objects']:
                try:
                    # Parse object path (format may vary)
                    # Typical: bucket_name/path/to/file.ext
                    parts = obj_path.split('/', 1)
                    if len(parts) < 2:
                        print(f"[WARN] Skipping invalid path: {obj_path}")
                        failed += 1
                        continue
                    
                    bucket_name = parts[0]
                    file_path = parts[1]
                    
                    # Read file data
                    file_data = zip_ref.read(obj_path)
                    
                    # Upload to Supabase storage
                    print(f"[INFO] Restoring: {bucket_name}/{file_path} ({len(file_data)} bytes)")
                    response = supabase.storage.from_(bucket_name).upload(
                        path=file_path,
                        file=file_data,
                        file_options={"upsert": True}  # Overwrite if exists
                    )
                    
                    if response:
                        restored += 1
                        if restored % 10 == 0:
                            print(f"   Progress: {restored} objects restored...")
                    else:
                        failed += 1
                        print(f"[WARN] Failed to restore: {obj_path}")
                        
                except Exception as e:
                    failed += 1
                    print(f"[WARN] Error restoring {obj_path}: {e}")
            
            print(f"\n[OK] Restore completed:")
            print(f"   - Restored: {restored} objects")
            print(f"   - Failed: {failed} objects")
            return restored > 0
            
    except Exception as e:
        print(f"[ERROR] Failed to restore storage: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    print("\n" + "=" * 70)
    print("SUPABASE STORAGE RESTORATION")
    print("=" * 70)
    print("\nThis script will:")
    print("  1. Examine the storage backup zip file")
    print("  2. Restore storage objects to your Supabase project")
    print()
    
    # Examine backup first
    backup_info = examine_storage_backup()
    if not backup_info:
        return 1
    
    # Ask if user wants to proceed with restore
    print("\n" + "=" * 70)
    response = input("Do you want to proceed with restoring storage objects? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("[INFO] Restoration cancelled.")
        return 0
    
    # Restore
    success = restore_storage_objects(backup_info)
    
    if success:
        print("\n[SUCCESS] Storage restoration completed!")
        return 0
    else:
        print("\n[WARN] Storage restoration had issues. Check output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
