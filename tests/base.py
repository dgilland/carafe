
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
