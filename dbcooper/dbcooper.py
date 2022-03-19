from sqlalchemy import create_engine

from .finder import TableFinder, AccessorBuilder
from .tables import DbcDocumentedTable, query_to_tbl, name_to_tbl

import typing

if typing.TYPE_CHECKING:
    from sqlalchemy.engine import Engine


class DbCooper:
    def __init__(
        self,
        engine: "str | Engine",
        table_finder=TableFinder(),
        table_factory=DbcDocumentedTable,
        accessor_builder=AccessorBuilder(),
        initialize=True,
    ):

        if isinstance(engine, str):
            engine = create_engine(engine)

        self._engine = engine
        self._accessors = {}
        self._table_finder = table_finder
        self._table_factory = table_factory
        self._accessor_builder=accessor_builder

        if initialize:
            self._init()

    def __getattr__(self, k):
        if k in self._accessors:
            return self._accessors[k]

        raise AttributeError("No such attribute %s" % k)

    def __getitem__(self, k):
        if k in self._accessors:
            return self._accessors[k]

        raise AttributeError("No such attribute %s" % k)


    def __dir__(self):
        dbc_methods = ["reset", "query", "list", "tbl"]
        return dbc_methods + list(self._accessors.keys())

    def _ipython_key_completions_(self):
        return list(self._accessors)

    def _init(self):
        with self._engine.connect() as conn:
            table_map = self._table_finder.map_tables(self._engine.dialect, conn)

        accessors = self._accessor_builder.create_accessors(
            self._engine,
            self._table_factory,
            table_map
        )
        self._accessors = accessors

    def reset(self):
        self._init()

    def list(self, raw=False):
        dialect = self._engine.dialect
        with self._engine.connect() as conn:
            tables = self._table_finder.list_tables(dialect, conn)

        if raw:
            return tables
        else:
            results = []
            for table in tables:
                ident = self._table_finder.identify_table(dialect, table)
                results.append(self._table_finder.join_identifiers(ident))

            return results

    def query(self, query):
        return query_to_tbl(self._engine, query)

    def tbl(self, name, schema=None):
        return name_to_tbl(self._engine, name, schema)
