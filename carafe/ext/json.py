
from functools import wraps

from flask import json, jsonify as _jsonify
from werkzeug.exceptions import HTTPException, default_exceptions

class JSONEncoder(json.JSONEncoder):
    '''Extend flask's JSONEncoder class'''
    def default(self, o):
        if hasattr(o, 'isoformat'):
            return o.isoformat()
        else:
            return super(JSONEncoder, self).default(o)

def json_error_handler(ex):
    '''Convert exception to jsonify response'''
    error = {
        'description': getattr(ex, 'description', ''),
        'message': str(ex),
        'name': getattr(ex, 'name', ''),
        'code': ex.code if isinstance(ex, HTTPException) else 500
    }

    for k, v in error.iteritems():
        # only json-able values should be sent
        try:
            json.dumps(v)
        except Exception:
            error[k] = ''

    response = jsonify(error=error)
    response.status_code = error['code']

    return response

def jsonify(f=None, *args, **kargs):
    '''Function or decorator that returns jsonfiy response'''
    if callable(f):
        @wraps(f)
        def decorated(*args, **kargs):
            return _jsonify(**f(*args, **kargs))
        return decorated
    else:
        if f is not None:
            # consider `f` a positional arg
            args = tuple([f] + list(args))
        return _jsonify(*args, **kargs)

def init_app(app, error_handler=json_error_handler, encoder=JSONEncoder):
    if encoder:
        app.json_encoder = encoder

    if error_handler:
        for code in default_exceptions.iterkeys():
            app.error_handler_spec[None][code] = error_handler