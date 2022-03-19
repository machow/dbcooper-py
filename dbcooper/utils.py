class SingleGeneric:
    def __init__(self, name, dispatch_on_attr = "name"):
        self.name = name
        self.registry = {}
        self.dispatch_on_attr = dispatch_on_attr
        self.default = None

    def __call__(self, dialect, *args, **kwargs):
        type_str = getattr(dialect, self.dispatch_on_attr)

        try:
            f_concrete = self.registry[type_str]
        except KeyError:
            if self.default is not None:
                f_concrete = self.default
            else:
                raise NotImplementedError(f"Cannot dispatch on {type_str} and no default implementation.")

        return f_concrete(dialect, *args, **kwargs)

    def register(self, type_str, func=None):
        # allow it to function as a decorator
        if func is None:
            return lambda f: self.register(type_str, f)

        self.registry[type_str] = func

        return func

    def register_default(self, func):
        self.default = func

    def __repr__(self):
        return f"{type(self)}({self.name})"


