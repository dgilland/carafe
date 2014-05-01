
from werkzeug.exceptions import BadRequest

from carafe.utils import jsonify
from .base import TestBase

class TestJsonify(TestBase):
    '''Test jsonify function'''

    def test_jsonify_as_function(self):
        '''
        Test that json.jsonify can be used as a regular function
        to return a JSON response like flask.jsonify
        '''
        data = {'foo': 'bar'}

        @self.app.route('/args')
        def route_args():
            return jsonify(data)

        @self.app.route('/kargs')
        def route_kargs():
            return jsonify(**data)

        self.assertEqual(self.client.get('/args').json, data)
        self.assertEqual(self.client.get('/kargs').json, data)

    def test_jsonify_as_decorator(self):
        '''
        Test that json.jsonify can be used as a decorator
        to return a JSON response like flask.jsonify
        '''
        data = {'foo': 'bar'}

        @self.app.route('/')
        @jsonify
        def route():
            return data

        self.assertEqual(self.client.get('/').json, data)
