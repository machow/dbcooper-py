from siuba.sql import LazyTbl
from sqlalchemy import create_engine

from .builder import TableFinder
from .tables import query_to_tbl

class DbCooper:
    def __init__(self, engine, table_finder=TableFinder()):
        if isinstance(engine, str):
            engine = create_engine(engine)

        self._engine = engine
        self._accessors = {}
        self._table_finder = table_finder

    def __getattr__(self, k):
        if k in self._accessors:
            return self._accessors[k]

        raise AttributeError("No such attribute %s" % k)

    def __getitem__(self, k):
        if k in self._accessors:
            return self._accessors[k]

        raise AttributeError("No such attribute %s" % k)


    def __dir__(self):
        return ["query"] + list(self._accessors.keys())

    def _ipython_key_completions_(self):
        return list(self._accessors)

    def _init(self):
        accessors = self._table_finder.create_accessors(self._engine)
        self._accessors = accessors

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
                results.append(f"{ident.schema}.{ident.table}")

            return results

    def query(self, query):
        return query_to_tbl(self._engine, query)

    def tbl(self, name, schema=None):
        from sqlalchemy import sql
        
        # sql dialects like snowflake do not have great reflection capabilities,
        # so we execute a trivial query to discover the column names
        explore_table = sql.table(name, schema=schema)
        trivial = explore_table.select(sql.text("0 = 1")).add_columns(sql.text("*"))

        q = self._engine.execute(trivial)

        columns = [sql.column(k) for k in q.keys()]
        return LazyTbl(self._engine, sql.table(name, *columns, schema=schema))
