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
    print("=== RAILWAY PERSISTENT VOLUME TEST ===")
    
    # Test 1: Check environment
    print(f"1. Railway Environment: {os.getenv('RAILWAY_ENVIRONMENT', 'Not set')}")
    print(f"2. Current working directory: {os.getcwd()}")
    
    # Test 2: Check /data directory
    data_dir = "/data"
    print(f"3. /data directory exists: {os.path.exists(data_dir)}")
    if os.path.exists(data_dir):
        print(f"4. /data directory writable: {os.access(data_dir, os.W_OK)}")
        print(f"5. /data directory contents: {os.listdir(data_dir)}")
    
    # Test 3: Write test file
    test_file = "/data/persistent_test.txt"
    test_content = f"Test written at {datetime.now().isoformat()}"
    
    try:
        with open(test_file, 'w') as f:
            f.write(test_content)
        print(f"6. ✅ Successfully wrote test file: {test_file}")
        
        # Read it back
        with open(test_file, 'r') as f:
            read_content = f.read()
        
        if read_content == test_content:
            print("7. ✅ Successfully read test file - content matches")
        else:
            print("7. ❌ Test file content doesn't match")
            
    except Exception as e:
        print(f"6. ❌ Error writing test file: {e}")
    
    # Test 4: Database operations
    db_file = "/data/test_vehicle_weights.db"
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
        print(f"8. ✅ Successfully created and wrote to test database: {db_file}")
        
        # Read test data
        c.execute("SELECT * FROM test_vehicles WHERE make = 'Test'")
        result = c.fetchone()
        if result and result[3] == test_time:
            print("9. ✅ Successfully read from test database - data matches")
        else:
            print("9. ❌ Test database data doesn't match")
        
        conn.close()
        
    except Exception as e:
        print(f"8. ❌ Error with database operations: {e}")
    
    print("=== TEST COMPLETE ===")

if __name__ == "__main__":
    test_persistent_volume() 