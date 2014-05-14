"""General purpose utility functions.
"""

from functools import wraps, partial
from threading import Thread

from flask import jsonify as _jsonify


class classproperty(object):  # pylint: disable=invalid-name
    """Decorator that adds class properties. Allows for usage like @property
    but applies the property at the class level. Helps avoid having to use
    metaclasses or other complex techniques to achieve similar results.
    """
    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, owner):
        return self.getter(owner)


def iterflatten(items):
    """Return iterator which flattens list/tuple of lists/tuples

    >>> lst = [1, [2,3], [4, [5, [6]], 7], 8]
    >>> assert list(iterflatten(lst)) == [1,2,3,4,5,6,7,8]
    """
    for item in items:
        if isinstance(item, (list, tuple)):
            for subitem in flatten(item):
                yield subitem
        else:
            yield item


def flatten(items):
    """Return flattened list of a list/tuple of lists/tuples

    >>> lst = [1, [2,3], [4, [5, [6]], 7], 8]
    >>> assert flatten(lst) == [1,2,3,4,5,6,7,8]
    """
    return list(iterflatten(items))


def async(func):
    """Poor man's decorator to execute a function asynchronously using separate
    thread. This is an extremely limited async method which doesn't provide any
    way to access the created thread. Use with caution!

    For more robust async, consider using alternative methods/libraries
    (e.g. gevent).
    """
    @wraps(func)
    def wrapper(*args, **kargs):  # pylint: disable=missing-docstring
        thr = Thread(target=func, args=args, kwargs=kargs)
        thr.start()
    return wrapper


def to_dict(data=None, namespace=None):
    """Decorator enabled version of `_to_dict()`."""
    __to_dict = partial(_to_dict, namespace=namespace)

    if data is None:
        # pylint: disable=missing-docstring
        def decorator(func):
            @wraps(func)
            def decorated(*args, **kargs):
                data = func(*args, **kargs)
                return __to_dict(data)
            return decorated
        return decorator
    else:
        return __to_dict(data)


def _to_dict(data, namespace=None):
    """Converts elements of `data` using `data.to_dict()` or
    `data[].to_dict()`. Optionally namespaces data into a container dict using
    `namespace` as key.
    """
    if isinstance(data, list):
        data = [item.to_dict() if hasattr(item, 'to_dict') else item
                for item in data]
    elif hasattr(data, 'to_dict'):
        data = data.to_dict()

    if namespace is not None:
        data = {namespace: data}

    return data


def jsonify(func=None, *args, **kargs):
    """Function or decorator that returns jsonfiy response"""
    if callable(func):
        # pylint: disable=missing-docstring
        @wraps(func)
        def decorated(*args, **kargs):
            return _jsonify(**func(*args, **kargs))
        return decorated
    else:
        if func is not None:
            # consider `f` a positional arg
            args = tuple([func] + list(args))
        return _jsonify(*args, **kargs)
