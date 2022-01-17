
from copy import deepcopy

def deepcopy_self(fn):
    """
    deepcopy_self
    =============

    Decorator that allows models to return copies of themselves, allowing for
    safe method chaining.
    """
    def inner(self, *args,**kwargs):
        return fn(deepcopy(self), *args, **kwargs)
    return inner
