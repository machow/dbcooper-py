from dataclasses import dataclass, astuple

@dataclass(frozen=True)
class TableName:
    database: "str | None"
    schema: "str | None"
    table: "str"

    def to_tuple(self, exists=False):
        tup = astuple(self)

        if exists:
            return tuple(x for x in tup if x is not None)

        return tup

    def field_index_from_end(self, part):
        # could derive from dataclasses.fields, but probably not worth it.
        if part == "database":
            return -3
        elif part == "schema":
            return -2
        elif part == "table":
            return -1

@dataclass(frozen=True)
class TableIdentity:
    schema: "str | quoted_name | None"
    table: "str | quoted_name"

