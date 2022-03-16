from collections.abc import Mapping

from .inspect import TableName, list_tables, format_table, identify_table
from .tables import DbcDocumentedTable
# from collections import defaultdict

class AttributeDict(Mapping):
    """Similar to a dictionary, except items may also be accessed as attributes."""

    def __init__(self):
        self._d = {}

    def __getitem__(self, k):
        return self._d[k]

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return len(self._d)

    def __getattr__(self, k):
        if k in self._d:
            return self._d[k]

        raise AttributeError("No attribute %s" % k)

    def __setitem__(self, k, v):
        self._d[k] = v

    def __dir__(self):
        return list(self._d.keys())

    def __repr__(self):
        repr_d = repr(self._d)
        return f"{self.__class__.__name__}({repr_d})"



class TableFinder:
    # TODO: rename exclude_schemas
    def __init__(self, exclude=None, format_from_part=None, identify_from_part=None, table_builder=DbcDocumentedTable):
        # TODO: filter method
        self.exclude = exclude
        self.format_from_part = format_from_part
        self.identify_from_part = identify_from_part
        self.table_builder = table_builder

    def list_tables(self, dialect, conn):
        return list_tables(dialect, conn, self.exclude)

    def format_table(self, dialect, table: TableName):
        #return format_table(dialect, table)
        return format_table(dialect, table, self.format_from_part)
        

    def identify_table(self, dialect, table: TableName):
        return identify_table(dialect, table, self.identify_from_part)

    def map_tables(self, dialect, conn):
        table_map = {}
        table_names = self.list_tables(dialect, conn)

        for name in table_names:
            ident_table = self.identify_table(dialect, name)
            table_map[name] = ident_table

        return table_map

    def create_accessors(self, engine):
        accessors = AttributeDict()

        with engine.connect() as conn:
            table_map = self.map_tables(engine.dialect, conn)

        for table, ident in table_map.items():
            fmt_name = self.format_table(engine.dialect, table)

            if fmt_name in accessors:
                raise Exception("multiple tables w/ formatted name: %s" % fmt_name)

            accessors[fmt_name] = self.table_builder(engine, ident.table, ident.schema)

        return accessors
