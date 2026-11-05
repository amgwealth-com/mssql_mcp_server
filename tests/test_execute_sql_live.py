"""Opt-in SQL Server regressions over the real MCP stdio transport.

Run only with MSSQL_RESULT_TESTS=1 and explicit MSSQL_* credentials.
Queries use constants/catalog metadata and session-local table variables only;
no application records or persistent database objects are changed.
"""

import os
import sys

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

pytestmark = pytest.mark.skipif(
    os.getenv("MSSQL_RESULT_TESTS") != "1",
    reason="Opt-in live SQL Server result tests (MSSQL_RESULT_TESTS=1)",
)


@pytest.mark.asyncio
async def test_execute_sql_over_stdio():
    required = ("MSSQL_SERVER", "MSSQL_DATABASE", "MSSQL_USER", "MSSQL_PASSWORD")
    assert all(os.getenv(name) for name in required), "Explicit SQL credentials required"
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mssql_mcp_server"],
        env=dict(os.environ),
    )
    cases = [
        ("SELECT 1 AS n;", ["n\n1"]),
        ("WITH x(n) AS (SELECT 1) SELECT * FROM x;", ["n\n1"]),
        ("/* comment */ ;WITH x(n) AS (SELECT 1) SELECT n FROM x;", ["n\n1"]),
        ("DECLARE @n int = 1; SELECT @n AS n;", ["n\n1"]),
        ("SET NOCOUNT ON; SELECT 1 AS n;", ["n\n1"]),
        ("SELECT 1 AS n WHERE 1=0;", ["n"]),
        ("SELECT 1 AS first; SELECT 2 AS second;", ["first\n1", "second\n2"]),
        (
            "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE 1=0;",
            ["TABLE_SCHEMA,TABLE_NAME"],
        ),
        (
            "SET NOCOUNT OFF; DECLARE @t TABLE(n int); "
            "INSERT INTO @t VALUES (1); SELECT n FROM @t;",
            ["n\n1"],
        ),
        (
            "SET NOCOUNT OFF; DECLARE @t TABLE(n int); INSERT INTO @t VALUES (0); "
            "UPDATE @t SET n=1 OUTPUT inserted.n; SELECT n FROM @t;",
            ["n\n1", "n\n1"],
        ),
        (
            "SET NOCOUNT OFF; DECLARE @t TABLE(n int); "
            ";WITH x AS (SELECT n FROM @t) UPDATE x SET n=1;",
            ["Query executed successfully. Rows affected: 0"],
        ),
    ]
    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for query, expected in cases:
                result = await session.call_tool("execute_sql", {"query": query})
                assert not result.isError
                assert [item.text for item in result.content] == expected, query
