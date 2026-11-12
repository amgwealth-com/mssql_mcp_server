"""Result handling regressions; no live database or credentials required."""

from unittest.mock import Mock

import pytest

from mssql_mcp_server import server


@pytest.fixture
def database(monkeypatch):
    cursor = Mock()
    cursor.description = [("n",)]
    cursor.fetchall.return_value = [(1,)]
    cursor.rowcount = -1
    cursor.nextset.return_value = None
    connection = Mock()
    connection.cursor.return_value = cursor
    monkeypatch.setattr(server.pyodbc, "connect", Mock(return_value=connection))
    return connection, cursor


@pytest.mark.asyncio
async def test_cte_returns_rows(database):
    connection, cursor = database
    query = "WITH x(n) AS (SELECT 1) SELECT * FROM x;"

    result = await server._tool_execute_sql("unused", "testdb", query)

    assert [item.text for item in result] == ["n\n1"]
    cursor.execute.assert_called_once_with(query)
    cursor.close.assert_called_once()
    connection.close.assert_called_once()


@pytest.mark.asyncio
async def test_output_rows_are_returned_and_write_is_committed(database):
    connection, cursor = database
    query = "UPDATE example SET n = 1 OUTPUT inserted.n;"

    result = await server._tool_execute_sql("unused", "testdb", query)

    assert [item.text for item in result] == ["n\n1"]
    connection.commit.assert_called_once()


@pytest.mark.asyncio
async def test_skips_rowcount_tokens_to_fetch_later_result_set(database):
    connection, cursor = database
    cursor.description = None
    cursor.rowcount = 2

    def advance():
        cursor.description = [("n",)]
        cursor.rowcount = -1
        cursor.nextset.return_value = None
        cursor.nextset.side_effect = None
        return True

    cursor.nextset.side_effect = advance
    query = "SET NOCOUNT OFF; DECLARE @n int = 1; SELECT @n AS n;"

    result = await server._tool_execute_sql("unused", "testdb", query)

    assert [item.text for item in result] == ["n\n1"]
    connection.commit.assert_called_once()
    assert cursor.nextset.call_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("stage", ["execute", "fetchall", "nextset", "commit"])
async def test_failures_roll_back_and_close_resources(database, stage):
    connection, cursor = database
    target = connection if stage == "commit" else cursor
    getattr(target, stage).side_effect = RuntimeError("synthetic failure")

    result = await server._tool_execute_sql("unused", "testdb", "SELECT 1 AS n")

    assert [item.text for item in result] == ["Error executing query: synthetic failure"]
    connection.rollback.assert_called_once()
    if stage != "commit":
        connection.commit.assert_not_called()
    cursor.close.assert_called_once()
    connection.close.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("query", [
    "SELECT 1 AS n;",
    "/* comment */ -- comment\nWITH x(n) AS (SELECT 1) SELECT n FROM x;",
    ";WITH x(n) AS (SELECT 1) SELECT n FROM x;",
    "DECLARE @n int = 1; SELECT @n AS n;",
    "SET NOCOUNT ON; SELECT 1 AS n;",
    "EXEC example_procedure;",
])
async def test_result_metadata_not_first_keyword_controls_fetching(database, query):
    connection, cursor = database
    result = await server._tool_execute_sql("unused", "testdb", query)
    assert [item.text for item in result] == ["n\n1"]
    cursor.execute.assert_called_once_with(query)
    connection.commit.assert_called_once()


@pytest.mark.asyncio
async def test_empty_result_preserves_column_headers(database):
    _, cursor = database
    cursor.fetchall.return_value = []
    result = await server._tool_execute_sql("unused", "testdb", "SELECT 1 AS n WHERE 1=0;")
    assert [item.text for item in result] == ["n"]


@pytest.mark.asyncio
async def test_information_schema_results_preserve_all_columns(database):
    _, cursor = database
    cursor.description = [("TABLE_SCHEMA",), ("TABLE_NAME",)]
    cursor.fetchall.return_value = [("dbo", "example")]
    result = await server._tool_execute_sql(
        "unused", "testdb", "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES;"
    )
    assert [item.text for item in result] == ["TABLE_SCHEMA,TABLE_NAME\ndbo,example"]


@pytest.mark.asyncio
@pytest.mark.parametrize("query", [
    "INSERT INTO example(n) VALUES (1);",
    "UPDATE example SET n=1;",
    "DELETE FROM example;",
    "WITH x AS (SELECT n FROM example) UPDATE x SET n=1;",
    "SELECT n INTO example_copy FROM example;",
])
async def test_no_result_writes_still_commit_and_report_rowcount(database, query):
    connection, cursor = database
    cursor.description = None
    cursor.rowcount = 2
    result = await server._tool_execute_sql("unused", "testdb", query)
    assert [item.text for item in result] == ["Query executed successfully. Rows affected: 2"]
    connection.commit.assert_called_once()
    cursor.fetchall.assert_not_called()


@pytest.mark.asyncio
async def test_multiple_result_sets_are_returned_in_order_before_commit(database):
    connection, cursor = database

    def advance():
        cursor.description = [("second",)]
        cursor.fetchall.return_value = [(2,)]
        cursor.nextset.side_effect = None
        return True

    cursor.nextset.side_effect = advance
    connection.commit.side_effect = lambda: (
        cursor.nextset.call_count == 2 or pytest.fail("Committed before draining results")
    )
    result = await server._tool_execute_sql("unused", "testdb", "SELECT 1 AS n; SELECT 2 AS second;")
    assert [item.text for item in result] == ["n\n1", "second\n2"]
    connection.commit.assert_called_once()


@pytest.mark.asyncio
async def test_connection_failure_returns_error_without_unbound_cleanup(database, monkeypatch):
    connection, _ = database
    monkeypatch.setattr(server.pyodbc, "connect", Mock(side_effect=RuntimeError("offline")))
    result = await server._tool_execute_sql("unused", "testdb", "SELECT 1;")
    assert [item.text for item in result] == ["Error executing query: offline"]
    connection.commit.assert_not_called()


@pytest.mark.asyncio
async def test_rollback_failure_does_not_hide_original_error(database):
    connection, cursor = database
    cursor.execute.side_effect = RuntimeError("original")
    connection.rollback.side_effect = RuntimeError("rollback failed")
    result = await server._tool_execute_sql("unused", "testdb", "SELECT 1;")
    assert [item.text for item in result] == ["Error executing query: original"]
    connection.close.assert_called_once()


@pytest.mark.asyncio
async def test_cursor_close_failure_still_closes_connection(database):
    connection, cursor = database
    cursor.close.side_effect = RuntimeError("close failed")
    result = await server._tool_execute_sql("unused", "testdb", "SELECT 1 AS n;")
    assert [item.text for item in result] == ["n\n1"]
    connection.close.assert_called_once()
