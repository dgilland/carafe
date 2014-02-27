
from functools import wraps
import inspect

from flask import request, current_app
from werkzeug import urls
from flask.ext.cache import Cache as CacheBase

CACHE_VIEW_ID_KEY = '_id'
CACHE_KEY_FORMATS = {
    'view': '{namespace}:view:{path}',
    # using default, this translates to '{namespace}:_id:{_id}'
    CACHE_VIEW_ID_KEY: '{{namespace}}:{0}:{{{0}}}'.format(CACHE_VIEW_ID_KEY)
}

class Cache(CacheBase):
    '''
    Manager class for handling creating and deleting cache keys based on API view events
    '''

    view_key_format = '{namespace}:view:{path}'

    def __init__(self, app=None, with_jinja2_ext=True, config=None, signaler=None):
        self.signaler = signaler
        super(Cache, self).__init__(app=app, with_jinja2_ext=with_jinja2_ext, config=config)

    def init_app(self, app, config=None):
        self.app = app
        if config is None:
            config = self.config

        if config is None:
            config = app.config

        config.setdefault('CARAFE_CACHE_ENABLED', True)
        config.setdefault('CARAFE_CACHE_IGNORED_REQUEST_ARGS', [])

        if config['CARAFE_CACHE_ENABLED']:
            super(Cache, self).init_app(app, config=config)

            if self.signaler:
                self.connect_signals()

    def connect_signals(self):
        # @note: have to keep a handle on the signal for the receive event to work (not sure why exactly)
        # not ok: self.signaler.<signal>.connect(self.<method>)
        # ok: self.<signal_name> = self.signaler.<signal>
        #     self.<signal_name>.connect(self.<method>)

        # connect receivers
        self.signaler.after_post.connect(self.after_post)
        self.signaler.after_put.connect(self.after_put)
        self.signaler.after_patch.connect(self.after_patch)
        self.signaler.after_delete.connect(self.after_delete)

    def get_cache_namespace(self, obj):
        if getattr(obj, 'cache_namespace', None) is not None:
            return obj.cache_namespace
        elif hasattr(obj, '__name__'):
            return obj.__name__
        else:
            return obj.__class__.__name__

    @property
    def client(self):
        '''Proxy to cache client wrapper.'''
        return self.cache if self.enabled else None

    @property
    def server(self):
        '''Proxy to cache server client.'''
        return getattr(self.cache, '_client', None) if self.enabled else None

    @property
    def enabled(self):
        return current_app.config['CARAFE_CACHE_ENABLED']

    def clear_keys(self, pipe, *keys, **kargs):
        '''Clear specified keys'''
        if not keys:
            return

        execute = kargs.get('execute')

        keys = [current_app.config['CACHE_KEY_PREFIX'] + k for k in keys]
        pipe.delete(*keys)

        if execute:
            pipe.execute()

        return True

    def clear_prefix(self, pipe, *prefixes, **kargs):
        '''Clear keys starting with prefix'''
        keys = []
        for prefix in prefixes:
            keys.extend(pipe.keys(prefix + '*'))

        return self.clear_keys(pipe, *keys, **kargs)

    def clear(self, prefixes=None, keys=None):
        '''
        Clear cache keys using an optional prefix, regex, and/or list of keys

        :param string prefix: prefix to append to global CACHE_KEY_PREFIX
        :param string regex: regex to filter keys matched by CACHE_KEY_PREFIX + prefix
        :param list keys: additional keys to delete during pipeline transaction
        '''
        if not self.enabled:
            return

        if not any([prefixes, keys]):
            # this is the same as clearing the entire cache
            return self.cache.clear()

        if not hasattr(self.server, 'pipeline'):
            # enhanced cache clearing is only supported using redis
            return self.cache.clear()

        if prefixes is None:
            prefixes = []

        if keys is None:
            keys = []

        with self.server.pipeline() as pipe:
            self.clear_prefix(pipe, *prefixes)
            self.clear_keys(pipe, *keys)
            pipe.execute()

        return True

    def cached_view(self, timeout=None, namespace=None, unless=None, include_request_args=True):
        '''
        Wrapper around self.cached which itself is a decorator.
        We're wrapping because we want to have access to the class instance of the view in order to namespace the key.
        We can't always namespace using key_prefix since some cache decorators are placed around parent classes which
        don't know anything about the child class.
        '''

        def wrap(f):
            @wraps(f)
            def wrapper(*args, **kargs):
                if not self.enabled:
                    return f(*args, **kargs)

                if namespace is not None:
                    # make namespace available in case `f` is used as signal sender
                    # mainly used to get namespace when invalidating cache keys via namespace prefix
                    f.cache_namespace = namespace

                # if args[0] is set, then this is a class based view, else use function
                obj = args[0] if args else f
                cache_namespace = self.get_cache_namespace(obj)
                view_path = self.create_view_path(include_request_args)
                key_prefix = self.view_key_format.format(namespace=cache_namespace, path=view_path, **request.view_args)

                cached = self.cached(timeout=timeout, key_prefix=key_prefix, unless=unless)(f)

                try:
                    # cache server could be down
                    result = cached(*args, **kargs)
                except Exception as e: # pragma: no cover
                    # return function call instead
                    result = f(*args, **kargs)
                    current_app.logger.exception(e)

                return result

            return wrapper

        return wrap

    def create_view_path(self, include_request_args=False):
        '''Construct view path from request.path with option to include GET args'''
        href = urls.Href(request.path)

        if include_request_args:
            args = {k:v for k, v in request.args.iteritems() if k not in current_app.config['CARAFE_CACHE_IGNORED_REQUEST_ARGS']}
        else:
            args = None

        return href(args)

    def on_modified_record(self, sender):
        '''Common tasks to perform when a record is modified'''
        namespace = self.get_cache_namespace(sender)
        prefixes = [self.view_key_format.format(namespace=namespace, path='')]

        # append cascade keys which should be invalidated (typically due to this API's records being used in other APIs)
        prefixes += getattr(sender, 'cache_cascade', [])

        try:
            self.clear(prefixes=prefixes)
        except Exception as e: # pragma: no cover
            current_app.logger.exception(e)

    def after_post(self, sender):
        '''Handle the `after_post` event. Executed after a ModelAPI POST request.'''
        self.on_modified_record(sender)

    def after_put(self, sender):
        '''Handle the `after_put` event. Executed after a ModelAPI PUT request.'''
        self.on_modified_record(sender)

    def after_patch(self, sender):
        '''Handle the `after_patch` event. Executed after a ModelAPI PATCH request.'''
        self.on_modified_record(sender)

    def after_delete(self, sender):
        '''Handle the `after_delete` event. Executed after a ModelAPI DELETE request.'''
        self.on_modified_record(sender)

