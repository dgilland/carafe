
from flask import Request as RequestBase
from werkzeug import cached_property

_missing = object()

class Request(RequestBase):
    '''Subclass of flask.Request with some added features'''

    def get_dict(self, force=True, silent=True, cache=True):
        '''
        Attempt to return request data as a dict.

        This is similar to `get_json` but is more permissive in trying to return something useful.

        Try to convert from JSON first but then fallback to other extraction methods.
        '''
        data = getattr(self, '_cached_dict', _missing)
        if data is not _missing:
            return data

        data = self.get_json(force=force, silent=silent, cache=cache)

        if data is None:
            # fallback to form data
            data = self.form

        if hasattr(data, 'to_dict'):
            data = data.to_dict()

        data = data or {}
        self._cached_dict = data

        return data
