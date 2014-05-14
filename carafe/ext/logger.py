"""Flask extension which integrates additional loggers with Flask app.
"""

import logging
from logging import getLogger, Formatter
from logging.handlers import (
    SMTPHandler as SMTPHandlerBase,
    RotatingFileHandler as RotatingFileHandlerBase
)
import pprint
from functools import partial

from flask import request, current_app


# Universal error message format for custom logger handlers. Any handler who
# uses this should use the EnvironDataMixin class so that extra data
# is attached.
ERROR_FORMAT = """
===============================================================================
Message type:       %(levelname)s
Location:           %(pathname)s:%(lineno)d
Module:             %(module)s
Function:           %(funcName)s
Time:               %(asctime)s


REQUEST:

%(environ)s


ERROR:

%(message)s
===============================================================================
"""

WARNING_FORMAT = (
    '%(asctime)s: %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')


# default pprint.pformat function to use to output request environ
# pylint: disable=invalid-name
pformat = partial(pprint.pformat, indent=4, depth=None)
# pylint: enable=invalid-name


class Logger(object):
    """Flask Logger extension."""

    def __init__(self, app=None):
        self.app = app

        if app:  # pragma: no cover
            self.init_app(app)

    def init_app(self, app):
        """Initialize app."""
        app.config.setdefault('CARAFE_LOGGER_ENABLED', True)

        if not app.config['CARAFE_LOGGER_ENABLED']:  # pragma: no cover
            return

        if app.config.get('CARAFE_LOGGER_RFILE_ENABLED'):
            loggers = ([app.logger] +
                       app.config.get('CARAFE_LOGGER_RFILE_ADD_LOGGERS', []))

            self.add_handlers(
                loggers, create_rotating_file_handler(app.config))

        if app.config.get('CARAFE_LOGGER_SMTP_ENABLED'):
            loggers = ([app.logger] +
                       app.config.get('CARAFE_LOGGER_SMTP_ADD_LOGGERS', []))

            self.add_handlers(
                loggers, create_email_handler(app.config))

    def add_handlers(self, loggers, handlers):
        """Attach additional logging handlers to loggers."""
        if not isinstance(loggers, list):  # pragma: no cover
            loggers = [loggers]

        if not isinstance(handlers, list):  # pragma: no cover
            handlers = [handlers]

        for logger in loggers:
            if isinstance(logger, basestring):
                logger = getLogger(logger)

            for handler in handlers:
                logger.addHandler(handler)

    def __getattr__(self, attr):
        """Proxy attribute calls to current_app.logger."""
        return getattr(current_app.logger, attr)


class EnvironDataMixin(object):
    """Mixin class that exposes request data to log format."""

    def get_request_environ(self):
        """Return copy of request data for debugging purposes."""
        environ = request.environ.copy()
        environ.update({
            'REQUEST_DATA': request.data,
            'REQUEST_JSON': request.get_json(silent=True),
            'REQUEST_FORM': request.form.to_dict(),
            'REQUEST_FILES': request.files.to_dict(),
            'REQUEST_HEADERS': dict(request.headers),
            'REQUEST_ARGS': request.args.to_dict()
        })

        return environ


class SMTPHandler(SMTPHandlerBase, EnvironDataMixin):
    """Override `emit()` function so that request data is available to log
    formatter.
    """

    def getSubject(self, record):
        """Override with custom subject."""
        return '[{0}] Application Error: {1}'.format(
            current_app.name, request.url)

    def emit(self, record):
        """Override parent method and attach request environ data to
        log record.
        """
        record.environ = pformat(self.get_request_environ())
        super(SMTPHandler, self).emit(record)


class RotatingFileHandler(RotatingFileHandlerBase, EnvironDataMixin):
    """Override `emit()` function so that request data is available to log
    formatter.
    """
    def emit(self, record):
        """Override parent method and attach request environ data to
        log record
        """
        record.environ = pformat(self.get_request_environ())
        super(RotatingFileHandler, self).emit(record)


def create_rotating_file_handler(config):
    """Create a rotating file logger handler."""
    kargs = {
        'filename': config['CARAFE_LOGGER_RFILE_FILENAME'],
        'mode': config.get('CARAFE_LOGGER_RFILE_MODE', 'a'),
        'maxBytes': config.get('CARAFE_LOGGER_RFILE_MAXBYTES', 0),
        'backupCount': config.get('CARAFE_LOGGER_RFILE_BACKUPCOUNT', 0),
        'encoding': config.get('CARAFE_LOGGER_RFILE_ENCODING'),
        'delay': config.get('CARAFE_LOGGER_RFILE_DELAY', 0)
    }

    handler = RotatingFileHandler(**kargs)
    handler.setLevel(
        getattr(logging, config.get('CARAFE_LOGGER_RFILE_LEVEL', 'WARNING')))

    handler.setFormatter(Formatter(WARNING_FORMAT))

    return handler


def create_email_handler(config):
    """Create an email logging handler."""
    if isinstance(config['CARAFE_LOGGER_SMTP_TOADDRS'], basestring):
        # convert to list
        config['CARAFE_LOGGER_SMTP_TOADDRS'] = [
            x.strip()
            for x in config['CARAFE_LOGGER_SMTP_TOADDRS'].split(',')
        ]

    kargs = {
        'mailhost': (
            config['CARAFE_LOGGER_SMTP_SERVER'],
            config['CARAFE_LOGGER_SMTP_PORT']
        ),
        'fromaddr': config['CARAFE_LOGGER_SMTP_FROMADDR'],
        'toaddrs': config['CARAFE_LOGGER_SMTP_TOADDRS'],
        'subject': 'Application Error',
        'credentials': (
            config['CARAFE_LOGGER_SMTP_USERNAME'],
            config['CARAFE_LOGGER_SMTP_PASSWORD']
        ),
        'secure': () if config.get('CARAFE_LOGGER_SMTP_USE_TLS') else None
    }

    handler = SMTPHandler(**kargs)
    handler.setLevel(
        getattr(logging, config.get('CARAFE_LOGGER_SMTP_LEVEL', 'ERROR')))

    handler.setFormatter(Formatter(ERROR_FORMAT))

    return handler
