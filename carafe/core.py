
from .app import FlaskCarafe

from .ext.json import jsonify, JSONEncoder
from .ext.logger import Logger
from .ext.cache import Cache
from .ext.signaler import signaler
from .ext.auth import Auth

# extensions for use
# each object below should expose an "init_app" function/method
from .ext import json
from .ext import session
logger = Logger()
cache = Cache(signaler=signaler)
auth = Auth()