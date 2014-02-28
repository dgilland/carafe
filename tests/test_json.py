
import json as _json

from werkzeug.exceptions import BadRequest

from carafe.ext import json
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
            return json.jsonify(data)

        @self.app.route('/kargs')
        def route_kargs():
            return json.jsonify(**data)

        self.assertEqual(self.client.get('/args').json, data)
        self.assertEqual(self.client.get('/kargs').json, data)

    def test_jsonify_as_decorator(self):
        '''
        Test that json.jsonify can be used as a decorator
        to return a JSON response like flask.jsonify
        '''
        data = {'foo': 'bar'}

        @self.app.route('/')
        @json.jsonify
        def route():
            return data

        self.assertEqual(self.client.get('/').json, data)

class TestJSONEncoder(TestBase):
    '''Test JSONEncoder class'''

    def dumps(self, obj):
        '''dumps obj as json using JSONEncoder class'''
        return _json.dumps(obj, cls=json.JSONEncoder)

    def test_encoding_unsupported(self):
        test = object()
        self.assertRaises(TypeError, self.dumps, test)

    def test_encoding_isoformat(self):
        '''Test that obj with method `isoformat` has said method called during json encoding'''
        test_return = 'arrr matey!'

        class ISO(object):
            def isoformat(self):
                return test_return

        test = {'iso': ISO()}
        expected = _json.dumps({'iso': test_return})

        self.assertEqual(self.dumps(test), expected)

    def test_encoding_isoformat_datetime(self):
        '''Test that datetime objects are converted to isoformat'''
        from datetime import datetime

        iso = '{year:02d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}'

        kargs = dict(year=2014, month=1, day=22, hour=9, minute=30, second=45)

        dt = datetime(**kargs)
        test = {'dt': dt}
        expected = _json.dumps({'dt': iso.format(**kargs)})

        self.assertEqual(self.dumps(test), expected)

class TestJSON(TestBase):
    '''Test JSON extension'''

    def test_default_encoder(self):
        '''Test extension's default json encoder is used'''
        self.assertIs(self.app.json_encoder, json.JSONEncoder)

    def test_default_error_handler(self):
        '''Test extension's default error handler is used'''

        self.assertTrue(len(self.app.error_handler_spec[None].values()))

        for error_handler in self.app.error_handler_spec[None].values():
            self.assertIs(error_handler, json.json_error_handler)

    def test_error_handler(self):
        '''Test error handler is invoked'''
        @self.app.route('/')
        def index():
            raise BadRequest('bollocks!')

        res = self.client.get('/')

        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json['error']['description'], 'bollocks!')

class TestCARAFEJSONDisabled(TestBase):
    class __config__(object):
        CARAFE_JSON_ENABLED = False

    def test_disabled_encoder(self):
        self.assertIsNot(self.app.json_encoder, json.JSONEncoder)

    def test_disabled_error_handler(self):
        self.assertFalse(len(self.app.error_handler_spec[None].values()))

