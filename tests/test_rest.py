
import carafe
from carafe.rest import RestCtrl
from carafe.ext.classy import register_view, route, RestView
from carafe.core import cache
from carafe.utils import classproperty

from .base import TestBase

data = {i: {'_id': i} for i in xrange(0, 10)}

class MockDB(object):
    def __init__(self):
        self.exception_on_commit = False

    def add(self, *items):
        pass

    def commit(self):
        if self.exception_on_commit:
            raise Exception('Mock exception')

    def rollback(self):
        pass

    @property
    def session(self):
        return self

db = MockDB()

class MockModel(object):

    def __init__(self, strict=False, **data):
        self.data = data

    def update(self, data, strict=False):
        self.data.update(data)

    @classproperty
    def query(cls):
        return MockQuery()

    @classmethod
    def get(cls, _id):
        _id = int(_id)
        return data.get(_id)

    def to_dict(self):
        return self.data

class MockQuery(object):
    def search(self, search_string, search_dict, limit, offset):
        return MockResults(data.values()[offset:limit])

    def filter_by(self, **kargs):
        return self

    def lazyload(self, *args, **kargs):
        return self

    def delete(self):
        return True

class MockResults(object):
    def __init__(self, data):
        self.data = data

    def all(self):
        return self.data

class Ctrl(RestCtrl):
    __model__ = MockModel

class View(RestView):
    route_base = 'view'

    __controller__ = Ctrl

    dict_namespace = 'data'

    @property
    def controller(self):
        return self.__controller__(db=db)

class TestRestBase(TestBase):
    __client_class__ = carafe.JSONClient

    def setUp(self):
        register_view(self.app, View)

class TestRest(TestRestBase):
    def test_index(self):
        res = self.client.get('/view')
        self.assert200(res)
        self.assertEqual(res.json['data'], data.values())

    def test_index_limit(self):
        limit = 5
        res = self.client.get('/view', params={'limit': limit})
        self.assert200(res)
        self.assertEqual(len(res.json['data']), limit)

    def test_index_offset(self):
        offset = 5
        res = self.client.get('/view', params={'offset': offset})
        self.assert200(res)
        self.assertEqual(res.json['data'], data.values()[offset:])

    def test_get(self):
        res = self.client.get('/view/1')
        self.assert200(res)
        self.assertEqual(res.json['data'], data.get(1))

    def test_get_404(self):
        res = self.client.get('/view/{0}'.format(max(data)+1))
        self.assert404(res)

    def test_post(self):
        record = {'_id': max(data)+1}
        res = self.client.post('/view', data=record)
        self.assert200(res)
        self.assertEqual(res.json['data'], record)

    def test_put(self):
        record = {'name': 'put'}
        res = self.client.put('/view/1', data=record)
        self.assert200(res)
        self.assertEqual(res.json['data']['name'], record['name'])

    def test_patch(self):
        record = {'name': 'patch'}
        res = self.client.patch('/view/1', data=record)
        self.assert200(res)
        self.assertEqual(res.json['data']['name'], record['name'])

    def test_delete(self):
        res = self.client.delete('/view/1')
        self.assert200(res)
        self.assertEqual(res.json['data'], True)

    def test_commit_exception(self):
        db.exception_on_commit = True

        res = self.client.put('/view/1', data={})
        self.assert400(res)

        db.exception_on_commit = False

