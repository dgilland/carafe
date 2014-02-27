
from time import sleep, time
import re

from flask.views import MethodView

import carafe
from carafe.core import cache, signaler, jsonify

from .base import TestBase

def register_view(app, view, endpoint, url, pk='_id', pk_type='int'):
    view_func = view.as_view(endpoint)
    app.add_url_rule(url, defaults={pk: None}, view_func=view_func, methods=['GET',])
    app.add_url_rule(url, view_func=view_func, methods=['POST',])
    app.add_url_rule('%s<%s:%s>' % (url, pk_type, pk), view_func=view_func, methods=['GET', 'PUT', 'PATCH', 'DELETE'])


class TestCacheBase(TestBase):
    class __config__(object):
        CACHE_TYPE = 'simple'
        CACHE_KEY_PREFIX = ''

    __client_class__ = carafe.JsonClient

    # need to mock a cache server similar to redis to fully test cache clearing functionality
    class MockCacheServer(object):
        class MockPipeline(object):
            def __init__(self, cache):
                self._cache = cache

            def __enter__(self):
                return self

            def __exit__(self, *args, **kargs):
                pass

            def keys(self, search=None):
                if search:
                    # replace '*' search with re equivalent
                    search = re.sub('\*', '.+', search)
                    r = re.compile(search)
                    return [k for k in self._cache.keys() if r.match(k)]
                else:
                    return self._cache.keys()

            def delete(self, *keys):
                for k in keys:
                    if k in self._cache.keys():
                        del self._cache[k]

            def execute(self):
                pass

        def pipeline(self):
            self._cache = cache.client._cache
            return self.MockPipeline(self._cache)

    def setUp(self):
        @self.app.route('/')
        @cache.cached_view(timeout=1)
        def index():
            return ''

        @self.app.route('/<_id>')
        @cache.cached_view(timeout=1)
        def index_id(_id):
            return ''

    def cache_keys(self):
        return cache.client._cache.keys() if cache.enabled else None

class TestCache(TestCacheBase):

    def test_cached_view_basic(self):
        timeout = 0.5
        tracker = {'count': 0}

        class MyView(MethodView):
            @jsonify
            @cache.cached_view(timeout=timeout)
            def get(self, _id):
                tracker['count'] += 1
                return tracker

        register_view(self.app, MyView, 'my_view', '/myview/')

        results = []
        expected = []

        # increment count
        results.append(self.client.get('/myview/').json['count'])
        expected.append(1)

        # subsequent call falls within cached timeout so count shouldn't change
        results.append(self.client.get('/myview/').json['count'])
        expected.append(1)

        # cache key based on default key format using class name as prefix
        cache_keys = self.cache_keys()
        self.assertIn('MyView:view:/myview/', self.cache_keys())

        # sleep so cache expires
        sleep(timeout)

        # increment count
        results.append(self.client.get('/myview/').json['count'])
        expected.append(2)

        self.assertEqual(results, expected)

    def test_cached_view_explicit_namespace(self):
        @self.app.route('/custom')
        @cache.cached_view(namespace='mynamespace')
        def custom():
            return ''

        self.assertEqual(len(self.cache_keys()), 0)

        self.client.get('/')
        self.client.get('/custom')

        cache_keys = self.cache_keys()

        self.assertIn('index:view:/', cache_keys)
        self.assertIn('mynamespace:view:/custom', cache_keys)

    def test_cached_view_include_request_args(self):
        @self.app.route('/noviewargs')
        @cache.cached_view(include_request_args=False)
        def noviewargs():
            return ''

        params = {'a': 'a', 'b': 'b'}
        # index route includes get args in cache
        self.client.get('/', params=params)

        # custom route above does not
        self.client.get('/noviewargs', params=params)

        cache_keys = self.cache_keys()

        self.assertIn('index:view:/?a=a&b=b', cache_keys)
        self.assertIn('noviewargs:view:/noviewargs', cache_keys)

class TestCacheClear(TestCacheBase):

    def setUp(self):
        cache.cache._client = self.MockCacheServer()

        @self.app.route('/foo')
        @cache.cached_view(namespace='foo')
        def foo():
            return str(time())

        @self.app.route('/bar')
        @cache.cached_view(namespace='bar')
        def bar():
            return ''

        @self.app.route('/baz')
        @cache.cached_view(namespace='baz')
        def baz():
            return ''

        # generate cache entries
        params = {'a': 'a'}
        for route in ['/foo', '/bar', '/baz']:
            self.client.get(route)
            self.client.get(route, params=params)

    def test_clear(self):
        self.assertTrue(len(self.cache_keys()) > 0)
        cache.clear()
        self.assertTrue(len(self.cache_keys()) == 0)

    def test_clear_prefix(self):
        self.assertTrue(len(self.cache_keys()) > 0)
        count_cache_keys = len(self.cache_keys())
        prefix = 'bar'
        keys = set([key for key in self.cache_keys() if key.startswith(prefix)])

        self.assertEqual(len(keys), 2)

        cache.clear(prefixes=[prefix])

        self.assertEqual(len(self.cache_keys()), (count_cache_keys-len(keys)))

        for key in keys:
            self.assertNotIn(key, self.cache_keys())

    def test_clear_keys(self):
        self.assertTrue(len(self.cache_keys()) > 0)
        count_cache_keys = len(self.cache_keys())

        keys = set(['foo:view:/foo?a=a', 'foo:view:/foo'])
        self.assertTrue(keys.issubset(self.cache_keys()))

        cache.clear(keys=keys)

        self.assertEqual(len(self.cache_keys()), (count_cache_keys-len(keys)))

        for key in keys:
            self.assertNotIn(key, self.cache_keys())

    def test_clear_all(self):
        self.assertTrue(len(self.cache_keys()) > 0)
        count_cache_keys = len(self.cache_keys())

        keys = set(['foo:view:/foo?a=a', 'foo:view:/foo'])
        prefix = 'bar'
        regex = 'a=a'
        r = re.compile(regex)

        prefix_keys = set([key for key in self.cache_keys() if key.startswith(prefix)])

        self.assertEqual(len(prefix_keys), 2)

        cache.clear(prefixes=[prefix], keys=keys)

        self.assertEqual(len(self.cache_keys()), (count_cache_keys-(len(keys)+len(prefix_keys))))

        for key in keys | prefix_keys:
            self.assertNotIn(key, self.cache_keys())

    def test_reduced_functionality(self):
        cache.cache._client = None
        self.assertTrue(len(self.cache_keys()) > 0)
        cache.clear(prefixes=['nonmatchingprefix'])
        self.assertTrue(len(self.cache_keys()) == 0)

    def test_cache_disabled(self):
        # verify data is cached
        foo_data = self.client.get('/foo').data
        sleep(0.5)
        self.assertEqual(self.client.get('/foo').data, foo_data)

        self.app.config['CARAFE_CACHE_ENABLED'] = False

        # cache keys exist since cache was accessed prior to disabling
        cached = cache.cache._cache.copy()
        self.assertTrue(len(cached.keys()) > 0)

        # no cache client
        self.assertIsNone(cache.client)

        # clear does nothing
        cache.clear()
        self.assertEqual(cached, cache.cache._cache)

        # caching access doesn't work
        self.client.get('/foo', params={'cache_buster': 'foo'})
        self.assertEqual(cached, cache.cache._cache)

        # cached values aren't returned
        sleep(0.5)
        self.assertNotEqual(self.client.get('/foo').data, foo_data)

    def test_clear_keys_execute(self):
        count = len(self.cache_keys())
        self.assertTrue(count > 0)
        key = self.cache_keys()[0]
        cache.clear_keys(cache.server.pipeline(), key, execute=True)
        self.assertNotIn(key, self.cache_keys())

class TestCacheCascade(TestCacheBase):
    def setUp(self):
        cache.cache._client = self.MockCacheServer()

        class RestView(MethodView):
            tracker = {}

            cache_cascade = ['CascadeView']

            @cache.cached_view()
            def get(self, _id):
                key = 'get' if _id else 'index'
                self.tracker.setdefault(key, 0)
                self.tracker[key] += 1
                return ''

            def post(self):
                signaler.after_post.send(self)
                return ''

            def put(self, _id):
                signaler.after_put.send(self)
                return ''

            def patch(self, _id):
                signaler.after_patch.send(self)
                return ''

            def delete(self, _id):
                signaler.after_delete.send(self)
                return ''

        class CascadeView(RestView):
            tracker = {}

        class AnotherRestView(RestView):
            tracker = {}

        self.RestView = RestView
        self.CascadeView = CascadeView
        self.AnotherRestView = AnotherRestView

        register_view(self.app, RestView, 'rest', '/rest/')
        register_view(self.app, CascadeView, 'cascade', '/cascade/')
        register_view(self.app, AnotherRestView, 'another', '/another/')

        # add cache entries for `another` so selective cache cascade is tested (i.e. these keys shouldn't be cleared)
        self.client.get('/another/')
        self.client.get('/another/1')

        # add cache entires for 'rest' to demonstrate cache cascade
        self.client.get('/rest/')
        self.client.get('/rest/1')

        self.client.get('/cascade/')
        self.client.get('/cascade/1')

        self.assertEqual(len(self.cache_keys()), 6)

        self.assertEqual(RestView.tracker['index'], 1)
        self.assertEqual(RestView.tracker['get'], 1)

        # re-accessing doesn't increase tracker hits
        self.client.get('/rest/')
        self.client.get('/rest/1')

        self.assertEqual(RestView.tracker['index'], 1)
        self.assertEqual(RestView.tracker['get'], 1)

        self.assertEqual(len(self.cache_keys()), 6)
        self.assertEqual(self.len_prefix_keys('RestView'), 2)
        self.assertEqual(self.len_prefix_keys('CascadeView'), 2)

    def tearDown(self):
        self.RestView.tracker.clear()
        self.CascadeView.tracker.clear()
        self.AnotherRestView.tracker.clear()

    def len_prefix_keys(self, prefix):
        return len([k for k in self.cache_keys() if k.startswith(prefix)])

    def assertKeyPrefixEmpty(self, prefix):
        self.assertEqual(self.len_prefix_keys(prefix), 0)

    def test_after_post(self):
        self.client.post('/rest/', {})

        self.assertKeyPrefixEmpty('RestView')
        self.assertKeyPrefixEmpty('CascadeView')
        self.assertEqual(len(self.cache_keys()), 2)

    def test_after_put(self):
        self.client.put('/rest/1', {})

        self.assertKeyPrefixEmpty('RestView')
        self.assertKeyPrefixEmpty('CascadeView')
        self.assertEqual(len(self.cache_keys()), 2)

    def test_after_patch(self):
        self.client.patch('/rest/1', {})

        self.assertKeyPrefixEmpty('RestView')
        self.assertKeyPrefixEmpty('CascadeView')
        self.assertEqual(len(self.cache_keys()), 2)

    def test_after_delete(self):
        self.client.delete('/rest/1')

        self.assertKeyPrefixEmpty('RestView')
        self.assertKeyPrefixEmpty('CascadeView')
        self.assertEqual(len(self.cache_keys()), 2)

