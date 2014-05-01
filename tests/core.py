
from carafe import FlaskCarafe

from carafe.ext.logger import Logger
from carafe.ext.cache import Cache
from carafe.ext.signaler import Signaler
from carafe.ext.auth import Auth

# extensions for use
# each object below should expose an "init_app" function/method
from carafe.ext import session


signaler = Signaler()
logger = Logger()
cache = Cache(signaler=signaler)
auth = Auth()