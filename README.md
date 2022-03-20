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
import lahman
from sqlalchemy import create_engine

def load_tables_for_engine(engine, exclude=[], **kwargs):
    for name in lahman._accessors:
        if name in exclude: continue
        df = getattr(lahman, name)()
        df.to_sql(name, engine, **kwargs)

engine = create_engine("sqlite://")
engine.execute("ATTACH ':memory:' AS lahman")
load_tables_for_engine(engine, schema="lahman")
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

TODO: GIF of accessor + autocompletion (or put it at the very top)

### Using database functions

* `.list()`: Get a list of tables
* `.tbl()`: Access a table that can be worked with using `siuba`.
* `.query()`: Perform a SQL query and work with the result.
* `._engine`: Get the underlying sqlalchemy engine.


```python
dbc.list()
dbc.tbl("Batting")

from siuba import _, count
dbc.tbl("Batting") >> count(_.teamID)
```




<div><pre># Source: lazy query
# DB Conn: Engine(sqlite://)
# Preview:
</pre><div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>teamID</th>
      <th>n</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>CHN</td>
      <td>5060</td>
    </tr>
    <tr>
      <th>1</th>
      <td>PHI</td>
      <td>4971</td>
    </tr>
    <tr>
      <th>2</th>
      <td>PIT</td>
      <td>4920</td>
    </tr>
    <tr>
      <th>3</th>
      <td>SLN</td>
      <td>4853</td>
    </tr>
    <tr>
      <th>4</th>
      <td>CIN</td>
      <td>4731</td>
    </tr>
  </tbody>
</table>
</div><p># .. may have more rows</p></div>



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




<div><pre># Source: lazy query
# DB Conn: Engine(sqlite://)
# Preview:
</pre><div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>playerID</th>
      <th>AB</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>aardsda01</td>
      <td>4</td>
    </tr>
    <tr>
      <th>1</th>
      <td>aaronha01</td>
      <td>12364</td>
    </tr>
    <tr>
      <th>2</th>
      <td>aaronto01</td>
      <td>944</td>
    </tr>
    <tr>
      <th>3</th>
      <td>aasedo01</td>
      <td>5</td>
    </tr>
    <tr>
      <th>4</th>
      <td>abadan01</td>
      <td>21</td>
    </tr>
  </tbody>
</table>
</div><p># .. may have more rows</p></div>



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
