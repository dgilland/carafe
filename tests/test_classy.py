
from time import sleep

from flask import request, session

import carafe
from carafe.ext.classy import register_view, route, BaseView, ReadView, WriteView, RestView, to_dict, url_join
from carafe.core import auth, cache

from .base import TestBase
from .test_auth import TestAuthBase
from .test_cache import TestCacheBase

class DictClass(object):
    def __init__(self, data):
        self.data = data

    def to_dict(self):
        return self.data

class Ctrl(object):
    data = {
        1: {'name': 'Joe'},
        2: {'name': 'James'},
        3: {'name': 'Jack'},
        4: {'name': 'John'},
        5: {'name': 'Jill'},
    }

    def index(self, params=None):
        return self.data.values()

    def get(self, _id):
        _id = int(_id)
        return self.data.get(_id)

    def post(self, data):
        self.data[max(self.data.keys())+1] = data
        return data

    def put(self, _id, data):
        _id = int(_id)
        if _id in self.data:
            self.data[_id].update(data)
            return self.data[_id]
        else:
            return None

    def patch(self, _id, data):
        _id = int(_id)
        return self.put(_id, data)

    def delete(self, _id):
        _id = int(_id)
        if _id in self.data:
            del self.data[_id]
            return True
        else:
            return None

class PermissionsCtrl(Ctrl):
    data = Ctrl.data.copy()

    def delete(self, _id):
        return True

responses = {
    'index': {'index': True},
    'foo': {'foo': True}
}

class TestClassyBase(TestBase):
    __client_class__ = carafe.JsonClient

class TestClassyRegister(TestClassyBase):

    class View1(BaseView):
        route_prefix = '/prefix/'
        route_base = '/base'

        def index(self):
            return responses['index']

    class View2(BaseView):
        @route('/foo/')
        def foo(self):
            return responses['foo']

    def assertResponse(self, name, url):
        res = self.client.get(url)
        self.assert200(res)
        self.assertEqual(res.json, responses[name])

    def test_register_basic(self):
        register_view(self.app, self.View1)

        self.assertResponse('index', '/prefix/base')

    def test_register_with_prefix(self):
        register_view(self.app, [self.View1, self.View2], route_prefix='api')

        self.assertResponse('index', '/api/prefix/base')
        self.assertResponse('foo', '/api/foo/')

    def test_register_with_base(self):
        register_view(self.app, [self.View1, self.View2], route_base='bar')

        self.assertResponse('index', '/prefix/bar/base')
        self.assertResponse('foo', '/bar/foo/')

    def test_register_with_prefix_and_base(self):
        register_view(self.app, [self.View1, self.View2], route_prefix='api', route_base='bar')

        self.assertResponse('index', '/api/prefix/bar/base')
        self.assertResponse('foo', '/api/bar/foo/')

    def test_register_with_prefix_replace(self):
        register_view(self.app, [self.View1, self.View2], route_prefix='api', replace_prefix=True)

        self.assertResponse('index', '/api/base')
        self.assertResponse('foo', '/api/foo/')

    def test_register_with_base_replace(self):
        register_view(self.app, [self.View1, self.View2], route_base='bar', replace_base=True)

        self.assertResponse('index', '/prefix/bar')
        self.assertResponse('foo', '/bar/foo/')

    def test_register_with_prefix_and_base_replace(self):
        register_view(self.app, [self.View1, self.View2], route_prefix='api', route_base='bar', replace_prefix=True, replace_base=True)

        self.assertResponse('index', '/api/bar')
        self.assertResponse('foo', '/api/bar/foo/')

    def test_register_with_trailing_slash(self):
        register_view(self.app, [self.View1], route_prefix='api', route_base='bar', trailing_slash=True)

        self.assertResponse('index', '/api/prefix/bar/base/')

class TestClassyToDict(TestClassyBase):
    class View(BaseView):
        @to_dict
        def index(self):
            return DictClass(responses['index'])

    def test_to_dict(self):
        self.View.register(self.app, route_base='/')
        res = self.client.get('/')
        self.assert200(res)
        self.assertEqual(res.json, {'': responses['index']})

class TestClassyRestBase(TestClassyBase):
    class View(RestView):
        __controller__ = Ctrl
        route_base = 'view'

    def setUp(self):
        self.original_data = self.data.copy()
        register_view(self.app, self.View, trailing_slash=True)

    def tearDown(self):
        self.data = self.original_data

    @property
    def data(self):
        return self.View.__controller__.data

    @data.setter
    def data(self, data):
        self.View.__controller__.data = data

class TestClassyRestView(TestClassyRestBase):
    def test_index(self):
        res = self.client.get('/view/')
        self.assert200(res)
        self.assertEqual(res.json, {'': self.data.values()})

    def test_get(self):
        _id = 1
        res = self.client.get('/view/{0}'.format(_id))
        self.assert200(res)
        self.assertEqual(res.json, {'': self.data.get(_id)})

    def test_get_no_results(self):
        res = self.client.get('/view/-1')
        self.assert404(res)

    def test_post(self):
        data = {'name': 'Joan'}
        res = self.client.post('/view/', data=data)
        self.assert200(res)
        self.assertEqual(res.json, {'': self.data.get(max(self.data.keys()))})

    def test_put(self):
        _id = 1
        data = {'name': 'Jordan'}
        res = self.client.put('/view/{0}'.format(_id), data=data)
        self.assert200(res)
        self.assertEqual(res.json, {'': self.data.get(_id)})

    def test_patch(self):
        _id = 1
        data = {'name': 'Jamal'}
        res = self.client.patch('/view/{0}'.format(_id), data=data)
        self.assert200(res)
        self.assertEqual(res.json, {'': self.data.get(_id)})

    def test_delete(self):
        _id = 1
        res = self.client.delete('/view/{0}'.format(_id))
        self.assert200(res)
        self.assertEqual(res.json, {'': True})

class TestClassyDictNamespace(TestClassyRestBase):
    class View(RestView):
        __controller__ = Ctrl
        route_base = 'view'
        dict_namespace = 'mynamespace'

    def test_index_namespace(self):
        res = self.client.get('/view/')
        self.assert200(res)
        self.assertEqual(res.json, {self.View.dict_namespace: self.data.values()})

class TestClassyPermissions(TestAuthBase):
    class PermissionsView(RestView):
        __controller__ = PermissionsCtrl
        route_base = 'permissions'
        permissions = {
            'before_post': [auth.require.admin(401)],
            'before_put': auth.require.manager(403),
            'before_delete': [auth.require.admin(401), auth.require.manager(403)],
        }

    def endpoint(self, *args):
        return url_join('/', self.PermissionsView.route_base, *args)

    def setUp(self):
        super(TestClassyPermissions, self).setUp()
        register_view(self.app, self.PermissionsView)

    def tearDown(self):
        self.logout()

    def test_unrestricted(self):
        self.assert200(self.client.get(self.endpoint()))
        self.assert200(self.client.get(url_join(self.endpoint('1'))))

    def test_restricted_post(self):
        endpoint = self.endpoint()

        # not logged in
        self.assert401(self.client.post(endpoint, {}))

        # log in with user who doesn't have proper permissions
        self.login(self.regular_user_id)
        self.assert401(self.client.post(endpoint, {}))

        # log in with proper user
        self.logout()
        self.login(self.admin_user_id)
        self.assert200(self.client.post(endpoint, {}))

    def test_restricted_put(self):
        endpoint = self.endpoint('1')

        # not logged in
        self.assert403(self.client.put(endpoint, {}))

        # log in with user who doesn't have proper permissions
        self.login(self.regular_user_id)
        self.assert403(self.client.put(endpoint, {}))

        # log in with proper user
        self.logout()
        self.login(self.manager_user_id)
        self.assert200(self.client.put(endpoint, {}))

    def test_restricted_delete(self):
        endpoint = self.endpoint('1')

        # not logged in
        self.assert403(self.client.delete(endpoint))

        # log in with user who doesn't have proper permissions
        self.login(self.manager_user_id)
        self.assert401(self.client.delete(endpoint))

        # log in with proper user
        self.logout()
        self.login(self.admin_user_id)
        self.assert200(self.client.delete(endpoint))

class TestClassyCache(TestCacheBase):
    class CachedView(RestView):
        route_base = 'cached'

        tracker = {}

        @cache.cached_view(timeout=0.25)
        def index(self):
            self.tracker.setdefault('count', 0)
            self.tracker['count'] += 1
            return self.tracker

    def setUp(self):
        register_view(self.app, self.CachedView)

    def tearDown(self):
        self.CachedView.tracker.clear()

    def test_cached_view(self):
        count = self.client.get('/cached').json['count']
        test_count = self.client.get('/cached').json['count']

        self.assertEqual(test_count, count)

        sleep(0.25)
        test_count = self.client.get('/cached').json['count']
        self.assertNotEqual(test_count, count)
