# Microsoft SQL Server MCP Server

<!-- [![PyPI](https://img.shields.io/pypi/v/mssql_mcp_server)](https://pypi.org/project/mssql_mcp_server/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) -->

<!-- <a href="https://glama.ai/mcp/servers/29cpe19k30">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/29cpe19k30/badge" alt="Microsoft SQL Server MCP server" />
</a> -->

A Model Context Protocol (MCP) server for secure SQL Server database access through Claude Desktop and Cursor.

## Features

- 🔍 List database tables
- 📊 Execute SQL queries (SELECT, INSERT, UPDATE, DELETE)
- 🔐 Multiple authentication methods
  - SQL Authentication
  - Windows Authentication
  - Entra ID (TODO)
- 🏢 LocalDB and Azure SQL support
- 🔌 Custom port configuration
- 🚀 Uses Microsoft's official ODBC driver via pyodbc

## Prerequisites

You need to have Microsoft's ODBC Driver for SQL Server installed:

- **macOS**: `brew install unixodbc` (ODBC Driver 18 is usually already installed)
- **Linux**: Install `unixodbc` and `msodbcsql18` following [Microsoft's instructions](https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server)
- **Windows**: ODBC Driver is typically pre-installed

## Quick Start

### Install with Claude Desktop / Cursor

Add to your `claude_desktop_config.json` or Cursor settings:

```json
{
  "mcpServers": {
    "mssql": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/amgwealth-com/mssql_mcp_server.git", "mssql_mcp_server"],
      "env": {
        "MSSQL_SERVER": "localhost",
        "MSSQL_DATABASE": "your_database",
        "MSSQL_USER": "your_username",
        "MSSQL_PASSWORD": "your_password"
      }
    }
  }
}
```

## Configuration

### Basic SQL Authentication
```bash
MSSQL_SERVER=localhost          # Required
MSSQL_DATABASE=your_database    # Required
MSSQL_USER=your_username        # Required for SQL auth
MSSQL_PASSWORD=your_password    # Required for SQL auth
```

### Azure SQL Database

TBD

### Optional Settings
```bash
MSSQL_PORT=1433                 # Custom port (default: 1433)
MSSQL_ENCRYPT=true              # Force encryption
```


### Development
```bash
git clone https://github.com/amgwealth-com/mssql_mcp_server.git
cd mssql_mcp_server

# Using uv (recommended)
uv sync

# Or using pip
pip install -e .

# Test the connection
export MSSQL_SERVER="your_server"
export MSSQL_DATABASE="your_database"
export MSSQL_USER="your_username"
export MSSQL_PASSWORD="your_password"

uv run python test_pyodbc_connection.py
```

## Security

- Create a dedicated SQL user with minimal permissions
- Never use admin/sa accounts
- Use Windows Authentication when possible
- Enable encryption for sensitive data

## License

MIT