
from flask.sessions import SecureCookieSessionInterface

class SessionInterface(SecureCookieSessionInterface):
    def __init__(self, salt=None, permanent=True):
        if salt:
            # salt is added on top of secret key
            self.salt = salt

        self.permanent = permanent

    def open_session(self, app, request):
        session = super(SessionInterface, self).open_session(app, request)

        if session is not None and self.permanent:
            # set session to permanent
            session.permanent = True

        return session

def init_app(app):
	app.config.setdefault('CARAFE_SESSION_PERMANENT', True)
	app.config.setdefault('CARAFE_SESSION_SALT', None)

	permanent = app.config['CARAFE_SESSION_PERMANENT'] and app.config['PERMANENT_SESSION_LIFETIME'].total_seconds() > 0

	app.session_interface = SessionInterface(salt=app.config['CARAFE_SESSION_SALT'], permanent=permanent)
