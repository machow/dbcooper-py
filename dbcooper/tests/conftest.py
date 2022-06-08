import pytest

from siuba.tests.helpers import SqlBackend, BigqueryBackend, CloudBackend
from dbcooper.tests.helpers import create_examples

params_backend = [
    pytest.param(lambda: SqlBackend("postgresql"), id = "postgresql", marks=pytest.mark.postgresql),
    pytest.param(lambda: SqlBackend("mysql"), id = "mysql", marks=pytest.mark.mysql),
    pytest.param(lambda: SqlBackend("sqlite"), id = "sqlite", marks=pytest.mark.sqlite),
    pytest.param(lambda: BigqueryBackend("bigquery"), id = "bigquery", marks=pytest.mark.bigquery),
    pytest.param(lambda: CloudBackend("snowflake"), id = "snowflake", marks=pytest.mark.snowflake),
    ]

@pytest.fixture(params=params_backend, scope = "session")
def backend(request):
    backend = request.param()
    if backend.name in ["snowflake", "bigquery"]:
        # We can't easily set up and teardown new databases for cloud providers
        # so really on creating the data outside of tests
        pass
    else:
        create_examples(backend.engine)

    return backend
