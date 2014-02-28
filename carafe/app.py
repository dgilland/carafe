
from flask import Flask, request
from flask._compat import text_type, string_types

from .request import Request
from .response import Response

class FlaskCarafe(Flask):
    request_class = Request
    response_class = Response

    def make_response(self, rv):
        status_or_headers = headers = None
        if isinstance(rv, tuple):
            rv, status_or_headers, headers = rv + (None,) * (3 - len(rv))

        if rv is None:
            raise ValueError('View function did not return a response')

        if isinstance(status_or_headers, (dict, list)):
            headers, status_or_headers = status_or_headers, None

        if not isinstance(rv, self.response_class):
            # add support for converting list or dict to json response
            if isinstance(rv, (text_type, bytes, bytearray, list, dict)):
                rv = self.response_class(rv, headers=headers, status=status_or_headers)
                headers = status_or_headers = None
            else:
                rv = self.response_class.force_type(rv, request.environ)

        if status_or_headers is not None:
            if isinstance(status_or_headers, string_types):
                rv.status = status_or_headers
            else:
                rv.status_code = status_or_headers

        if headers:
            rv.headers.extend(headers)

        return rv
