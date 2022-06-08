import itertools

from sqlalchemy import sql
from sqlalchemy.sql.elements import quoted_name
from sqlalchemy.engine import Dialect

from .utils import SingleGeneric
from .base import TableName, TableIdentity

from typing import Sequence



# list_tables generic =========================================================

list_tables = SingleGeneric("list_tables")

@list_tables.register("sqlite")
def _list_tables_sqlite(self: Dialect, conn, exclude=None) -> Sequence[TableName]:
    if exclude is None:
        exclude = ("INFORMATION_SCHEMA",)

    schemas = self.get_schema_names(conn)
    query_str = """SELECT name FROM {0} WHERE type='table' ORDER BY name"""

    results = []
    for schema in schemas:
        if schema in exclude:
            continue

        qschema = self.identifier_preparer.quote_identifier(schema)
        qmaster = f"{qschema}.sqlite_master"
        q = conn.exec_driver_sql(query_str.format(qmaster))

        for row in q:
            results.append(TableName(None, schema, row[0]))

    return results


@list_tables.register("mysql")
def _list_tables_mysql(self: Dialect, conn, exclude=None) -> Sequence[TableName]:
    if exclude is None:
        exclude = tuple()

    q = conn.execute("""
        SELECT table_schema AS "schema", table_name as "name"
        FROM INFORMATION_SCHEMA.TABLES
        WHERE
            TABLE_TYPE='BASE TABLE'
            AND TABLE_SCHEMA NOT IN ('mysql', 'performance_schema', 'sys')
    """)

    results = [TableName(None, row[0], row[1]) for row in q]
    return _filter_result(results, exclude)
        


@list_tables.register("postgresql")
def _list_tables_pg(self: Dialect, conn, exclude=None) -> Sequence[TableName]:
    if exclude is None:
        exclude = ("information_schema", "pg_catalog")

    q = conn.execute(sql.text("""
        SELECT db.db_name, nspname, relname  FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        CROSS JOIN (SELECT current_database() AS db_name) db
        WHERE
            c.relkind in ('r', 'p')
    """))

    result = [TableName(*row) for row in q]

    return _filter_result(result, exclude)


@list_tables.register("snowflake")
def _list_tables_sf(self: Dialect, conn, exclude=None) -> Sequence[TableName]:

    if exclude is None:
        exclude = ("INFORMATION_SCHEMA",)

    # snowflake sql supports urls with .../<database>/<schema>,
    # so we need to parse them out.
    # note that alternatively, you could get conn.connection.database, etc..
    engine = conn.engine
    _, opts = engine.dialect.create_connect_args(engine.url)
    db_name, schema_name = opts.get("database"), opts.get("schema")

    if schema_name:
        full_name = ".".join([db_name, schema_name])
        in_clause = f"IN SCHEMA {full_name}"
    elif db_name:
        in_clause = f"IN DATABASE {db_name}"
    else:
        in_clause = "IN ACCOUNT"

    tables = conn.execute(sql.text(
        "SHOW TERSE TABLES " + in_clause
    ))

    views = conn.execute(sql.text(
        "SHOW TERSE VIEWS " + in_clause
    ))

    result = []
    for row in itertools.chain(tables, views):
        if db_name:
            # a default database is set. snowflake's dialect automatically prepends
            # the default database name everywhere, so we need to set database
            # to None in our results
            result.append(TableName(None, row[4], row[1]))
        else:
            # no default database, so return database in results. this allows
            # us to specify sqlalchemy.Table(..., schema="<database>.<schema>")
            result.append(TableName(row[3], row[4], row[1]))

    return _filter_result(result, exclude)


@list_tables.register("bigquery")
def _list_tables_bq(self: Dialect, conn, schema=None, exclude=None) -> Sequence[TableName]:
    if exclude is None:
        exclude = ("information_schema",)

    from google.api_core import exceptions

    client = conn.connection._client
    datasets = client.list_datasets()

    result = []
    for dataset in datasets:
        try:
            tables = client.list_tables(dataset.reference, self.list_tables_page_size)

            for table in tables:
                result.append(TableName(table.project, table.reference.dataset_id, table.table_id))
        except exceptions.NotFound:
            pass

    return _filter_result(result, exclude)

def _filter_result(result: Sequence[TableName], exclude: "Sequence | set") -> Sequence[TableName]:
    exclude_set = set(exclude)
    return [entry for entry in result if entry.schema not in exclude_set]


# Table formatter =============================================================

format_table = SingleGeneric("format_table")

def _join_parts(dialect, parts):
    return "_".join(parts)

def _table_from_part(dialect, table, from_part):
    tup = table.to_tuple(exists=True)
    ii = table.field_index_from_end(from_part)
    return _join_parts(dialect, tup[ii:])


@format_table.register_default
def _format_table_default(self: Dialect, table: TableName, from_part=None) -> str:
    if from_part is not None:
        return _table_from_part(self, table, from_part)

    # just use fully qualified name parts to generate user friendly name
    # e.g. databasename_schemaname_tablename
    tup = table.to_tuple(exists=True)
    return _join_parts(self, tup)

#@format_table.register("snowflake")
#def _format_table_sf(self: Dialect, table: TableName, from_part=None) -> str:
#    # names in snowflake are by default case insensitive (like many databases),
#    # however, they are also UPPERCASE. Make lowercase for ease of use.
#    lower = TableName(*[x.lower() if x is not None else x for x in table.to_tuple()])
#    return format_table.default(self, lower, from_part)


@format_table.register("sqlite")
@format_table.register("postgresql")
@format_table.register("mysql")
@format_table.register("bigquery")
def _format_table_no_db(self: Dialect, table: TableName, from_part=None) -> str:
    """By default only use schema and table name.

    Note that this function is meant to be used for database implementations that
    can't use the same sqlalchemy engine to query across databases. (Or that call
    a schema "database").
    """

    if from_part is not None:
        return _table_from_part(self, table, from_part)

    # return {schema_name}.{table_name}
    tup = table.to_tuple(exists=True)
    return _join_parts(self, tup[-2:])


# Table Identifier ============================================================

identify_table = SingleGeneric("identify_table")

def _identify_default_parts(dialect, parts):
    if len(parts) == 3:
        schema = ".".join(parts[:2])
    elif len(parts) == 2:
        schema = parts[0]
    else:
        schema = None

    return TableIdentity(schema, parts[-1])

def quote_if_not_upper(x):
    if x != x.upper():
        return quoted_name(x, True)

    return x

def _identify_snowflake_parts(dialect, parts):
    # Handle snowflake, whose dialect is a bit funky ---
    # basically, snowflake assumes you are being case insensitive,
    # e.g. that some_table means SOME_TABLE. You can escape this by the quoting
    # functions below. However, snowflake dialect also tries to be clever, and
    # knows that sOmE_tAbLe needs to be escaped.
    #
    # Unfortunately its code is wrong in a way that if you quote an uppercase
    # string it will fail. So we have to detect uppercase names.
    quoted = [dialect.identifier_preparer.quote_identifier(x) for x in parts]
    if len(parts) == 3:
        schema = quoted_name(".".join(quoted[0:2]), False)
    elif len(parts) == 2:
        schema = quote_if_not_upper(parts[0])
    else:
        schema = None

    table_name = quote_if_not_upper(parts[-1])
    return TableIdentity(schema, table_name)


@identify_table.register_default
def _identify_table_default(self: Dialect, table: TableName, from_part=None):
    """By default only use schema and table name.

    Note that this function is meant to be used for database implementations that
    can't use the same sqlalchemy engine to query across databases. (Or that call
    a schema "database").
    """

    if from_part is not None:
        tup = table.to_tuple(exists=True)
        ii = table.field_index_from_end(from_part)
        return _identify_default_parts(self, tup[ii:])

    # Note that database is omitted
    return _identify_default_parts(self, table.to_tuple(exists=True)[-2:])


@identify_table.register("snowflake")
def _identify_table_snowflake(self: Dialect, table: TableName, from_part=None):
    if from_part is not None:
        tup = table.to_tuple(exists=True)
        ii = table.field_index_from_end(from_part)
        return _identify_snowflake_parts(self, tup[ii:])

    return _identify_snowflake_parts(self, table.to_tuple(exists=True))

@identify_table.register("bigquery")
def _identify_table_bigquery(self: Dialect, table: TableName, from_part=None):
    # uses the default implementation (no need for explicit quoting), but
    # includes database name
    if from_part is None:
        from_part = "database"

    return identify_table.default(self, table, from_part=from_part)
