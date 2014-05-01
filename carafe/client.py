
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

        # convert kargs['data'] dict to json, otherwise, werkzeug will cast to ImmutableDict
        # ImmutableDicts are a problem since our API performs updates to incoming data
        # in normal operation, all dict data is sent as JSON strings which our API then converts to a dict which can be updated
        if isinstance(kargs.get('data'), dict):
            try:
                kargs['data'] = json.dumps(kargs['data'])
            except Exception:
                # some data may not be serializable (e.g. StringIO for file uploads)
                # in that case, it's probably ok to not serialize since that data dict won't be updated in the API
                pass

        return super(JSONClient, self).open(*args, **kargs)
