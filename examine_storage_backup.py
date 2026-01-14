#!/usr/bin/env python3
"""Examine Supabase storage backup zip file structure."""

import os
import zipfile
import json
from pathlib import Path

STORAGE_BACKUP_FILE = r"C:\Users\Sean\GameDev\RubyEstimator\wlqozdiatwixejdgjaux.storage.zip"


def main():
    """Examine the storage backup."""
    print("=" * 70)
    print("EXAMINING STORAGE BACKUP")
    print("=" * 70)
    
    if not os.path.exists(STORAGE_BACKUP_FILE):
        print(f"[ERROR] File not found: {STORAGE_BACKUP_FILE}")
        return 1
    
    print(f"\n[INFO] Reading: {STORAGE_BACKUP_FILE}")
    file_size = os.path.getsize(STORAGE_BACKUP_FILE)
    print(f"[INFO] File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
    
    try:
        with zipfile.ZipFile(STORAGE_BACKUP_FILE, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            print(f"[OK] Found {len(file_list)} items in zip")
            
            # Categorize items
            buckets = []
            objects = []
            metadata_files = []
            directories = []
            
            for item in file_list:
                if item.endswith('/'):
                    directories.append(item)
                elif 'bucket' in item.lower() and item.endswith('.json'):
                    buckets.append(item)
                elif item.endswith('.json'):
                    metadata_files.append(item)
                else:
                    objects.append(item)
            
            print(f"\n[INFO] Structure breakdown:")
            print(f"   - Directories: {len(directories)}")
            print(f"   - Bucket definitions: {len(buckets)}")
            print(f"   - Metadata files: {len(metadata_files)}")
            print(f"   - Storage objects: {len(objects)}")
            
            # Show bucket definitions
            if buckets:
                print(f"\n[INFO] Bucket definitions found:")
                for bucket_file in buckets:
                    try:
                        content = zip_ref.read(bucket_file).decode('utf-8')
                        bucket_data = json.loads(content)
                        print(f"   - {bucket_file}")
                        print(f"     Name: {bucket_data.get('name', 'N/A')}")
                        print(f"     Public: {bucket_data.get('public', 'N/A')}")
                    except Exception as e:
                        print(f"   - {bucket_file} (could not parse: {e})")
            
            # Show sample objects
            if objects:
                print(f"\n[INFO] Sample storage objects (first 20):")
                total_size = 0
                for i, obj in enumerate(objects[:20]):
                    try:
                        info = zip_ref.getinfo(obj)
                        size = info.file_size
                        total_size += size
                        print(f"   {i+1}. {obj} ({size:,} bytes)")
                    except:
                        print(f"   {i+1}. {obj}")
                
                if len(objects) > 20:
                    print(f"   ... and {len(objects) - 20} more objects")
                
                # Calculate total size
                for obj in objects[20:]:
                    try:
                        total_size += zip_ref.getinfo(obj).file_size
                    except:
                        pass
                
                print(f"\n[INFO] Total storage size: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)")
            
            # Show metadata files
            if metadata_files:
                print(f"\n[INFO] Metadata files:")
                for meta in metadata_files[:10]:
                    print(f"   - {meta}")
                if len(metadata_files) > 10:
                    print(f"   ... and {len(metadata_files) - 10} more")
            
            # Show directory structure
            if directories:
                print(f"\n[INFO] Directory structure:")
                unique_dirs = sorted(set(directories))
                for dir_path in unique_dirs[:20]:
                    print(f"   - {dir_path}")
                if len(unique_dirs) > 20:
                    print(f"   ... and {len(unique_dirs) - 20} more directories")
            
            return 0
            
    except Exception as e:
        print(f"[ERROR] Failed to read zip file: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
