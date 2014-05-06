
from flask.testing import FlaskClient
from flask import json
from werkzeug import urls
from werkzeug.utils import cached_property


class JsonResponseMixin(object):
    '''Mixin which adds method to jsonify response data'''
    @cached_property
    def json(self):
        return json.loads(self.data)


def make_client_response(response_class):
    class ClientResponse(response_class, JsonResponseMixin):
        pass

    return ClientResponse


class Client(FlaskClient):
    def get(self, url, params=None, **kargs):
        if params:
            url = urls.Href(url)(params)

        return super(Client, self).get(url, **kargs)

    def post(self, url, data, **kargs):
        kargs['data'] = data
        return super(Client, self).post(url, **kargs)

    def put(self, url, data, **kargs):
        kargs['data'] = data
        return super(Client, self).put(url, **kargs)

    def patch(self, url, data, **kargs):
        kargs['data'] = data
        return super(Client, self).patch(url, **kargs)


class JSONClient(Client):
    def open(self, *args, **kargs):
        # all requests will be treated like JSON unless otherwise specified
        kargs.setdefault('content_type', 'application/json')

        if (kargs['content_type'] == 'application/json'
                and isinstance(kargs.get('data'), dict):
            # If data is a dict, then assume we want to send a JSON serialized
            # string in the request.
            try:
                kargs['data'] = json.dumps(kargs['data'])
            except Exception:
                # Ignore error if data isn't serializable and just send it.
                pass

        return super(JSONClient, self).open(*args, **kargs)
