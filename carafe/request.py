"""Extension of flask.Request.
"""

from flask import Request as RequestBase


class Request(RequestBase):
    """Subclass of flask.Request with some added features"""

    @property
    def data(self):
        """Property access to get_dict()."""
        return self.get_dict()

    def get_dict(self, force=True, silent=True, cache=True):
        """Attempt to return request data as a dict. This is similar to
        `get_json` but is more permissive in trying to return something useful.
        Try to convert from JSON first but then fallback to other extraction
        methods.
        """
        data = getattr(self, '_cached_dict', None)
        if data is not None:
            return data

        data = self.get_json(force=force, silent=silent, cache=cache)

        if data is None:
            # fallback to form data
            data = self.form

        if hasattr(data, 'to_dict'):
            data = data.to_dict()

        data = data or {}

        if cache:
            self._cached_dict = data

        return data
