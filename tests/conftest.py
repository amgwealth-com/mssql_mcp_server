# tests/conftest.py
import pytest
import os
import pyodbc

@pytest.fixture(scope="session")
def mssql_connection():
    """Create a test database connection."""
    try:
        # Get available ODBC drivers
        drivers = [d for d in pyodbc.drivers() if 'SQL Server' in d]
        if not drivers:
            pytest.skip("No SQL Server ODBC driver found")
        
        driver = drivers[0]
        server = os.getenv("MSSQL_SERVER", "localhost")
        database = os.getenv("MSSQL_DATABASE", "test_db")
        user = os.getenv("MSSQL_USER", "sa")
        password = os.getenv("MSSQL_PASSWORD", "testpassword")
        
        conn_string = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={user};PWD={password}"
        connection = pyodbc.connect(conn_string)
        
        # Create a test table
        cursor = connection.cursor()
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'test_table')
            CREATE TABLE test_table (
                id INT IDENTITY(1,1) PRIMARY KEY,
                name VARCHAR(255),
                value INT
            )
        """)
        connection.commit()
        
        yield connection
        
        # Cleanup
        cursor.execute("DROP TABLE IF EXISTS test_table")
        connection.commit()
        cursor.close()
        connection.close()
            
    except pyodbc.Error as e:
        pytest.fail(f"Failed to connect to SQL Server: {e}")

@pytest.fixture(scope="session")
def mssql_cursor(mssql_connection):
    """Create a test cursor."""
    cursor = mssql_connection.cursor()
    yield cursor
    cursor.close()