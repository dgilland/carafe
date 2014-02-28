
from functools import wraps

from flask import request, abort
from flask.ext.classy import FlaskView, _FlaskViewMeta, route

from .json import jsonify
from .signaler import signaler
from ..utils import url_join, _to_dict, camelcase_to_underscore

def register_view(app, classes, route_prefix='', route_base='', subdomain=None, trailing_slash=False, replace_prefix=False, replace_base=False):
    '''
    Register a group of FlaskView based classes.

    If `replace_prefix` or `replace_base` is True, then
    class route_<...> is replaced instead of extended.
    '''

    if not isinstance(classes, list):
        classes = [classes]

    _prefix = []
    if route_prefix:
        _prefix.append(route_prefix)

    _base = []
    if route_base:
        _base.append(route_base)

    for cls in classes:
        prefix = _prefix[:]
        base = _base[:]

        if cls.route_prefix is not None and not replace_prefix:
            prefix.append(cls.route_prefix)

        if cls.route_base is not None and not replace_base:
            base.append(cls.route_base)

        cls.register(
            app,
            route_prefix=url_join(prefix),
            route_base=url_join(base),
            subdomain=subdomain,
            trailing_slash=trailing_slash
        )

def to_dict(f):
    '''Simple wrapper around `_to_dict` which supports namespacing as defined at the class level'''
    @wraps(f)
    def decorated(*args, **kargs):
        self = args[0]
        namespace = self._dict_namespace
        data = f(*args, **kargs)
        return _to_dict(data, namespace=namespace)
    return decorated

def noop(*args, **kargs):
    pass

class MetaView(_FlaskViewMeta):
    def __new__(cls, name, bases, dct):
        if 'permissions' in dct:
            # if permissions dict defined on class,
            # then set corresponding permissions keys on class dict
            # and decorate with supplied functions
            for method, permissions in dct['permissions'].iteritems():
                dct[method] = dct.get(method, noop)

                if not isinstance(permissions, list):
                    permissions = [permissions]

                for permission in permissions:
                    dct[method] = permission(dct[method])

        return type.__new__(cls, name, bases, dct)

class BaseView(FlaskView):
    __metaclass__ = MetaView

    # route prefix
    route_prefix = None

    # set route_base to '' to disable FlaskView's auto-routing from class name
    route_base = ''

    # controller class which has hooks for index(), get(), post(), put(), patch(), and delete()
    __controller__ = None

    # namespace to apply to returned data when returning json response
    dict_namespace = None

    # set this to override automatic cache namespace generation from class name
    cache_namespace = None

    # when invalidating this class' cache keys, also invalidate cache keys with these namespaces
    cache_cascade = []

    # @note: originally wanted to place the `to_dict` decorator here,
    # but, alas poor Yorick, the `self` needs to be passed in and that won't happen here.
    # so have to use the `@to_dict` syntax around the method def instead.
    decorators = [jsonify]

    # assign permissions to instance methods
    # `keys` correspond to method that has permission requirements
    # `values` can be a single permission function or a list of functions which will wrap/decorate method
    # e.g.
    #   permissions = {
    #       'before_post': auth.require.admin(401),
    #       'delete': [auth.require.admin(403), auth.require.auth(401)]
    #   }
    # @note: be aware that permissions are merged when subclassing
    # so if a parent class defines a partial set of permissions,
    # the subclass will have all the parent permissions as well as its own.
    # however, if a subclass overwrites a parent permission, the subclass
    # permission will be the only one used.
    # essentially, subclasses is like calling `Parent.permissions.update(Subclass.permissions)`
    permissions = {}

    @property
    def request(self):
        '''Proxy to request object'''
        return request

    @property
    def _dict_namespace(self):
        namespace = getattr(self, 'dict_namespace', None)

        if namespace is None:
            class_name = self.__class__.__name__
            if class_name.lower().endswith('view'):
                class_name = class_name[:-4]
            namespace = camelcase_to_underscore(class_name)

        return namespace

    @property
    def controller(self):
        # override as needed for custom initialization
        return self.__controller__()

    def after_request(self, name, response):
        # send `after_<http-method>` signal
        signaler.send('after_' + request.method.lower(), self)

        return response

    def _to_dict(self, data):
        return _to_dict(data, namespace=self._dict_namespace)

    def _results_or_404(self, results):
        if results is None:
            abort(404)
        return results

# @note: Each of the Rest endpoints below comes with a corresponding `_<method>` function.
# The purpose of this is to make it easier to subclass a method without then having to also
# duplicate the decoratores applied to the public method. Also, in the event that caching
# is enabled on an endpoint and another endpoint needs a non-cached version, or if `super()`
# needs to be called, then the `_<method>` function can be used to bypass the cache.

class ReadView(BaseView):
    '''REST read endpoints'''

    def index(self):
        return self._to_dict(self._index())

    def _index(self):
        return self.controller.index(params=self.request.args)

    def get(self, _id):
        return self._to_dict(self._get(_id))

    def _get(self, _id):
        results = self.controller.get(_id=_id)
        return self._results_or_404(results)

class WriteView(BaseView):
    '''REST write endpoints'''

    def post(self):
        return self._to_dict(self._post())

    def _post(self):
        return self.controller.post(self.request.data)

    def put(self, _id):
        return self._to_dict(self._put(_id))

    def _put(self, _id):
        results = self.controller.put(_id, self.request.data)
        return self._results_or_404(results)

    def patch(self, _id):
        return self._to_dict(self._patch(_id))

    def _patch(self, _id):
        ctrl = self.controller
        results = getattr(ctrl, 'patch', ctrl.put)(_id, self.request.data)
        return self._results_or_404(results)

    def delete(self, _id):
        return self._to_dict(self._delete(_id))

    def _delete(self, _id):
        results = self.controller.delete(_id)
        return self._results_or_404(results)

class RestView(ReadView, WriteView):
    '''REST read/write endpoints'''
    pass

