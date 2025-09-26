from __future__ import annotations

from sqlalchemy import sql
from sqlalchemy.engine import Engine
from sqlalchemy.sql.expression import TextClause
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from siuba.sql import LazyTbl
    from duckdb import DuckDBPyConnection
    from polars import DataFrame as PlDataFrame


def query_to_tbl(engine: Engine, query: str) -> TextClause:

    full_query = f"""
        SELECT * FROM (\n{query}\n) WHERE 1 = 0
    """

    with engine.connect() as con:
        q = con.execute(sql.text(full_query))
    
    columns = [sql.column(k) for k in q.keys()]
    text_as_from = sql.text(query).columns(*columns).alias()

    return text_as_from


def name_to_tbl(engine: Engine, table_name: str, schema: str | None=None) -> sql.TableClause:
    # sql dialects like snowflake do not have great reflection capabilities,
    # so we execute a trivial query to discover the column names
    explore_table = sql.table(table_name, schema=schema)
    trivial = explore_table.select(sql.text("0 = 1")).add_columns(sql.text("*"))

    with engine.connect() as con:
        q = con.execute(trivial)

    columns = [sql.column(k) for k in q.keys()]
    return sql.table(table_name, *columns, schema=schema)


def to_siuba(engine: Engine, expr: str | TextClause | sql.TableClause) -> LazyTbl:
    from siuba.sql import LazyTbl

    expr = query_to_tbl(engine, expr) if isinstance(expr, str) else expr
    
    return LazyTbl(engine, expr)


def to_polars(engine: Engine, expr: str | TextClause | sql.TableClause) -> PlDataFrame:
    from polars import read_database

    expr = query_to_tbl(engine, expr) if isinstance(expr, str) else expr

    if isinstance(expr, sql.TableClause):
        expr = expr.select().add_columns()

    with engine.connect() as con:
        return read_database(expr, con)


def to_duckdb(engine: Engine, expr: str | TextClause | sql.TableClause) -> DuckDBPyConnection:
    import duckdb

    if engine.name != "duckdb":
        raise ValueError("This function only works with duckdb engines")

    expr = query_to_tbl(engine, expr) if isinstance(expr, str) else expr

    if isinstance(expr, sql.TableClause):
        expr = expr.select().add_columns()

    with engine.connect() as con:
        # assumes we are using duckdb_engine
        # TODO: expr should be compiled?
        return con.connection.execute(str(expr))
