import pytest

from polars import DataFrame as PlDataFrame
from duckdb import DuckDBPyConnection

from dbcooper import DbCooper
from dbcooper.tests.helpers import EXAMPLE_SCHEMAS, EXAMPLE_DATA, assert_frame_sort_equal
from dbcooper.tables import DbcSimpleTable
from dbcooper.finder import TableFinder, AccessorBuilder
from dbcooper.collect import to_polars, to_duckdb, name_to_tbl

from siuba import collect

@pytest.fixture
def tbl(backend):
    if backend.name == "snowflake":
        # snowflake can't do reflection on schemas that aren't uppercase, see
        # see https://github.com/snowflakedb/snowflake-sqlalchemy/issues/276
        tbl = DbCooper(backend.engine, table_factory=DbcSimpleTable)
    elif backend.name == "duckdb":
        # tests currently assume database name isn't used in accessor
        tbl = DbCooper(backend.engine, accessor_builder=AccessorBuilder(format_from_part="schema"))
    else:
        tbl = DbCooper(backend.engine)

    tbl._init()
    return tbl



def test_example_number_of_accessors(tbl):
    assert len(tbl._accessors) == len(EXAMPLE_SCHEMAS)


def test_example_repr_exists(tbl):
    if tbl._engine.name == "snowflake":
        # see https://github.com/snowflakedb/snowflake-sqlalchemy/issues/276
        pytest.xfail()

    for (schema, table_name), attr_name in EXAMPLE_SCHEMAS.items():
        table = getattr(tbl, attr_name)
        assert table_name in repr(table)
    

def test_example_data_roundtrip_siuba(tbl):
    for (schema, table_name), attr_name in EXAMPLE_SCHEMAS.items():
        table = getattr(tbl, attr_name)
        assert_frame_sort_equal(collect(table()), EXAMPLE_DATA)

def test_to_polars(tbl):
    res = to_polars(tbl._engine, name_to_tbl(tbl._engine, "lower", "mai"))
    assert isinstance(res, PlDataFrame)

def test_to_duckdb(tbl):
    if tbl._engine.name != "duckdb":
        pytest.skip("to_duckdb only works with duckdb engines")

    res = to_duckdb(tbl._engine, name_to_tbl(tbl._engine, "lower", "mai"))
    assert isinstance(res, DuckDBPyConnection)

