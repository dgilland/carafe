
from collections import namedtuple

from flask import session, request

import carafe
from carafe.ext.auth import SQLAlchemyAuthProvider

from . import factory
from .core import auth
from .base import TestBase


##
# mock session object expected by auth.SQLAlchemyAuthProvider
##
class Session(object):
    class Storage(object):
        User = namedtuple('User', ['name', 'roles'])
        users = {
            1: User('User One', roles=[]),
            2: User('User Two', roles=['admin', 'manager']),
            3: User('User Three', roles=['manager']),
        }

        @staticmethod
        def get(_id):
            return Session.Storage.users.get(_id)

    def query(self, *args, **kargs):
        return self.Storage


class TestAuthBase(TestBase):
    class __config__(object):
        SECRET_KEY = 'secret key'

    __client_class__ = carafe.JSONClient

    regular_user_id = 1
    admin_user_id = 2
    manager_user_id = 3

    def create_app(self):
        options = {
            'auth': {'provider': SQLAlchemyAuthProvider(Session())}
        }

        app = factory.create_app(__name__, config=self.__config__, options=options)
        self.init_app(app)

        return app

    def setUp(self):
        # create session routes
        @self.app.route('/session', methods=['POST'])
        def session_post():
            auth.login(request.get_dict()['user_id'])
            return ''

        @self.app.route('/session', methods=['DELETE'])
        def session_delete():
            auth.logout()
            return ''

        @self.app.route('/session', methods=['GET'])
        def session_get():
            return dict(session)

        @self.app.route('/auth')
        @auth.require.login(401)
        def auth_handler():
            return ''

    def login(self, user_id):
        return self.client.post('/session', {'user_id': user_id})

    def logout(self):
        return self.client.delete('/session')


class TestAuth(TestAuthBase):
    """Test auth extension"""

    def test_auth_permission(self):
        """Test basic auth permission"""
        # test without logging in
        self.assertStatus(self.client.get('/auth'), 401)

        # login
        self.login(self.regular_user_id)
        self.assertEqual(self.client.get('/session').json['user_id'], self.regular_user_id)

        # test that identity is now recognized
        self.assertStatus(self.client.get('/auth'), 200)

        # logout
        self.logout()

        # auth is restricted again
        self.assertStatus(self.client.get('/auth'), 401)

    def test_general_permission(self):
        """Test general permissions"""
        @self.app.route('/admin')
        @auth.require.admin(403)
        def admin():
            return ''

        @self.app.route('/manager')
        @auth.require.manager(403)
        def manager():
            return ''

        @self.app.route('/general')
        @auth.require.foobar(401)
        def general():
            return ''

        # login with user who does have necessary permissions
        self.client.post('/session', {'user_id': self.regular_user_id})
        self.assertEqual(self.client.get('/session').json['user_id'], self.regular_user_id)
        self.assertStatus(self.client.get('/admin'), 403)
        self.assertStatus(self.client.get('/manager'), 403)
        self.assertStatus(self.client.get('/general'), 401)

        # login with user who does have necessary permissions (except one)
        self.client.post('/session', {'user_id': self.admin_user_id})
        self.assertEqual(self.client.get('/session').json['user_id'], self.admin_user_id)
        self.assertStatus(self.client.get('/admin'), 200)
        self.assertStatus(self.client.get('/manager'), 200)
        self.assertStatus(self.client.get('/general'), 401)

    def test_user_invalidated_offline(self):
        """Test that user is logged out if their account is removed offline"""
        orig_user = Session.Storage.users[self.regular_user_id]

        self.login(self.regular_user_id)

        self.assertStatus(self.client.get('/auth'), 200)

        del Session.Storage.users[self.regular_user_id]

        self.assertStatus(self.client.get('/auth'), 401)

        Session.Storage.users[self.regular_user_id] = orig_user


class TestAuthProviderMissing(TestAuthBase):

    def create_app(self):
        # don't provide options which is where provider is passed in
        options = {}
        app = factory.create_app(__name__, config=self.__config__, options=options)
        self.init_app(app)

        return app

    def test_missing_provider(self):
        """Test that not setting a provider causes identity to not load"""
        self.client.post('/session', {'user_id': self.regular_user_id})
        self.assertEqual(self.client.get('/session').json['user_id'], self.regular_user_id)
        self.assertStatus(self.client.get('/auth'), 401)
