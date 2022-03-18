from importlib.metadata import version as _v

# Set version -----------------------------------------------------------------

__version__ = _v("dbcooper")

del _v

# Main imports ----------------------------------------------------------------

from .dbcooper import DbCooper    # noqa
