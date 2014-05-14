"""Extension of flask.Response.
"""

from flask import Response as ResponseBase, json, current_app, request


class Response(ResponseBase):
    """Extend flask.Response with support for list/dict conversion to JSON."""
    def __init__(self, content=None, *args, **kargs):
        if isinstance(content, (list, dict)):
            kargs['mimetype'] = 'application/json'
            content = to_json(content)

        super(Response, self).__init__(content, *args, **kargs)

    @classmethod
    def force_type(cls, response, environ=None):
        """Override with support for list/dict."""
        if isinstance(response, (list, dict)):
            return cls(response)
        else:
            return super(Response, cls).force_type(response, environ)


def to_json(content):
    """Converts content to json while respecting config options."""
    indent = None
    if (current_app.config['JSONIFY_PRETTYPRINT_REGULAR']
            and not request.is_xhr):
        indent = 2
    return json.dumps(content, indent=indent)
