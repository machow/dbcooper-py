from __future__ import annotations

from collections.abc import Mapping

from .inspect import TableName, TableIdentity, list_tables, format_table, identify_table

from typing import Callable

def _set_default(d, k, default):
    """Same behavior as dict.setdefault"""
    if k in d:
        return d[k]
    else:
        d[k] = default
        return default

class AttributeDict(Mapping):
    """Similar to a dictionary, except items may also be accessed as attributes."""

    def __init__(self, d=None):
        if d is None:
            self._d = {}
        else:
            # make a copy, just to be safe
            self._d = {**d}

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
    # TODO: format="lowercase", exclude_schemas, exclude_tables
    def __init__(self,
        exclude_schemas=None,
        identify_from_part=None,
    ):
        # TODO: filter method
        self.exclude_schemas = exclude_schemas
        self.identify_from_part = identify_from_part

    def list_tables(self, dialect, conn):
        # first use generic method that dispatches on dialect name
        return list_tables(dialect, conn, self.exclude_schemas)


    def identify_table(self, dialect, table: TableName):
        return identify_table(dialect, table, self.identify_from_part)

    def join_identifiers(self, ident: TableIdentity):
        return f"{ident.schema}.{ident.table}"

    def map_tables(self, dialect, conn) -> Mapping[TableName, TableIdentity]:
        table_map = {}
        table_names = self.list_tables(dialect, conn)

        for name in table_names:
            ident_table = self.identify_table(dialect, name)
            table_map[name] = ident_table

        return table_map


class AccessorBuilder:
    def __init__(
        self,
        format_from_part=None,
        name_format: "str | Callable[TableName, str]" = "identity",
    ):
        self.format_from_part=format_from_part
        self.name_format=name_format

    def format_table(self, dialect, table: TableName):
        if callable(self.name_format):
            return self.name_format(table)

        # first use generic method that dispatches on dialect name
        table =  format_table(dialect, table, self.format_from_part)

        if self.name_format == "lower":
            return table.lower()
        elif self.name_format == "identity":
            return table
        else:
            raise ValueError(
                "Unknown name_format argument type: {type(self.name_format)}"
            )

    def create_accessors(self, engine, table_factory, table_map: Mapping[TableName, TableIdentity]):
        accessors = AttributeDict()

        for table, ident in table_map.items():
            fmt_name = self.format_table(engine.dialect, table)
            if fmt_name in accessors:
                raise Exception("multiple tables w/ formatted name: %s" % fmt_name)

            accessors[fmt_name] = table_factory(engine, ident.table, ident.schema)

        return accessors


class AccessorHierarchyBuilder(AccessorBuilder):
    def __init__(
        self, *args, omit_database=True, **kwargs
        ):
        super().__init__(*args, **kwargs)
        self.format_from_part="table"
        self.omit_database = omit_database

    def _group_by_level(self, table_map):
        from itertools import groupby

        sorted_items = sorted(
            sorted(table_map.items(), key=lambda x: x[0].database or ""),
            key=lambda x: x[0].schema or ""
        )

        grouped = groupby(sorted_items, lambda x: (x[0].database, x[0].schema))
        return {group_key: dict(iter_) for group_key, iter_ in grouped}

    def create_accessors(self, engine, table_factory, table_map):

        grouped = self._group_by_level(table_map)

        res = AttributeDict()
        for (db, schema), sub_map in grouped.items():
            sub_accessors = super().create_accessors(engine, table_factory, sub_map)
            acc_db = _set_default(res, db, AttributeDict())
            if schema in acc_db:
                raise ValueError(
                    "Already set accessors for this schema.\n"
                    f"Database name: {db}\n"
                    f"Schema name: {schema}\n"
                )
            acc_db[schema] = sub_accessors

        if self.omit_database:
            if len(acc_db) != 1:
                raise ValueError(
                    "Omitting database requires exactly 1 database entry, but found "
                    f"the following: {list(acc_db)}"
                )

            # return the only entry in the accessors dictionary
            return list(res.values())[0]

        return res

