#!/usr/bin/env python
"""Test SQL Server connection using the same configuration as the MCP server."""

import os
import sys
import pyodbc

# Add src to path to import our server module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mssql_mcp_server.server import get_db_config

try:
    print("Loading database configuration from environment variables...")
    config = get_db_config()
    
    # Mask sensitive information for display
    display_config = config.copy()
    if 'conn_string' in display_config:
        # Mask password in connection string
        masked_conn_string = display_config['conn_string']
        if 'PWD=' in masked_conn_string:
            parts = masked_conn_string.split(';')
            masked_parts = [p if not p.startswith('PWD=') else 'PWD=***' for p in parts]
            masked_conn_string = ';'.join(masked_parts)
        display_config['conn_string'] = masked_conn_string
    print(f"Configuration:")
    print(f"  Server: {config['server']}")
    print(f"  Database: {config['database']}")
    print(f"  User: {config['user']}")
    
    print("\nAttempting to connect to SQL Server...")
    conn = pyodbc.connect(config['conn_string'])
    cursor = conn.cursor()
    print("Connection successful!")
    
    print("\nTesting query execution...")
    cursor.execute("SELECT TOP 5 TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
    rows = cursor.fetchall()
    print(f"Found {len(rows)} tables:")
    for row in rows:
        print(f"  - {row[0]}")
    
    cursor.close()
    conn.close()
    print("\nConnection test completed successfully!")
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
