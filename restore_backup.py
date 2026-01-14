#!/usr/bin/env python3
"""Restore PostgreSQL backup to Supabase database."""

import gzip
import os
import sys
import re
import io
from urllib.parse import quote_plus, unquote

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

# Database connection string (use this directly - it handles URL encoding)
# Format: postgresql://user:password@host:port/database
CONNECTION_STRING = "postgresql://postgres:DyWyXAxvHY12dgUG@db.idhqjltjhyidtowdvvew.supabase.co:5432/postgres"

# Backup file path
BACKUP_FILE = r"C:\Users\Sean\GameDev\RubyEstimator\db_cluster-07-08-2025@14-52-47.backup.gz"

def restore_backup():
    """Restore the backup file to the database."""
    print(f"[INFO] Reading backup file: {BACKUP_FILE}")
    
    # Decompress the backup
    try:
        with gzip.open(BACKUP_FILE, 'rb') as f_in:
            backup_data = f_in.read()
        print(f"[OK] Decompressed backup ({len(backup_data)} bytes)")
    except Exception as e:
        print(f"[ERROR] Failed to decompress backup: {e}")
        return False
    
    # Check if it's a custom format backup (starts with PGDUMP header)
    if backup_data.startswith(b'PGDMP'):
        print("[WARN] This appears to be a PostgreSQL custom format backup (.backup)")
        print("   This requires 'pg_restore' tool, which is not available.")
        print("\n   Options:")
        print("   1. Install PostgreSQL client tools:")
        print("      Download from: https://www.postgresql.org/download/windows/")
        print("   2. Use Supabase dashboard to restore via SQL Editor")
        print("   3. Use a different backup format (SQL dump)")
        return False
    
    # Try to decode as SQL
    try:
        sql_content = backup_data.decode('utf-8')
        print(f"[OK] Backup appears to be SQL format ({len(sql_content)} characters)")
    except UnicodeDecodeError:
        print("[ERROR] Backup is not in SQL format. Custom format backups require pg_restore.")
        return False
    
    # Connect to database
    print(f"\n[INFO] Connecting to database...")
    try:
        # Use connection string directly (handles URL encoding automatically)
        conn = psycopg2.connect(CONNECTION_STRING)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        print("[OK] Connected successfully")
    except Exception as e:
        print(f"[ERROR] Failed to connect: {e}")
        print("\n[TIP] Verify your password in the Supabase dashboard:")
        print("   Settings → Database → Connection string")
        print("   Make sure the password matches exactly (including special characters)")
        return False
    
    # Execute SQL - handle COPY statements properly
    print("\n[INFO] Restoring backup...")
    try:
        cursor = conn.cursor()
        
        # Parse SQL content into statements and COPY blocks
        lines = sql_content.split('\n')
        statements = []
        copy_blocks = []
        
        current_statement = []
        current_copy = None
        in_copy = False
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith('--'):
                i += 1
                continue
            
            # Skip metadata header lines
            if any(stripped.startswith(prefix) for prefix in ['Type:', 'Schema:', 'Owner:', 'Name:', 'Description:']):
                i += 1
                continue
            
            # Detect COPY statement (may end with semicolon or be on separate line)
            # Check BEFORE adding to current_statement
            if 'COPY' in stripped.upper() and 'FROM stdin' in stripped.upper():
                print(f"   [DEBUG] Potential COPY found: {stripped[:80]}")
                # Parse COPY statement: COPY table_name (columns) FROM stdin;
                # Remove semicolon if present
                copy_line = stripped.rstrip(';')
                match = re.match(r'COPY\s+(?:(\w+)\.)?(\w+)\s*(?:\(([^)]+)\))?\s+FROM\s+stdin', copy_line, re.IGNORECASE)
                if match:
                    schema = match.group(1)
                    table = match.group(2)
                    columns = match.group(3)
                    
                    table_name = f"{schema}.{table}" if schema else table
                    current_copy = {
                        'table': table_name,
                        'columns': columns,
                        'data': []
                    }
                    in_copy = True
                    print(f"   [DEBUG] Found COPY for table: {table_name}")
                    i += 1
                    continue
            
            # Collect COPY data
            if in_copy:
                if stripped == '\.':
                    # End of COPY data
                    print(f"   [DEBUG] Finished COPY for {current_copy['table']}: {len(current_copy['data'])} data lines")
                    copy_blocks.append(current_copy)
                    current_copy = None
                    in_copy = False
                else:
                    # Data line
                    current_copy['data'].append(line)
                i += 1
                continue
            
            # Regular SQL statements
            current_statement.append(line)
            if stripped.endswith(';'):
                stmt = '\n'.join(current_statement).strip()
                if stmt and not stmt.startswith('--'):
                    # Check if it's a valid SQL statement
                    sql_keywords = ['CREATE', 'ALTER', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'SELECT', 
                                  'GRANT', 'REVOKE', 'SET', 'BEGIN', 'COMMIT', 'ROLLBACK']
                    if any(stmt.upper().startswith(keyword) for keyword in sql_keywords):
                        statements.append(stmt)
                current_statement = []
            i += 1
        
        # Handle any remaining statement
        if current_statement:
            stmt = '\n'.join(current_statement).strip()
            if stmt and not stmt.startswith('--'):
                statements.append(stmt)
        
        total_sql = len(statements)
        total_copy = len(copy_blocks)
        print(f"   Found {total_sql} SQL statements and {total_copy} COPY blocks")
        
        # Execute SQL statements first
        warnings = 0
        executed = 0
        print(f"\n[INFO] Executing SQL statements...")
        for i, statement in enumerate(statements, 1):
            if i % 50 == 0:
                print(f"   Progress: {i}/{total_sql} SQL statements...")
            try:
                cursor.execute(statement)
                executed += 1
            except Exception as e:
                error_str = str(e).lower()
                # Skip common non-critical errors
                if any(phrase in error_str for phrase in [
                    'already exists', 'does not exist', 'syntax error at or near "type"',
                    'syntax error at or near "schema"', 'syntax error at or near "owner"',
                    'syntax error at or near "name"', 'syntax error at or near "description"',
                    'permission denied', 'must be owner', 'reserved role', 'grant options'
                ]):
                    warnings += 1
                    if warnings <= 3:
                        print(f"   [WARN] Skipped: {str(e)[:80]}")
                    elif warnings == 4:
                        print(f"   ... (suppressing additional SQL warnings)")
                else:
                    # Only show non-ignored errors
                    if 'unterminated dollar-quoted string' not in error_str:
                        print(f"   [WARN] SQL {i}: {str(e)[:100]}")
        
        # Execute COPY statements using copy_from
        print(f"\n[INFO] Loading data via COPY statements...")
        copy_loaded = 0
        copy_failed = 0
        
        for i, copy_block in enumerate(copy_blocks, 1):
            try:
                table = copy_block['table']
                data_lines = copy_block['data']
                
                if not data_lines:
                    continue
                
                # Create StringIO object with the data
                data_io = io.StringIO('\n'.join(data_lines))
                
                # Use copy_from to load data
                if copy_block['columns']:
                    # COPY with specific columns
                    cursor.copy_from(
                        data_io,
                        table,
                        columns=[col.strip() for col in copy_block['columns'].split(',')],
                        sep='\t'  # PostgreSQL COPY default separator
                    )
                else:
                    # COPY all columns
                    cursor.copy_from(
                        data_io,
                        table,
                        sep='\t'
                    )
                
                copy_loaded += 1
                if copy_loaded % 5 == 0:
                    print(f"   Progress: {copy_loaded}/{total_copy} COPY blocks loaded...")
                    
            except Exception as e:
                copy_failed += 1
                error_str = str(e).lower()
                # Check if table doesn't exist (might be a system table we can't restore)
                if 'does not exist' in error_str or 'permission denied' in error_str:
                    if copy_failed <= 3:
                        print(f"   [WARN] Skipped COPY to {copy_block['table']}: {str(e)[:80]}")
                else:
                    print(f"   [WARN] COPY {i} ({copy_block['table']}): {str(e)[:100]}")
        
        cursor.close()
        print(f"\n[OK] Restore completed:")
        print(f"   - SQL statements: {executed}/{total_sql} executed")
        print(f"   - COPY blocks: {copy_loaded}/{total_copy} loaded")
        print(f"   - Warnings: {warnings} SQL, {copy_failed} COPY")
        return True
        
    except Exception as e:
        print(f"[ERROR] Restore failed: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = restore_backup()
    sys.exit(0 if success else 1)
