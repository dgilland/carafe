
import json
from flask import request

from carafe.core import jsonify

from .base import TestBase

class TestRequest(TestBase):
    '''Test custom request class'''

    data = {'foo': 'bar'}
    data_json = json.dumps(data)

    def setUp(self):
        super(TestRequest, self).setUp()

        # define echo route here so each test can access it
        @self.app.route('/', methods=['POST'])
        def index():
            return request.get_dict()

    def test_get_dict_json(self):
        '''Test request.get_dict() function with correct content_type'''
        result = self.client.post('/', data=self.data_json, content_type='application/json').json
        self.assertEqual(result, self.data)

    def test_get_dict_json_no_content_type(self):
        '''Test request.get_dict() function with no content type specified'''
        result = self.client.post('/', data=self.data_json).json
        self.assertEqual(result, self.data)

    def test_get_dict_json_wrong_content_type(self):
        '''Test request.get_dict() function with wrong content type'''
        result = self.client.post('/', data=self.data_json, content_type='text').json
        self.assertEqual(result, self.data)

    def test_get_dict_fallback_form_urlencoded(self):
        '''Test request.get_dict() function using form-urlencoded content type'''
        result = self.client.post('/', data=self.data, content_type='application/x-www-form-urlencoded').json
        self.assertEqual(result, self.data)

    def test_get_dict_fallback_form_data(self):
        '''Test request.get_dict() function using form-data content type'''
        result = self.client.post('/', data=self.data, content_type='multipart/form-data').json
        self.assertEqual(result, self.data)

    def test_get_dict_cached(self):
        '''Test request.get_dict() caching'''
        @self.app.route('/cached', methods=['POST'])
        def cached():
            override = {'override': 'data'}

            # not cached yet
            self.assertFalse(hasattr(request, '_cached_dict'))

            # calling get_dict caches result
            result1 = request.get_dict()
            self.assertTrue(hasattr(request, '_cached_dict'))
            self.assertNotEqual(result1, override)
            self.assertNotEqual(request._cached_dict, override)

            # override cache
            request._cached_dict = override
            result2 = request.get_dict()

            # results are pulled from cache
            self.assertEqual(result2, override)

            return result2


        self.client.post('/cached', self.data_json)

