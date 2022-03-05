from importlib.metadata import version as _v

# Set version -----------------------------------------------------------------

__version__ = _v("template_python_pkg")

del _v


# Example class ---------------------------------------------------------------


class ExampleClass:
    """Class that does not do anything.

    Parameters
    ----------
    x: str, optional
        Description of parameter `x`.

    See Also
    --------
    ExampleClass2 : Another example class.

    Examples
    --------

    >>> obj = ExampleClass(1)
    >>> obj.show()
    """

    def __init__(self, x: "str | None" = None):
        self.x = x

    def show(self) -> str:
        """Return a representation of this class.
        """

        return repr(self)


class ExampleClass2(ExampleClass):
    """A subclass that also doesn't do anything."""
