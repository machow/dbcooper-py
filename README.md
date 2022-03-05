# template-python-pkg

## Developing

```shell
# install with development dependencies
pip install -e .[dev]

# or install from requirements file
pip install -r requirements/dev.txt
```

## Testing

```shell
# run all tests, see pytest section of pyproject.toml
pytest

# run specific marks
pytest -m ex2

# stop on first failure, drop into debugger
pytest -x --pdb
```


## Setting version number

```shell
# set version number
git tag v0.0.1

# (optional) push to github
git push origin --tags

# check version
python -m setuptools_scm
```
