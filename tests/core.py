
from carafe import FlaskCarafe

from carafe.ext.logger import Logger
from carafe.ext.cache import Cache
from carafe.ext.auth import Auth

# extensions for use
# each object below should expose an "init_app" function/method
from carafe.ext import session


logger = Logger()
cache = Cache()
auth = Auth()
