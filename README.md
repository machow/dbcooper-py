# dbcooper-py

[![CI](https://github.com/machow/dbcooper-py/actions/workflows/ci.yml/badge.svg)](https://github.com/machow/dbcooper-py/actions/workflows/ci.yml)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/machow/dbcooper-py/HEAD)

The dbcooper package turns a database connection into a collection of functions,
handling logic for keeping track of connections and letting you take advantage of
autocompletion when exploring a database.

It's especially helpful to use when authoring database-specific Python packages,
for instance in an internal company package or one wrapping a public data source.

For the R version see [dgrtwo/dbcooper](https://github.com/dgrtwo/dbcooper).

## Installation

```
pip install dbcooper
```

## Example

### Initializing the functions

The dbcooper package asks you to create the connection first.
As an example, we'll use the Lahman baseball database package (`lahman`).


```python
from sqlalchemy import create_engine
from dbcooper.data import lahman_sqlite

# connect to sqlite
engine = create_engine("sqlite://")

# load the lahman data into the "lahman" schema
lahman_sqlite(engine)
```

Next we'll set up dbcooper


```python
from dbcooper import DbCooper

dbc = DbCooper(engine)
```

The `DbCooper` object contains two important things:

* Accessors to fetch specific tables.
* Functions for interacting with the underlying database.

### Using table accessors

In the example below, we'll use the `"Lahman"."Salaries"` table as an example.
By default, dbcooper makes this accessible as `.lahman_salaries`.

**Plain** `.lahman_salaries` prints out table and column info, including types and descriptions.


```python
# show table and column descriptions
dbc.lahman_salaries
```




<h3> salaries </h3>
<p> (No table description.) </p>
<table>
<thead>
<tr><th>name    </th><th>type  </th><th>description  </th></tr>
</thead>
<tbody>
<tr><td>index   </td><td>BIGINT</td><td>             </td></tr>
<tr><td>yearID  </td><td>BIGINT</td><td>             </td></tr>
<tr><td>teamID  </td><td>TEXT  </td><td>             </td></tr>
<tr><td>lgID    </td><td>TEXT  </td><td>             </td></tr>
<tr><td>playerID</td><td>TEXT  </td><td>             </td></tr>
<tr><td>salary  </td><td>BIGINT</td><td>             </td></tr>
</tbody>
</table>



Note that sqlite doesn't support table and columnn descriptions, so these sections
are empty.

**Calling** `.lahman_salaries()` fetches a lazy version of the data.



```python
dbc.lahman_salaries()
```




    # Source: lazy query
    # DB Conn: Engine(sqlite://)
    # Preview:
       index  yearID teamID lgID   playerID  salary
    0      0    1985    ATL   NL  barkele01  870000
    1      1    1985    ATL   NL  bedrost01  550000
    2      2    1985    ATL   NL  benedbr01  545000
    3      3    1985    ATL   NL   campri01  633333
    4      4    1985    ATL   NL  ceronri01  625000
    # .. may have more rows



Note that this data is a siuba `LazyTbl` object, which you can use to analyze the data.


```python
from siuba import _, count

dbc.lahman_salaries() >> count(over_100k = _.salary > 100_000)
```




    # Source: lazy query
    # DB Conn: Engine(sqlite://)
    # Preview:
       over_100k      n
    0       True  25374
    1      False   1054
    # .. may have more rows



### Using database functions

* `.list()`: Get a list of tables
* `.tbl()`: Access a table that can be worked with using `siuba`.
* `.query()`: Perform a SQL query and work with the result.
* `._engine`: Get the underlying sqlalchemy engine.

For instance, we could start by finding the names of the tables in the Lahman database.


```python
dbc.list()
```




    ['lahman.allstar_full',
     'lahman.appearances',
     'lahman.awards_managers',
     'lahman.awards_players',
     'lahman.awards_share_managers',
     'lahman.awards_share_players',
     'lahman.batting',
     'lahman.batting_post',
     'lahman.college_playing',
     'lahman.fielding',
     'lahman.fielding_of',
     'lahman.fielding_ofsplit',
     'lahman.fielding_post',
     'lahman.hall_of_fame',
     'lahman.home_games',
     'lahman.managers',
     'lahman.managers_half',
     'lahman.parks',
     'lahman.people',
     'lahman.pitching',
     'lahman.pitching_post',
     'lahman.salaries',
     'lahman.schools',
     'lahman.series_post',
     'lahman.teams',
     'lahman.teams_franchises',
     'lahman.teams_half']



We can access one of these tables with `dbc.tbl()`, then put it through any kind
of siuba operation.


```python
dbc.tbl("Salaries")
```




    # Source: lazy query
    # DB Conn: Engine(sqlite://)
    # Preview:
       index  yearID teamID lgID   playerID  salary
    0      0    1985    ATL   NL  barkele01  870000
    1      1    1985    ATL   NL  bedrost01  550000
    2      2    1985    ATL   NL  benedbr01  545000
    3      3    1985    ATL   NL   campri01  633333
    4      4    1985    ATL   NL  ceronri01  625000
    # .. may have more rows




```python
from siuba import _, count
dbc.tbl("Salaries") >> count(_.yearID, sort=True)
```




    # Source: lazy query
    # DB Conn: Engine(sqlite://)
    # Preview:
       yearID     n
    0    1999  1006
    1    1998   998
    2    1995   986
    3    1996   931
    4    1997   925
    # .. may have more rows



If you'd rather start from a SQL query, use the `.query()` method.


```python
dbc.query("""
    SELECT
        playerID,
        sum(AB) as AB
    FROM Batting
    GROUP BY playerID
""")
```




    # Source: lazy query
    # DB Conn: Engine(sqlite://)
    # Preview:
        playerID     AB
    0  aardsda01      4
    1  aaronha01  12364
    2  aaronto01    944
    3   aasedo01      5
    4   abadan01     21
    # .. may have more rows



For anything else you might want to do, the sqlalchemy Engine object is available.
For example, the code below shows how you can set its `.echo` attribute, which
tells sqlalchemy to provide useful logs.


```python
dbc._engine.echo = True
table_names = dbc.list()
```

    2022-03-20 22:49:37,553 INFO sqlalchemy.engine.Engine PRAGMA database_list
    2022-03-20 22:49:37,554 INFO sqlalchemy.engine.Engine [raw sql] ()
    2022-03-20 22:49:37,555 INFO sqlalchemy.engine.Engine SELECT name FROM "main".sqlite_master WHERE type='table' ORDER BY name
    2022-03-20 22:49:37,555 INFO sqlalchemy.engine.Engine [raw sql] ()
    2022-03-20 22:49:37,556 INFO sqlalchemy.engine.Engine SELECT name FROM "lahman".sqlite_master WHERE type='table' ORDER BY name
    2022-03-20 22:49:37,557 INFO sqlalchemy.engine.Engine [raw sql] ()


Note that the log messages above show that the `.list()` method executed two queries:
One to list tables in the "main" schema (which is empty), and one to list tables
in the "lahman" schema.

## Advanced Configuration

> ⚠️: These behaviors are well tested, but dbcooper's internals and API may change.

dbcooper can be configured in three ways, each corresponding to a class interface:

* **TableFinder**: Which tables will be used by `dbcooper`.
* **AccessorBuilder**: How table names are turned into accessors.
* **DbcDocumentedTable**: The class that defines what an accessor will return.


```python
from sqlalchemy import create_engine
from dbcooper.data import lahman_sqlite
from dbcooper import DbCooper, AccessorBuilder

engine = create_engine("sqlite://")
lahman_sqlite(engine)
```

### Excluding a schema


```python
from dbcooper import TableFinder

finder = TableFinder(exclude_schemas=["lahman"])
dbc_no_lahman = DbCooper(engine, table_finder=finder)
dbc_no_lahman.list()
```




    []



### Formatting table names


```python
from dbcooper import AccessorBuilder

# omits schema, and keeps only table name
# e.g. `salaries`, rather than `lahman_salaries`
builder = AccessorBuilder(format_from_part="table")

tbl_flat = DbCooper(engine, accessor_builder=builder)
tbl_flat.salaries()
```




    # Source: lazy query
    # DB Conn: Engine(sqlite://)
    # Preview:
       index  yearID teamID lgID   playerID  salary
    0      0    1985    ATL   NL  barkele01  870000
    1      1    1985    ATL   NL  bedrost01  550000
    2      2    1985    ATL   NL  benedbr01  545000
    3      3    1985    ATL   NL   campri01  633333
    4      4    1985    ATL   NL  ceronri01  625000
    # .. may have more rows



### Grouping tables by schema


```python
from dbcooper import AccessorHierarchyBuilder

tbl_nested = DbCooper(engine, accessor_builder=AccessorHierarchyBuilder())

# note the form: <schema>.<table>
tbl_nested.lahman.salaries()
```




    # Source: lazy query
    # DB Conn: Engine(sqlite://)
    # Preview:
       index  yearID teamID lgID   playerID  salary
    0      0    1985    ATL   NL  barkele01  870000
    1      1    1985    ATL   NL  bedrost01  550000
    2      2    1985    ATL   NL  benedbr01  545000
    3      3    1985    ATL   NL   campri01  633333
    4      4    1985    ATL   NL  ceronri01  625000
    # .. may have more rows



### Don't show table documentation


```python
from dbcooper import DbcSimpleTable

dbc_no_doc = DbCooper(engine, table_factory=DbcSimpleTable)
dbc_no_doc.lahman_salaries
```




    DbcSimpleTable(..., 'salaries', 'lahman')



Note that sqlalchemy dialects like `snowflake-sqlalchemy` cannot look up things
like table and column descriptions as well as other dialects, so `DbcSimpleTable`
may be needed to connect to snowflake (see [this issue](https://github.com/snowflakedb/snowflake-sqlalchemy/issues/276)).

## Developing

```shell
# install with development dependencies
pip install -e .[dev]

# or install from requirements file
pip install -r requirements/dev.txt
```

### Test

```shell
# run all tests, see pytest section of pyproject.toml
pytest

# run specific backends
pytest -m 'not snowflake and not bigquery'

# stop on first failure, drop into debugger
pytest -x --pdb
```

### Release

```shell
# set version number
git tag v0.0.1

# (optional) push to github
git push origin --tags

# check version
python -m setuptools_scm
```
