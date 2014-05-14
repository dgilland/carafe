"""Session interface for Flask.
"""

from flask.sessions import SecureCookieSessionInterface


class SessionInterface(SecureCookieSessionInterface):
    """Extends secure cookie session interface with better support for
    permanent sessions."""
    def __init__(self, salt=None, permanent=True):
        if salt:
            # Salt is added on top of secret key.
            self.salt = salt

        self.permanent = permanent

    def open_session(self, app, request):
        session = super(SessionInterface, self).open_session(app, request)

        if session is not None and self.permanent:
            session.permanent = True

        return session


def init_app(app):
    """Initialize app."""
    app.config.setdefault('CARAFE_SESSION_ENABLED', True)
    app.config.setdefault('CARAFE_SESSION_PERMANENT', True)
    app.config.setdefault('CARAFE_SESSION_SALT', None)

    if not app.config['CARAFE_SESSION_ENABLED']:
        return

    permanent = (app.config['PERMANENT_SESSION_LIFETIME'].total_seconds() > 0
                 and app.config['CARAFE_SESSION_PERMANENT'])

    app.session_interface = SessionInterface(
        salt=app.config['CARAFE_SESSION_SALT'], permanent=permanent)
