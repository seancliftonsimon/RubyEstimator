#!/usr/bin/env python3
"""
Test script to verify Railway persistent volume functionality.
Run this script to check if your database persistence is working correctly.
"""

import os
import sqlite3
from datetime import datetime

def test_persistent_volume():
    """Test persistent volume functionality."""
    print("=== RAILWAY PERSISTENT VOLUME DIAGNOSTICS ===")
    
    # Test 1: Environment Information
    print(f"1. Railway Environment: {os.getenv('RAILWAY_ENVIRONMENT', 'Not set')}")
    print(f"2. Current working directory: {os.getcwd()}")
    print(f"3. DATABASE_PATH env var: {os.getenv('DATABASE_PATH', 'Not set')}")
    print(f"4. RAILWAY_PROJECT_ID: {os.getenv('RAILWAY_PROJECT_ID', 'Not set')}")
    print(f"5. RAILWAY_SERVICE_ID: {os.getenv('RAILWAY_SERVICE_ID', 'Not set')}")
    
    # Test 2: Check /data directory
    data_dir = "/data"
    print(f"\n6. /data directory exists: {os.path.exists(data_dir)}")
    if os.path.exists(data_dir):
        print(f"7. /data directory writable: {os.access(data_dir, os.W_OK)}")
        print(f"8. /data directory permissions: {oct(os.stat(data_dir).st_mode)[-3:]}")
        print(f"9. /data directory owner: {os.stat(data_dir).st_uid}")
        print(f"10. /data directory contents: {os.listdir(data_dir)}")
    else:
        print("7. ❌ /data directory does not exist - volume may not be mounted")
        print("   💡 Try creating volume through Railway dashboard")
    
    # Test 3: Check /tmp directory (fallback)
    tmp_dir = "/tmp"
    print(f"\n11. /tmp directory exists: {os.path.exists(tmp_dir)}")
    if os.path.exists(tmp_dir):
        print(f"12. /tmp directory writable: {os.access(tmp_dir, os.W_OK)}")
        print(f"13. /tmp directory permissions: {oct(os.stat(tmp_dir).st_mode)[-3:]}")
        print(f"14. /tmp directory contents: {os.listdir(tmp_dir)}")
    
    # Test 4: Check /app directory
    app_dir = "/app"
    print(f"\n15. /app directory exists: {os.path.exists(app_dir)}")
    if os.path.exists(app_dir):
        print(f"16. /app directory writable: {os.access(app_dir, os.W_OK)}")
        print(f"17. /app directory contents: {os.listdir(app_dir)}")
    
    # Test 5: Write test file to /tmp (fallback)
    test_file = "/tmp/persistent_test.txt"
    test_content = f"Test written at {datetime.now().isoformat()}"
    
    try:
        with open(test_file, 'w') as f:
            f.write(test_content)
        print(f"\n18. ✅ Successfully wrote test file: {test_file}")
        
        # Read it back
        with open(test_file, 'r') as f:
            read_content = f.read()
        
        if read_content == test_content:
            print("19. ✅ Successfully read test file - content matches")
        else:
            print("19. ❌ Test file content doesn't match")
            
    except Exception as e:
        print(f"\n18. ❌ Error writing test file: {e}")
    
    # Test 6: Database operations in /tmp
    db_file = "/tmp/test_vehicle_weights.db"
    try:
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        
        # Create test table
        c.execute("""
            CREATE TABLE IF NOT EXISTS test_vehicles (
                id INTEGER PRIMARY KEY,
                make TEXT,
                model TEXT,
                test_time TEXT
            )
        """)
        
        # Insert test data
        test_time = datetime.now().isoformat()
        c.execute("INSERT INTO test_vehicles (make, model, test_time) VALUES (?, ?, ?)", 
                 ("Test", "Vehicle", test_time))
        
        conn.commit()
        print(f"\n20. ✅ Successfully created and wrote to test database: {db_file}")
        
        # Read test data
        c.execute("SELECT * FROM test_vehicles WHERE make = 'Test'")
        result = c.fetchone()
        if result and result[3] == test_time:
            print("21. ✅ Successfully read from test database - data matches")
        else:
            print("21. ❌ Test database data doesn't match")
        
        conn.close()
        
    except Exception as e:
        print(f"\n20. ❌ Error with database operations: {e}")
    
    # Test 7: Try to create /data directory manually
    print(f"\n22. Attempting to create /data directory manually...")
    try:
        os.makedirs("/data", exist_ok=True)
        if os.path.exists("/data"):
            print("23. ✅ Successfully created /data directory")
            print(f"24. /data directory writable: {os.access('/data', os.W_OK)}")
        else:
            print("23. ❌ Failed to create /data directory")
    except Exception as e:
        print(f"23. ❌ Error creating /data directory: {e}")
    
    print("\n=== DIAGNOSTICS COMPLETE ===")
    print("\n💡 RECOMMENDATIONS:")
    print("1. If /data doesn't exist: Create volume through Railway dashboard")
    print("2. If volume creation fails: Use DATABASE_PATH=/tmp/vehicle_weights.db")
    print("3. If /tmp works: Set environment variable for persistence")

if __name__ == "__main__":
    test_persistent_volume() 