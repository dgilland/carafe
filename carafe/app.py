"""Carafe's custom Flask app.
"""

from flask import Flask

from .request import Request
from .response import Response


class FlaskCarafe(Flask):
    """Extension of standard Flask app with custom request and response
    classes.
    """
    request_class = Request
    response_class = Response
