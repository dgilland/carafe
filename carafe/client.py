"""Flask test client extensions.
"""

from flask.testing import FlaskClient
from flask import json
from werkzeug import urls
from werkzeug.utils import cached_property


class JsonResponseMixin(object):
    """Mixin which adds method to jsonify response data"""
    @cached_property
    def json(self):
        """Attempt to convert response data to JSON."""
        return json.loads(self.data)


def make_client_response(response_class):
    """Factory function for mixing JsonResponseMixin with app's response class.
    """
    class ClientResponse(response_class, JsonResponseMixin):
        """Mixed in resposne class."""
        pass

    return ClientResponse


class Client(FlaskClient):
    """Expose standard interface for HTTP verbs.
    """
    def get(self, url, params=None, **kargs):
        """Wrap get request with URL params support."""
        if params:
            url = urls.Href(url)(params)

        return super(Client, self).get(url, **kargs)

    def post(self, url, data, **kargs):
        """Wrap post request with data argument exposed in args."""
        kargs['data'] = data
        return super(Client, self).post(url, **kargs)

    def put(self, url, data, **kargs):
        """Wrap put request with data argument exposed in args."""
        kargs['data'] = data
        return super(Client, self).put(url, **kargs)

    def patch(self, url, data, **kargs):
        """Wrap patch request with data argument exposed in args."""
        kargs['data'] = data
        return super(Client, self).patch(url, **kargs)


class JSONClient(Client):
    """JSON API client with convenience handling of content-type and JSON
    serialization.
    """
    def open(self, *args, **kargs):
        """Wrap open with JSON data handling."""

        # All requests will be treated like JSON unless otherwise specified.
        kargs.setdefault('content_type', 'application/json')

        if (kargs['content_type'] == 'application/json'
                and isinstance(kargs.get('data'), dict)):
            # If data is a dict, then assume we want to send a JSON serialized
            # string in the request.
            try:
                kargs['data'] = json.dumps(kargs['data'])
            except Exception:
                # Ignore error if data isn't serializable and just send it.
                pass

        return super(JSONClient, self).open(*args, **kargs)
