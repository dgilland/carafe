
from flask import Flask

from .request import Request
from .response import Response


class FlaskCarafe(Flask):
    request_class = Request
    response_class = Response
