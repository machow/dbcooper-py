from tabulate import tabulate
from siuba.sql import LazyTbl
from sqlalchemy import sql


def query_to_tbl(engine, query: str) -> LazyTbl:

    full_query = f"""
        SELECT * FROM (\n{query}\n) WHERE 1 = 0
    """

    q = engine.execute(sql.text(full_query))
    
    columns = [sql.column(k) for k in q.keys()]
    text_as_from = sql.text(query).columns(*columns).alias()

    return LazyTbl(engine, text_as_from)


def name_to_tbl(engine, table_name, schema=None) -> LazyTbl:
    # sql dialects like snowflake do not have great reflection capabilities,
    # so we execute a trivial query to discover the column names
    explore_table = sql.table(table_name, schema=schema)
    trivial = explore_table.select(sql.text("0 = 1")).add_columns(sql.text("*"))

    q = engine.execute(trivial)

    columns = [sql.column(k) for k in q.keys()]
    return LazyTbl(engine, sql.table(table_name, *columns, schema=schema))

class DbcSimpleTable:
    def __init__(self, engine, table_name, schema=None):
        self.engine = engine
        self.table_name = table_name
        self.schema = schema

    def __repr__(self):
        repr_args = map(repr, [self.table_name, self.schema])
        joined_repr = ", ".join(repr_args)
        return f"{self.__class__.__name__}(..., {joined_repr})"

    def _repr_html_(self):
        raise NotImplementedError()

    def __call__(self):
        return self._create_table()

    def _create_table(self):
        return name_to_tbl(self.engine, self.table_name, self.schema)


class DbcDocumentedTable(DbcSimpleTable):
    """Represent a database table.

    Note that this class's objects return a siuba LazyTbl when called, and print
    out the table and column descriptions otherwise.
    """

    table_comment_fields = {"name": "name", "type": "type", "description": "comment"}

    def _create_table(self):
        from sqlalchemy import Table, MetaData
        table = Table(self.table_name, MetaData(), schema=self.schema, autoload_with = self.engine)
        return LazyTbl(self.engine, table)

    # methods for representation ----------------------------------------------

    def _col_to_row(self, col):
        return {k: getattr(col, v) for k,v in self.table_comment_fields.items()}

    def _repr_body(self, table, tablefmt):
        rows = [self._col_to_row(col) for col in table.columns]
        return tabulate(rows, headers="keys", tablefmt=tablefmt)

    @staticmethod
    def _get_table_comment(table):
        if table.comment is None:
            return "(No table description.)"
        else:
            return table.comment

    def _repr_html_(self):
        tbl = self._create_table()
        table = tbl.tbl

        table_comment = self._get_table_comment(table)

        return f"""\
<h3> {table.name} </h3>
<p> {table_comment} </p>
{self._repr_body(table, "html")}\
"""

    def __repr__(self):
        tbl = self._create_table()
        table = tbl.tbl

        table_comment = self._get_table_comment(table)

        return f"""\
{table.name}
{table_comment}

{self._repr_body(table, "simple")}\
"""





