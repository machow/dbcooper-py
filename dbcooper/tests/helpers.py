import pandas as pd

from dbcooper.utils import SingleGeneric
from sqlalchemy.sql.elements import quoted_name

from siuba.tests.helpers import SqlBackend, BigqueryBackend, assert_frame_sort_equal

EXAMPLE_SCHEMAS  = {
    ("mai", "lower"): "mai_lower",
    ("mai", "UPPER"): "mai_UPPER",
    ("mai", "MiXeD"): "mai_MiXeD",

    ("MAIN_UPPER", "some_table"): "MAIN_UPPER_some_table",
}


EXAMPLE_DATA = pd.DataFrame({"x": [1,2,3], "y": ['a', 'b', 'b']})

# utilities -------------------------------------------------------------------

write_table = SingleGeneric("write_table")

@write_table.register_default
def _wt_default(engine, df, table_name, schema):
    return df.to_sql(quoted_name(table_name, True), engine, schema=quoted_name(schema, True), if_exists="replace",index=False)

@write_table.register("sqlite")
def _wt_sqlite(engine, df, table_name, schema):
    return df.to_sql(quoted_name(table_name, True), engine, schema=quoted_name(schema, True), if_exists="replace",index=False)


@write_table.register("snowflake")
def _wt_snowflake(engine, df, table_name, schema):
    # Note that I have literally spent more time trying to support writing
    # case sensitive schema + table names to snowflake, than in the development
    # of the rest of this library. The sqlalchemy dialect is not made for it,
    # the python connector methods fail silently, and pandas to_sql fails on
    # reflection (due to dialect issues).
    from sqlalchemy.sql.elements import quoted_name
    from snowflake.connector.pandas_tools import write_pandas, pd_writer
    
    ip = engine.dialect.identifier_preparer
    quoted_schema = ip.quote_identifier(schema)
    quoted_table_name = ip.quote_identifier(table_name)
    with engine.connect() as conn:
        conn.execute(f"""
            CREATE OR REPLACE TABLE {quoted_schema}.{quoted_table_name} (
              x integer,
              y varchar(100)
            )
        """)

        conn.execute(f"""
            INSERT INTO {quoted_schema}.{quoted_table_name}
                VALUES (1, 'a'),
                       (2, 'b'),
                       (3, 'b')
        """)
        #sf_conn = conn.connection.connection
        #conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
        #write_pandas(
        #    sf_conn,
        #    df, table_name, schema= schema, auto_create_table=True, 
        #)
    

create_examples = SingleGeneric("create_examples")

@create_examples.register_default
def _create_examples_default(engine):
    ip = engine.dialect.identifier_preparer

    for schema, table in EXAMPLE_SCHEMAS.keys():
        engine.execute(f"CREATE SCHEMA IF NOT EXISTS {ip.quote_identifier(schema)}")
        write_table(engine, EXAMPLE_DATA, table, schema)

@create_examples.register("sqlite")
def _create_examples_sqlite(engine):
    ip = engine.dialect.identifier_preparer
    prev_schemas = set()

    for schema, table in EXAMPLE_SCHEMAS.keys():
        if schema not in prev_schemas:
            engine.execute(f"ATTACH DATABASE ':memory:' AS {ip.quote_identifier(schema)}")

        prev_schemas.add(schema)
        write_table(engine, EXAMPLE_DATA, table, schema)

