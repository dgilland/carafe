
import flask
from flask import session, current_app
from flask.ext.principal import (
    Principal,
    identity_loaded,
    identity_changed,
    Identity,
    AnonymousIdentity,
    Permission,
    UserNeed,
    RoleNeed,
    TypeNeed
)

login_need = TypeNeed('login')


class SQLAlchemyAuthProvider(object):
    '''
    SQLAlchemy backed UserProvider class which provides identity information for logged in user.
    '''

    # SQLAlchemy model used to query the database for identity information
    __model__ = None

    __id_key__ = 'id'
    __roles_key__ = 'roles'

    def __init__(self, session):
        self.session = session

    def identify(self, identity):
        '''
        Identify a user via _id to provide information for role based authentication.
        '''
        ident = {}

        user = self.get_user(identity.id)
        if user:
            ident.update({
                self.__id_key__: identity.id,
                self.__roles_key__: self.get_roles(user)
            })

        return ident

    ##
    # Override these methods if they don't return user data correctly based on your models
    ##

    def get_user(self, _id):
        '''Return user object from database.'''
        if _id is None:
            return None
        return self.session.query(self.__model__).get(_id)

    def get_roles(self, user):
        '''Return a list of `roles` as strings.'''
        return getattr(user, self.__roles_key__, [])


class Auth(object):
    _extension_name = 'carafe.auth'

    def __init__(self, app=None, provider=None):
        self.principal = Principal(use_sessions=False)
        self.require = PermissionFactory()

        self.app = app
        if self.app:  # pragma: no cover
            self.init_app(app, provider)

    def init_app(self, app, provider=None):
        app.config.setdefault('CARAFE_AUTH_SESSION_ID_KEY', 'user_id')
        app.config.setdefault('CARAFE_AUTH_IDENTITY_ID_KEY', 'id')
        app.config.setdefault('CARAFE_AUTH_IDENTITY_ROLES_KEY', 'roles')

        if not hasattr(app, 'extensions'): # pragma: no cover
            app.extensions = {}

        app.extensions[self._extension_name] = {'provider': provider}

        # @note: instead of having principal use it's session loader, we'll use ours
        self.principal.init_app(app)
        self.principal.identity_loader(self.session_identity_loader)
        identity_loaded.connect_via(app)(self.on_identity_loaded)

    @property
    def session_id_key(self):
        return current_app.config['CARAFE_AUTH_SESSION_ID_KEY']

    @property
    def identity_id_key(self):
        return current_app.config['CARAFE_AUTH_IDENTITY_ID_KEY']

    @property
    def identity_roles_key(self):
        return current_app.config['CARAFE_AUTH_IDENTITY_ROLES_KEY']

    @property
    def user_id(self):
        return session.get(self.session_id_key)

    @property
    def provider(self):
        return current_app.extensions[self._extension_name]['provider']

    def session_identity_loader(self):
        '''Fetch user id from session using config's auth id key'''
        if self.session_id_key in session:
            identity = Identity(session[self.session_id_key])
        else:
            identity = None

        return identity

    def on_identity_loaded(self, app, identity):
        '''Called if session_identity_loader() returns an identity (i.e. not None)'''
        # whatever is returned is used for our identity
        # potentially, provider may return a different user than original identity
        # (e.g. app provides way for admin users to access site using a different user account)
        if self.provider:
            ident = self.provider.identify(identity)
        else:
            ident = {self.identity_id_key: None}

        if self.user_id and not ident:
            # session has an user_id but the ident return is empty
            # user possibly deleted or inactivated in another process
            self.logout()

        # provide auth (whether user is not anonymous)
        if ident.get(self.identity_id_key):
            identity.provides.add(login_need)

        # provide roles
        for role in ident.get(self.identity_roles_key, []):
            identity.provides.add(RoleNeed(role))

    def send_identity_changed(self, user_id):
        identity = AnonymousIdentity() if user_id is None else Identity(user_id)
        identity_changed.send(current_app._get_current_object(), identity=identity)

    def login(self, user_id, propagate=True):
        if session.get(self.session_id_key) != user_id:
            session[self.session_id_key] = user_id
            if propagate:
                self.send_identity_changed(user_id)

    def logout(self, propagate=True):
        if session.get(self.session_id_key):
            del session[self.session_id_key]
            if propagate:
                self.send_identity_changed(None)


class PermissionFactory(object):
    def __init__(self):
        self._permissions = {
            'login': Permission(login_need)
        }

    def __getattr__(self, attr):
        if attr not in self._permissions:
            self._permissions[attr] = Permission(RoleNeed(attr))

        return self._permissions[attr].require

