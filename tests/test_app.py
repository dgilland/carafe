
from flask import Response
from carafe.app import FlaskCarafe

from .base import TestBase


class TestApp(TestBase):

    content = 'content'

    def test_return_content(self):
        @self.app.route('/')
        def index():
            return self.content

        res = self.client.get('/')

        self.assertStatus(res, 200)
        self.assertEqual(res.data, self.content)

    def test_return_content_status(self):
        @self.app.route('/')
        def index():
            return (self.app.response_class(self.content), 201)

        res = self.client.get('/')

        self.assertStatus(res, 201)
        self.assertEqual(res.data, self.content)

    def test_return_content_status_headers(self):
        @self.app.route('/')
        def index():
            return (self.app.response_class(self.content), 201, {'X-TEST': 'test'})

        res = self.client.get('/')

        self.assertStatus(res, 201)
        self.assertEqual(res.data, self.content)
        self.assertEqual(res.headers['X-TEST'], 'test')

    def test_return_content_status_string(self):
        @self.app.route('/')
        def index():
            return (self.app.response_class(self.content), 'status', {'X-TEST': 'test'})

        res = self.client.get('/')

        self.assertStatus(res, 0)
        self.assertEqual(res.status, '0 status')
        self.assertEqual(res.data, self.content)
        self.assertEqual(res.headers['X-TEST'], 'test')

    def test_return_dict_as_json(self):
        @self.app.route('/')
        def index():
            return {'data': self.content}

        res = self.client.get('/')

        self.assertStatus(res, 200)
        self.assertEqual(res.json['data'], self.content)

    def test_return_dict_as_json_with_status_headers(self):
        @self.app.route('/')
        def index():
            return ({'data': self.content}, 201, {'X-TEST': 'test'})

        res = self.client.get('/')

        self.assertStatus(res, 201)
        self.assertEqual(res.json['data'], self.content)
        self.assertEqual(res.headers['X-TEST'], 'test')

    def test_return_list_as_json(self):
        @self.app.route('/')
        def index():
            return [self.content]

        res = self.client.get('/')

        self.assertStatus(res, 200)
        self.assertEqual(res.json[0], self.content)

    def test_return_list_as_json_with_status_headers(self):
        @self.app.route('/')
        def index():
            return ([self.content], 201, {'X-TEST': 'test'})

        res = self.client.get('/')

        self.assertStatus(res, 201)
        self.assertEqual(res.json[0], self.content)
        self.assertEqual(res.headers['X-TEST'], 'test')

    def test_return_none_exception(self):
        @self.app.route('/')
        def index():
            pass

        self.assertRaises(ValueError, self.client.get, '/')

    def test_return_force_type(self):
        @self.app.route('/')
        def index():
            return Response(self.content)

        res = self.client.get('/')

        self.assertStatus(res, 200)
        self.assertEqual(res.data, self.content)
