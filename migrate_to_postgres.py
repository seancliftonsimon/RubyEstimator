"""
Migration script to transfer data from SQLite to PostgreSQL.

Usage:
    1. Set DATABASE_URL in your .env file to your PostgreSQL connection string
    2. Run: python migrate_to_postgres.py
"""

import os
import sqlite3
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect, MetaData, Table
from pathlib import Path
import sys

# Load environment variables
load_dotenv()

# Get database URLs
sqlite_path = Path(__file__).parent / "rubyestimator_local.db"
sqlite_url = f"sqlite:///{sqlite_path}"
postgres_url = os.getenv("DATABASE_URL")

if not postgres_url:
    print("❌ ERROR: DATABASE_URL not found in environment variables!")
    print("Please set DATABASE_URL in your .env file to your PostgreSQL connection string.")
    sys.exit(1)

if postgres_url.startswith("sqlite"):
    print("❌ ERROR: DATABASE_URL is pointing to SQLite, not PostgreSQL!")
    print("Please update DATABASE_URL to your PostgreSQL connection string.")
    sys.exit(1)

print("🔄 Starting Migration from SQLite to PostgreSQL")
print("="*60)

# Create engines
sqlite_engine = create_engine(sqlite_url)
postgres_engine = create_engine(postgres_url)

# Check if SQLite database exists
if not sqlite_path.exists():
    print(f"❌ ERROR: SQLite database not found at {sqlite_path}")
    sys.exit(1)

print(f"✓ SQLite database found: {sqlite_path}")
print(f"✓ PostgreSQL URL configured")
print()

# Get table names from SQLite
sqlite_inspector = inspect(sqlite_engine)
tables = sqlite_inspector.get_table_names()

if not tables:
    print("⚠️  WARNING: No tables found in SQLite database!")
    print("Nothing to migrate.")
    sys.exit(0)

print(f"📊 Found {len(tables)} table(s) to migrate:")
for table in tables:
    with sqlite_engine.connect() as conn:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
    print(f"   - {table}: {count} rows")
print()

# Ask for confirmation
response = input("Do you want to proceed with migration? (yes/no): ")
if response.lower() not in ['yes', 'y']:
    print("Migration cancelled.")
    sys.exit(0)

print()
print("🚀 Starting migration...")
print("="*60)

# Reflect SQLite schema
metadata = MetaData()
metadata.reflect(bind=sqlite_engine)

# Migrate each table
total_rows_migrated = 0

for table_name in tables:
    print(f"\n📦 Migrating table: {table_name}")
    
    table = Table(table_name, metadata, autoload_with=sqlite_engine)
    
    # Create table in PostgreSQL (using SQLAlchemy metadata)
    try:
        table.create(postgres_engine, checkfirst=True)
        print(f"   ✓ Table structure created in PostgreSQL")
    except Exception as e:
        print(f"   ⚠️  Table may already exist: {e}")
    
    # Get data from SQLite
    with sqlite_engine.connect() as sqlite_conn:
        result = sqlite_conn.execute(table.select())
        rows = result.fetchall()
        columns = result.keys()
    
    if not rows:
        print(f"   ⚠️  No data to migrate")
        continue
    
    # Insert data into PostgreSQL
    try:
        with postgres_engine.connect() as postgres_conn:
            # Convert rows to dictionaries
            data_dicts = [dict(zip(columns, row)) for row in rows]
            
            # Insert in batches
            batch_size = 100
            for i in range(0, len(data_dicts), batch_size):
                batch = data_dicts[i:i + batch_size]
                postgres_conn.execute(table.insert(), batch)
            
            postgres_conn.commit()
        
        total_rows_migrated += len(rows)
        print(f"   ✓ Migrated {len(rows)} rows")
    
    except Exception as e:
        print(f"   ❌ Error migrating data: {e}")
        print(f"   Attempting row-by-row migration...")
        
        # Try row by row (slower but more error-tolerant)
        success_count = 0
        with postgres_engine.connect() as postgres_conn:
            for row_dict in data_dicts:
                try:
                    postgres_conn.execute(table.insert(), [row_dict])
                    success_count += 1
                except Exception as row_error:
                    print(f"      ⚠️  Skipped row: {row_error}")
            postgres_conn.commit()
        
        total_rows_migrated += success_count
        print(f"   ✓ Migrated {success_count}/{len(rows)} rows")

print()
print("="*60)
print(f"✅ Migration Complete!")
print(f"   Total rows migrated: {total_rows_migrated}")
print()

# Verify migration
print("🔍 Verifying migration...")
postgres_inspector = inspect(postgres_engine)
postgres_tables = postgres_inspector.get_table_names()

print(f"   PostgreSQL now has {len(postgres_tables)} table(s):")
for table in postgres_tables:
    with postgres_engine.connect() as conn:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
    print(f"   - {table}: {count} rows")

print()
print("🎉 Migration successful!")
print()
print("Next steps:")
print("1. Update your Streamlit secrets with the PostgreSQL credentials")
print("2. Test your app locally with: streamlit run app.py")
print("3. Deploy to Streamlit Cloud")

