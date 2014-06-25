
from flask import Flask
from flask.ext.testing import TestCase

import carafe

from . import factory


class TestBase(TestCase):
    __config__ = None
    __client_class__ = carafe.Client

    def create_app(self, config=None):
        config = self.__config__ if config is None else config
        app = factory.create_app(__name__, config=config)
        self.init_app(app)
        return app

    def init_app(self, app):
        # enable testing
        app.config['TESTING'] = True

        # override default test_client_class with our own
        app.response_class = carafe.client.make_client_response(app.response_class)
        app.test_client_class = self.__client_class__

    ##
    # polyfills for python2.6 supports
    ##
    def assertIsNone(self, a, msg=None):
        try:
            assert a is None
        except AssertionError:
            if msg:
                raise AssertionError(msg)
            else:
                raise

    def assertIsNotNone(self, a, msg=None):
        try:
            assert a is not None
        except AssertionError:
            if msg:
                raise AssertionError(msg)
            else:
                raise

    def assertIs(self, a, b, msg=None):
        try:
            assert a is b
        except AssertionError:
            if msg:
                raise AssertionError(msg)
            else:
                raise

    def assertIsInstance(self, a, b, msg=None):
        try:
            assert isinstance(a, b)
        except AssertionError:
            if msg:
                raise AssertionError(msg)
            else:
                raise

    def assertNotIsInstance(self, a, b, msg=None):
        try:
            assert not isinstance(a, b)
        except AssertionError:
            if msg:
                raise AssertionError(msg)
            else:
                raise

    def assertIn(self, a, b, msg=None):
        try:
            assert a in b
        except AssertionError:
            if msg:
                raise AssertionError(msg)
            else:
                raise

    def assertNotIn(self, a, b, msg=None):
        try:
            assert a not in b
        except AssertionError:
            if msg:
                raise AssertionError(msg)
            else:
                raise
