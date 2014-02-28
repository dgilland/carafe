
from flask import Response as ResponseBase, json, current_app, request

class Response(ResponseBase):
    def __init__(self, content=None, *args, **kargs):
        if isinstance(content, (list, dict)):
            kargs['mimetype'] = 'application/json'
            content = to_json(content)

        super(Response, self).__init__(content, *args, **kargs)

def to_json(content):
    indent = None
    if current_app.config['JSONIFY_PRETTYPRINT_REGULAR'] and not request.is_xhr:
        indent = 2
    return json.dumps(content, indent=indent)

