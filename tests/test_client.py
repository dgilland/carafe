
from flask import request
from carafe import Client, JSONClient
from carafe.utils import jsonify

from .base import TestBase


class TestClientBase(TestBase):
    def setUp(self):
        @self.app.route('/', methods=['GET', 'POST', 'PATCH', 'PUT', 'DELETE'])
        def index():
            return {'data': request.get_dict(), 'params': request.args}


class TestClient(TestClientBase):
    __client_class__ = Client

    # use string value since they'll be converted to string during transmission
    data = {'x': '1', 'y': '2'}
    params = {'a': '3', 'b': '4'}

    def test_get_params(self):
        self.assertEqual(self.client.get('/', self.params).json['params'], self.params)
        self.assertEqual(self.client.get('/', params=self.params).json['params'], self.params)

    def test_post(self):
        self.assertEqual(self.client.post('/', self.data).json['data'], self.data)
        self.assertEqual(self.client.post('/', data=self.data).json['data'], self.data)

    def test_put(self):
        self.assertEqual(self.client.put('/', self.data).json['data'], self.data)
        self.assertEqual(self.client.put('/', data=self.data).json['data'], self.data)

    def test_patch(self):
        self.assertEqual(self.client.patch('/', self.data).json['data'], self.data)
        self.assertEqual(self.client.patch('/', data=self.data).json['data'], self.data)


class TestJSONClient(TestClientBase):
    __client_class__ = JSONClient

    # use number values since their type should be preserved via json conversion
    data = {'x': 1, 'y': 2}

    def test_dict_to_json_conversion(self):
        '''Test that client accepts dict object for data attribute'''
        self.assertEqual(self.client.post('/', self.data).json['data'], self.data)

    def test_invalid_conversion(self):
        '''Test that invalid data is not converted'''
        invalid = {'x': object(), 'y': 2}
        self.assertEqual(self.client.post('/', invalid).json['data'], {})
