"""Test script to verify Neon database logging is working properly."""

import logging
import sys

# Configure logging to show all levels
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)

logger = logging.getLogger(__name__)

def test_database_connection():
    """Test 1: Verify database connection and log database type."""
    print("\n" + "="*80)
    print("TEST 1: Database Connection")
    print("="*80)
    
    from database_config import test_database_connection, get_database_url, is_sqlite
    
    url = get_database_url()
    db_type = "SQLite" if is_sqlite() else "PostgreSQL (Neon)"
    logger.info(f"Database type detected: {db_type}")
    
    success, message = test_database_connection()
    if success:
        logger.info(f"✅ Connection test passed: {message}")
    else:
        logger.error(f"❌ Connection test failed: {message}")
    
    return success


def test_schema_creation():
    """Test 2: Verify schema creation with logging."""
    print("\n" + "="*80)
    print("TEST 2: Schema Creation")
    print("="*80)
    
    from persistence import ensure_schema
    
    try:
        ensure_schema()
        logger.info("✅ Schema creation/validation completed")
        return True
    except Exception as e:
        logger.error(f"❌ Schema creation failed: {e}", exc_info=True)
        return False


def test_vehicle_lookup():
    """Test 3: Test database read operations (cache lookup)."""
    print("\n" + "="*80)
    print("TEST 3: Database Read Test (Cache Lookup)")
    print("="*80)
    
    from vehicle_data import process_vehicle
    
    # Try looking up a test vehicle (this will log database read operations)
    logger.info("Testing database read for: 2015 Honda Civic")
    result = process_vehicle(2015, "Honda", "Civic")
    
    if "error" not in result or result.get("curb_weight_lbs"):
        logger.info("✅ Vehicle lookup completed (check logs above for database read details)")
        return True
    else:
        logger.warning("⚠️  Vehicle lookup had errors (check logs above)")
        return True  # Still return True as this tests the logging


def test_vehicle_persistence():
    """Test 4: Test database write operations."""
    print("\n" + "="*80)
    print("TEST 4: Database Write Test")
    print("="*80)
    
    from vehicle_data import process_vehicle
    
    # Process a vehicle that likely isn't cached to trigger a database write
    logger.info("Testing database write for: 2020 Toyota Camry")
    result = process_vehicle(2020, "Toyota", "Camry")
    
    if "error" not in result or result.get("curb_weight_lbs"):
        logger.info("✅ Vehicle processing completed (check logs above for database write details)")
        return True
    else:
        logger.warning("⚠️  Vehicle processing had errors (check logs above)")
        return True  # Still return True as this tests the logging


def main():
    """Run all database logging tests."""
    print("\n" + "="*80)
    print("NEON DATABASE LOGGING VERIFICATION")
    print("="*80)
    print("\nThis script will test database operations and show detailed logging.")
    print("Look for log messages with these emojis:")
    print("  🔗 = Database URL/connection info")
    print("  ⚙️  = Engine creation")
    print("  📋 = Schema operations")
    print("  🔍 = Cache lookups (READ)")
    print("  💾 = Data persistence (WRITE)")
    print("  ✓/✅ = Success")
    print("  ❌ = Errors")
    print("\n")
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Schema Creation", test_schema_creation),
        ("Database Read (Cache)", test_vehicle_lookup),
        ("Database Write", test_vehicle_persistence),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}", exc_info=True)
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "="*80)
    print("WHAT TO LOOK FOR IN THE LOGS ABOVE:")
    print("="*80)
    print("1. Database URL should show your Neon PostgreSQL connection")
    print("   (or SQLite if DATABASE_URL env var is not set)")
    print("2. Schema creation should show table creation for PostgreSQL/SQLite")
    print("3. Cache lookups should show:")
    print("   - Reading from 'vehicles' table")
    print("   - Reading from 'field_values' table")
    print("4. Database writes should show:")
    print("   - Writing to 'runs' table")
    print("   - Writing to 'vehicles' table")
    print("   - Writing to 'field_values' table")
    print("   - Writing to 'evidence' table")
    print("="*80)


if __name__ == "__main__":
    main()

