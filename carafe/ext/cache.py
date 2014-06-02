"""Flask extension of Flask-Cache.
"""

from functools import wraps

from flask import request, current_app
from flask.signals import Namespace
from werkzeug import urls
from flask_cache import Cache as CacheBase


# pylint: disable=invalid-name


signals = Namespace()


# Signals for dealing with cache invalidation after REST methods.
after_post = signals.signal('after_post', doc="""
Signal which should be sent after a POST operation.
""")


after_put = signals.signal('after_put', doc="""
Signal which should be sent after a PUT operation.
""")


after_patch = signals.signal('after_patch', doc="""
Signal which should be sent after a PATCH operation.
""")


after_delete = signals.signal('after_delete', doc="""
Signal which should be sent after a DELETE operation.
""")


# pylint: enable=invalid-name


class Cache(CacheBase):
    """Manager class for handling creating and deleting cache keys based o
    view events.
    """

    view_key_format = '{namespace}:view:{path}'

    def init_app(self, app, config=None):
        if config is None:
            config = app.config

        config.setdefault('CARAFE_CACHE_ENABLED', True)
        config.setdefault('CARAFE_CACHE_IGNORED_REQUEST_ARGS', [])

        if not config['CARAFE_CACHE_ENABLED']:  # pragma: no cover
            return

        super(Cache, self).init_app(app, config=config)

        self.connect_signals()

    def connect_signals(self):
        """Connect supported signals to handlers."""
        after_post.connect(self.on_after_post)
        after_put.connect(self.on_after_put)
        after_patch.connect(self.on_after_patch)
        after_delete.connect(self.on_after_delete)

    def get_cache_namespace(self, obj):
        """Determine object's cache namespace."""
        if getattr(obj, 'cache_namespace', None) is not None:
            return obj.cache_namespace
        elif hasattr(obj, '__name__'):
            return obj.__name__
        else:
            return obj.__class__.__name__

    @property
    def client(self):
        """Proxy to cache client wrapper."""
        return self.cache if self.enabled else None

    @property
    def server(self):
        """Proxy to cache server client."""
        return getattr(self.cache, '_client', None) if self.enabled else None

    @property
    def enabled(self):
        """Property access to config's CARAFE_CACHE_ENABLED."""
        return current_app.config['CARAFE_CACHE_ENABLED']

    @property
    def cache_key_prefix(self):
        return current_app.config['CACHE_KEY_PREFIX']

    def clear_keys(self, *keys):
        """Clear specified keys"""
        if not keys:  # pragma: no cover
            return

        keys = [self.cache_key_prefix + k for k in keys]
        self.server.delete(*keys)

    def clear_prefixes(self, *prefixes):
        """Clear keys starting with prefix"""
        if not prefixes:  # pragma: no cover
            return

        def search_prefix(prefix):
            return '{0}{1}*'.format(self.cache_key_prefix, prefix)

        keys = []
        for prefix in prefixes:
            keys += self.server.keys(search_prefix(prefix))

        self.server.delete(*keys)

    def clear(self, prefixes=None, keys=None):
        """Clear cache keys using an optional prefix, regex, and/or list of
        keys.
        """
        if not self.enabled:
            return

        if not any([prefixes, keys]):
            # this is the same as clearing the entire cache
            return self.cache.clear()

        if not hasattr(self.server, 'pipeline'):
            # enhanced cache clearing is only supported using redis
            return self.cache.clear()

        if prefixes:
            self.clear_prefixes(*prefixes)

        if keys:
            self.clear_keys(*keys)

    def cached_view(self,
                    timeout=None,
                    namespace=None,
                    unless=None,
                    include_request_args=True):
        """Wrapper around self.cached which itself is a decorator. We're
        wrapping because we want to have access to the class instance of the
        view in order to namespace the key. We can't always namespace using
        key_prefix since some cache decorators are placed around parent classes
        which don't know anything about the child class.
        """

        # pylint: disable=missing-docstring
        def wrap(func):
            @wraps(func)
            def wrapper(*args, **kargs):
                if not self.enabled:
                    return func(*args, **kargs)

                if namespace is not None:
                    # Make namespace available in case `f` is used as signal
                    # sender. Mainly used to get namespace when invalidating
                    # cache keys via namespace prefix.
                    func.cache_namespace = namespace

                # If args[0] is set, then this is a class based view, else use
                # function.
                obj = args[0] if args else func
                cache_namespace = self.get_cache_namespace(obj)
                view_path = self.create_view_path(include_request_args)
                key_prefix = self.view_key_format.format(
                    namespace=cache_namespace,
                    path=view_path,
                    **request.view_args)

                cached = self.cached(timeout=timeout,
                                     key_prefix=key_prefix,
                                     unless=unless)(func)

                try:
                    # Cache server could be down.
                    result = cached(*args, **kargs)
                except Exception as ex:  # pragma: no cover
                    # Return function call instead.
                    current_app.logger.exception(ex)
                    result = func(*args, **kargs)

                return result

            return wrapper

        return wrap

    def create_view_path(self, include_request_args=False):
        """Construct view path from request.path with option to include GET
        args.
        """
        href = urls.Href(request.path)

        if include_request_args:
            ignored = current_app.config['CARAFE_CACHE_IGNORED_REQUEST_ARGS']
            args = dict((k, v) for k, v in request.args.iteritems()
                        if k not in ignored)
        else:
            args = None

        return href(args)

    def on_modified_record(self, sender):
        """Common tasks to perform when a record is modified."""
        namespace = self.get_cache_namespace(sender)
        prefixes = [self.view_key_format.format(namespace=namespace, path='')]

        # Append cascade keys which should be invalidated (typically due to
        # this API's data being used in other APIs).
        prefixes += getattr(sender, 'cache_cascade', [])

        try:
            self.clear(prefixes=prefixes)
        except Exception as ex:  # pragma: no cover
            current_app.logger.exception(ex)

    def on_after_post(self, sender):
        """Handle the `after_post` event. Executed after a POST request."""
        self.on_modified_record(sender)

    def on_after_put(self, sender):
        """Handle the `after_put` event. Executed after a PUT request."""
        self.on_modified_record(sender)

    def on_after_patch(self, sender):
        """Handle the `after_patch` event. Executed after a PATCH request."""
        self.on_modified_record(sender)

    def on_after_delete(self, sender):
        """Handle the `after_delete` event. Executed after a DELETE request."""
        self.on_modified_record(sender)
