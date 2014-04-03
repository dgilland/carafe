
from functools import wraps

from flask import request, abort, current_app
from flask.ext.classy import FlaskView, route

from .signaler import signaler
from ..utils import urlpathjoin, _to_dict, camelcase_to_underscore


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
            route_prefix=urlpathjoin(prefix),
            route_base=urlpathjoin(base),
            subdomain=subdomain,
            trailing_slash=trailing_slash
        )

def to_dict(func):
    '''Wrapper around `self._to_dict` which supports namespacing as defined at the class level.'''
    @wraps(func)
    def decorated(*args, **kargs):
        data = func(*args, **kargs)

        if not isinstance(data, current_app.response_class):
            # only convert to dict if function return is not Response

            # if decorator called from FlaskView.decorators[],
            # `self` won't be passed in so we need to get it from `func`
            if hasattr(func, 'im_self'):
                self = func.im_self
            else:
                self = args[0]

            data = self._to_dict(data)

        return data
    return decorated


def noop(*args, **kargs):
    pass


class MetaView(type):
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

    # universal decorators applied to all view routes
    decorators = []

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

        if namespace is True:
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

    def _index(self):
        return self.controller.index(params=self.request.args)

    def _get(self, _id):
        results = self.controller.get(_id=_id)
        return self._results_or_404(results)

    def _post(self):
        return self.controller.post(self.request.data)

    def _put(self, _id):
        results = self.controller.put(_id, self.request.data)
        return self._results_or_404(results)

    def _patch(self, _id):
        ctrl = self.controller
        results = getattr(ctrl, 'patch', ctrl.put)(_id, self.request.data)
        return self._results_or_404(results)

    def _delete(self, _id):
        results = self.controller.delete(_id)
        return self._results_or_404(results)


# @note: Each of the Rest endpoints below comes with a corresponding `_<method>` function.
# The purpose of this is to make it easier to subclass a method without then having to also
# duplicate the decoratores applied to the public method. Also, in the event that caching
# is enabled on an endpoint and another endpoint needs a non-cached version, or if `super()`
# needs to be called, then the `_<method>` function can be used to bypass the cache.

class RestView(BaseView):
    '''REST read/write endpoints'''

    decorators = [to_dict]

    def index(self):
        return self._index()

    def get(self, _id):
        return self._get(_id)

    def post(self):
        return self._post()

    def put(self, _id):
        return self._put(_id)

    def patch(self, _id):
        return self._patch(_id)

    def delete(self, _id):
        return self._delete(_id)
