from __future__ import annotations

from tabulate import tabulate
from siuba.sql import LazyTbl
from typing import TYPE_CHECKING
from sqlalchemy import Table, MetaData

from .collect import name_to_tbl, to_siuba

if TYPE_CHECKING:
    import sqlalchemy as sqla
    from sqlalchemy.engine import Engine

class DbcSimpleTable:
    """Represent a database table."""
    def __init__(self, engine: Engine, table_name: str, schema: str | None = None, to_frame=to_siuba):
        self.engine = engine
        self.table_name = table_name
        self.schema = schema
        self.to_frame = to_frame

    def __repr__(self):
        repr_args = map(repr, [self.table_name, self.schema])
        joined_repr = ", ".join(repr_args)
        return f"{self.__class__.__name__}(..., {joined_repr})"

    def _repr_html_(self):
        raise NotImplementedError()

    def __call__(self):
        sqla_tbl = self._create_table()
        return self.to_frame(self.engine, sqla_tbl)

    def _create_table(self) -> sqla.sql.TableClause:
        return name_to_tbl(self.engine, self.table_name, self.schema)


class DbcDocumentedTable(DbcSimpleTable):
    """Represent a database table with a nice column summary (including comments).

    Note that this class's objects return a siuba LazyTbl when called, and print
    out the table and column descriptions otherwise.
    """

    table_comment_fields = {"name": "name", "type": "type", "description": "comment"}

    def _create_table(self) -> sqla.Table:
        table = Table(self.table_name, MetaData(), schema=self.schema, autoload_with = self.engine)
        return table

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
        table = self._create_table()

        table_comment = self._get_table_comment(table)

        return f"""\
<h3> {table.name} </h3>
<p> {table_comment} </p>
{self._repr_body(table, "html")}\
"""

    def __repr__(self):
        table = self._create_table()

        table_comment = self._get_table_comment(table)

        return f"""\
{table.name}
{table_comment}

{self._repr_body(table, "simple")}\
"""





