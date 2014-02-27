
from .base import TestBase

from flask import session
from flask.sessions import SecureCookieSession

import carafe
from carafe.ext.session import SessionInterface

class TestSession(TestBase):
	class __config__(object):
		CARAFE_SESSION_PERMANENT = True
		CARAFE_SESSION_SALT = 'carafe-salt'
		SECRET_KEY = 'carafe-secret'

	def test_session(self):
		@self.app.route('/foo')
		@carafe.ext.json.jsonify
		def foo():
			session['foo'] = True
			return session

		@self.app.route('/bar')
		@carafe.ext.json.jsonify
		def bar():
			session['bar'] = True
			return session

		self.assertEqual(self.client.get('/foo').json, {'foo': True, '_permanent': True})
		self.assertEqual(self.client.get('/bar').json, {'bar': True, 'foo': True, '_permanent': True})
		self.assertEqual(self.client.get('/foo').json, {'bar': True, 'foo': True, '_permanent': True})

	def test_session_interface_enabled(self):
		self.assertIsInstance(self.app.session_interface, SessionInterface)

class TestSessionDisabled(TestBase):
	class __config__(object):
		CARAFE_SESSION_ENABLED = False

	def test_session_interface_disabled(self):
		self.assertNotIsInstance(self.app.session_interface, SessionInterface)
