import pytest

from dbcooper.autotables import AutoTable
from dbcooper.tests.helpers import EXAMPLE_SCHEMAS, EXAMPLE_DATA, assert_frame_sort_equal
from dbcooper.tables import DbcSimpleTable
from dbcooper.builder import TableFinder
from siuba import collect

@pytest.fixture
def tbl(backend):
    if backend.name == "snowflake":
        # snowflake can't do reflection on schemas that aren't uppercase, see
        # see https://github.com/snowflakedb/snowflake-sqlalchemy/issues/276
        finder = TableFinder(table_builder=DbcSimpleTable)
        tbl = AutoTable(backend.engine, table_finder=finder)
    else:
        tbl = AutoTable(backend.engine)

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
    

def test_example_data_roundtrip(tbl):
    for (schema, table_name), attr_name in EXAMPLE_SCHEMAS.items():
        table = getattr(tbl, attr_name)
        assert_frame_sort_equal(collect(table()), EXAMPLE_DATA)
