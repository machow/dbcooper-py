import pytest

from template_python_pkg import ExampleClass, ExampleClass2

params = [
    pytest.param(ExampleClass, id="ex", marks=pytest.mark.ex),
    pytest.param(ExampleClass2, id="ex2", marks=pytest.mark.ex2),
]


@pytest.fixture(params=params, scope="function")
def example(request):
    # set up
    cls_factory = request.param
    example = cls_factory(1)

    # give to test
    yield example

    # teardown
    print("tearing down")


def test_example_show(example):
    assert example.show() == repr(example)
