#!/usr/bin/env python3
"""Test pyodbc connection to MSSQL database."""

import os
import sys
import pyodbc

def test_connection():
    """Test database connection with pyodbc."""
    # Get connection details from environment
    server = os.getenv("MSSQL_SERVER", "localhost")
    database = os.getenv("MSSQL_DATABASE")
    user = os.getenv("MSSQL_USER")
    password = os.getenv("MSSQL_PASSWORD")
    port = os.getenv("MSSQL_PORT", "1433")
    
    print(f"Testing connection to:")
    print(f"  Server: {server}")
    print(f"  Port: {port}")
    print(f"  Database: {database}")
    print(f"  User: {user}")
    print()
    
    # Get available drivers
    drivers = [d for d in pyodbc.drivers() if 'SQL Server' in d]
    if not drivers:
        print("ERROR: No SQL Server ODBC driver found!")
        print("Please install ODBC Driver for SQL Server.")
        return False
    
    driver = drivers[0]
    print(f"Using ODBC driver: {driver}")
    print()
    
    # Build connection string
    conn_parts = [f"DRIVER={{{driver}}}"]
    
    if port and port != "1433":
        conn_parts.append(f"SERVER={server},{port}")
    else:
        conn_parts.append(f"SERVER={server}")
    
    conn_parts.append(f"DATABASE={database}")
    conn_parts.append(f"UID={user}")
    conn_parts.append(f"PWD={password}")
    
    # Check for encryption settings
    encrypt_str = os.getenv("MSSQL_ENCRYPT", "false")
    if encrypt_str.lower() == "true":
        conn_parts.append("Encrypt=yes")
        conn_parts.append("TrustServerCertificate=yes")
    
    conn_string = ";".join(conn_parts)
    print(f"Connection string (without password):")
    print(f"  {conn_string.replace(password, '***')}")
    print()
    
    try:
        print("Attempting connection...")
        conn = pyodbc.connect(conn_string)
        print("✓ Connection successful!")
        print()
        
        # Test a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        print(f"SQL Server version:")
        print(f"  {version[:100]}...")
        print()
        
        # List tables
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
        """)
        tables = cursor.fetchall()
        print(f"Found {len(tables)} tables:")
        for table in tables[:10]:  # Show first 10 tables
            print(f"  - {table[0]}")
        if len(tables) > 10:
            print(f"  ... and {len(tables) - 10} more")
        
        cursor.close()
        conn.close()
        print()
        print("✓ All tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Connection failed!")
        print(f"Error: {str(e)}")
        print()
        print("Troubleshooting tips:")
        print("  1. Verify server name and port are correct")
        print("  2. Check firewall settings")
        print("  3. Ensure SQL Server authentication is enabled")
        print("  4. Verify username and password are correct")
        return False

if __name__ == "__main__":
    if not os.getenv("MSSQL_DATABASE"):
        print("Please set environment variables:")
        print("  MSSQL_SERVER")
        print("  MSSQL_DATABASE")
        print("  MSSQL_USER")
        print("  MSSQL_PASSWORD")
        print("  MSSQL_PORT (optional, default: 1433)")
        print("  MSSQL_ENCRYPT (optional, default: false)")
        sys.exit(1)
    
    success = test_connection()
    sys.exit(0 if success else 1)
