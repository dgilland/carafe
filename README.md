# carafe

Collection of Flask extensions geared towards JSON APIs


## Extensions


### session

Sets `app.session_interface = ext.session.SessionInterface()` which uses `SecureCookieSession` as session class.

```python
from carafe.ext import session
session.init_app(app)
```

#### Configuration

```python
# enable/disable extension
CARAFE_SESSION_ENABLED = True
# combined with SECRET_KEY when signing cookies
CARAFE_SESSION_SALT = 'my salt'
# when true and SESSION_PERMANENT_LIFETIME > 0, session is set to permanent
CARAFE_SESSION_PERMANENT = True
# (from flask) lifetime of permanent session int/timedelta
SESSION_PERMANENT_LIFETIME = timedelta(days=15000) # or `1296000000`
# (from flask) must be set to enable secure signing string
SECRET_KEY = 'my secret key'
```


### Cache

Extends `flask-cache` to provide `cache.cached_view()` decorator which supports cache invalidation via key prefix modification cascades.

```python
from carafe.ext.cache import Cache, after_post
from flask.ext.classy import FlaskView

cache = Cache()
cache.init_app(app)

class MyView(FlaskView):
    cache_cascade = ['MyDependentView']

    @cache.cached_view(timeout=3600)
    def index(self):
        # this route gets cached with key = "MyView:view:{path}"
        # and includes any request.args used (i.e. "/route/"
        # and "/route/?foo=bar" have different cache keys)
        return ''

    def post(self):
        return ''

    def after_post(self):
        # after post, then signal is sent which tells "cache" to delete
        # both "MyView" prefixed keys as well as "MyDependentView" prefixed keys
        after_post.send(self)

class MyDependentView(FlaskView):
    def index(self):
        return ''

class MyOtherView(FlaskView):
    cache_namespace = 'my-awesome-namespace'

    @cache.cached_view(include_request_args=False)
    def index(self):
        # this route gets cached with key = "my-awesome-namespace:view:{path}"
        # and doesn't include request.args
        # (i.e. "/route/" and "/route/?foo=bar" have the same cache key)
        return ''
```

#### Configuration

```python
# enable/disable extension
CARAFE_CACHE_ENABLED = True
# ignore these request args when creating cached view key from request path
CARAFE_CACHE_IGNORED_REQUEST_ARGS = []
# cache key prefix
CACHE_KEY_PREFIX = 'my_prefix:'
# default timeout (in seconds) for cache key expiration
CACHE_DEFAULT_TIMEOUT = 300
# cache server host
CACHE_REDIS_HOST = 'localhost'
# cache server port
CACHE_REDIS_PORT = 6379
redis db index (zero-based); defaults to `0`
CACHE_REDIS_DB = 0
```


### Auth

Uses `flask-principal` for managing/generating permission based access.

Requires an Identity Provider class instance which exposes identity information. An example `AuthProvider` is defined in `ext.auth.SQLAlchemyAuthProvider`.

```python
from carafe import FlaskCarafe
from carafe.ext.auth import Auth, SQLAlchemyAuthProvider

# use flask-sqlalchemy for demo purposes
from flask.ext.sqlalchemy import SQLAlchemy
db = SQLAlchemy()

from models import User

MyAuthProvider(SQLAlchemyAuthProvider):
    __model__ = User

    ##
    # Override these methods if they don't return user data
    # correctly based on your models
    ##

    def get_user(self, _id):
        '''Return user object from database.'''
        return self.session.query(self.__model__).get(_id)

    def get_roles(self, user):
        '''Return a list of `roles` as strings.'''
        return getattr(user, self.__roles_key__, [])

provider = MyAuthProvider(db.session)

app = FlaskCarafe(__name__)
auth = Auth(provider=provider)
auth.init_app(app)

@app.route('/login/')
def login():
    if valid:
        auth.login(request.form['user_id'])
    return ''

@app.route('/logout/')
def logout():
    auth.logout()
    reutrn ''

@app.route('/session-user-id/')
def session_user_id():
    return str(auth.user_id)

@app.route('/auth-protected/')
@auth.require.auth(401)
def auth_protected():
    return ''

@app.route('/some-role-protected/')
@auth.require.some_role(403)
def some_role_protected():
    # user has permission if their `user.roles` list contains `'some_role'`
    return ''
```

One can use `auth.require.<permission>` just like `flask.ext.principal.Permission`:

```python
from flask.ext.principal import Permission, RoleNeed
my_role = Permission(RoleNeed('my_role'))

@my_role.require(401)
def foo():
    return ''

##
# is equivalent to
##

@auth.require.my_role(401)
def foo():
    return ''
```

Essentially, `auth.require` is a role-based permission factory which creates permissions on the fly if they haven't been referenced yet.

If one just needs to protect against login, `auth.require` exposes the permission `auth.require.auth()` which is a `TypeNeed` set on successful login.

#### init_app()

```python
auth.init_app(app, provider=MyProvider())
```

#### Configuration

```python
# session key which contains auth user id
CARAFE_AUTH_SESSION_ID_KEY = 'user_id'
# auth provider key which contains auth user id
CARAFE_AUTH_IDENTITY_ID_KEY = 'id'
# auth provider key which contains auth user roles
CARAFE_AUTH_IDENTITY_ROLES_KEY = 'roles'
```


### Logger

Attaches additional loggers to `app.logger`. Provides proxy to `app.logger` via `carafe.logger`.

```python
from carafe.ext.logger import Logger
logger = Logger()
logger.init_app(app)
```

### Configuration

```python
# enable/disable extension as a whole (False disables all types of logging)
CARAFE_LOGGER_ENABLED = False

##
# Rotating file logger
##
# enable/disable rotating file logger
CARAFE_LOGGER_RF_ENABLED = False
# filename
CARAFE_LOGGER_RF_FILENAME
# file write mode
CARAFE_LOGGER_RF_MODE = 'a'
# maximum bytes each log file can have before being rotated
CARAFE_LOGGER_RF_MAXBYTES = 0
# maximum number of backup log files
CARAFE_LOGGER_RF_BACKUPCOUNT = 0
# file encoding to use when opening file
CARAFE_LOGGER_RF_ENCODING = None
# if true delay file opening until first call to emit
CARAFE_LOGGER_RF_DELAY = False
# logging level
CARAFE_LOGGER_RF_LEVEL = 'WARNING'
# additional loggers (referenced by logger name) to attach to
CARAFE_LOGGER_RFILE_ADD_LOGGERS = []

##
# SMTP logger
##
# enable/disable smpt logger
CARAFE_LOGGER_SMTP_ENABLED
# SMTP server
CARAFE_LOGGER_SMTP_SERVER
# SMTP port
CARAFE_LOGGER_SMTP_PORT
# SMTP username
CARAFE_LOGGER_SMTP_USERNAME
# SMTP password
CARAFE_LOGGER_SMTP_PASSWORD
# from email address
CARAFE_LOGGER_SMTP_FROMADDR
# to email address(es)
CARAFE_LOGGER_SMTP_TOADDRS = []
# whether to use TLS
CARAFE_LOGGER_SMTP_USE_TLS = False
# logging level
CARAFE_LOGGER_SMTP_LEVEL = 'ERROR'
# additional loggers (referenced by logger name) to attach to
CARAFE_LOGGER_SMTP_ADD_LOGGERS = []
```
