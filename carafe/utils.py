
from functools import wraps, partial
from threading import Thread
import re

class classproperty(object):
    '''
    Decorator that adds class properties.
    Allows for usage like @property but applies the property at the class level.
    Helps avoid having to use metaclasses or other complex techniques to achieve similar results.
    '''
    def __init__(self, getter):
        self.getter = getter
    def __get__(self, instance, owner):
        return self.getter(owner)


def iterflatten(l):
    '''
    Return iterator which flattens list/tuple of lists/tuples
    >>> assert list(iterflatten([1, [2,3], [4, [5, [6]], 7], 8])) == [1,2,3,4,5,6,7,8]
    '''
    for x in l:
        if isinstance(x, (list, tuple)):
            for y in flatten(x):
                yield y
        else:
            yield x

def flatten(l):
    '''
    Return flattened list of a list/tuple of lists/tuples
    >>> assert flatten([1, [2,3], [4, [5, [6]], 7], 8]) == [1,2,3,4,5,6,7,8]
    '''
    return list(iterflatten(l))

def async(f):
    '''
    Poor man's decorator to execute a function asynchronously using separate thread.
    This is an extremely limited async method which doesn't provide any way to
    access the created thread. Use with caution!

    For more robust async, consider using alternative methods/libraries (e.g. gevent)
    '''
    @wraps(f)
    def wrapper(*args, **kargs):
        thr = Thread(target=f, args=args, kwargs=kargs)
        thr.start()
    return wrapper

def to_dict(data=None, namespace=None):
    '''
    Decorator enabled version of `_to_dict()`
    '''
    __to_dict = partial(_to_dict, namespace=namespace)

    if data is None:
        def decorator(f):
            @wraps(f)
            def decorated(*args, **kargs):
                data = f(*args, **kargs)
                return __to_dict(data)
            return decorated
        return decorator
    else:
        return __to_dict(data)

def _to_dict(data, namespace=None):
    '''
    Converts elements of `data` using `data.to_dict()` or `data[].to_dict()`.
    Optionally namespaces data into a container dict using `namespace` as key.
    '''
    if isinstance(data, list):
        data = [d.to_dict() if hasattr(d, 'to_dict') else d for d in data]
    elif hasattr(data, 'to_dict'):
        data = data.to_dict()

    if namespace is not None:
        data = {namespace: data}

    return data

def urlpathjoin(*paths):
    '''Join URL paths into single URL while maintaining leading and trailing slashes
    if present on first and last elements respectively.

    >>> assert urlpathjoin('') == ''
    >>> assert urlpathjoin(['', '/a']) == '/a'
    >>> assert urlpathjoin(['a', '/']) == 'a/'
    >>> assert urlpathjoin(['', '/a', '', '', 'b']) == '/a/b'
    >>> assert urlpathjoin(['/a/', 'b/', '/c', 'd', 'e/']) == '/a/b/c/d/e/'
    >>> assert urlpathjoin(['a', 'b', 'c']) == 'a/b/c'
    >>> assert urlpathjoin(['a/b', '/c/d/', '/e/f']) == 'a/b/c/d/e/f'
    >>> assert urlpathjoin('/', 'a', 'b', 'c', 1, '/') == '/a/b/c/1/'
    >>> assert urlpathjoin([]) == ''
    '''
    paths = [str(path) for path in flatten(paths) if path]
    leading = '/' if paths and paths[0].startswith('/') else ''
    trailing = '/' if paths and paths[-1].endswith('/') else ''
    url = leading + '/'.join([p.strip('/') for p in paths if p.strip('/')]) + trailing
    return url

def camelcase_to_underscore(name):
    '''
    >>> assert camelcase_to_underscore('FooBar') == 'foo_bar'
    >>> assert camelcase_to_underscore('FooBar_Baz') == 'foo_bar__baz'
    '''
    first_cap_re = re.compile('(.)([A-Z][a-z]+)')
    all_cap_re = re.compile('([a-z0-9])([A-Z])')

    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()

