
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
# uses this should use the HandlerDataMixin class so that extra data
# is attached.
ERROR_FORMAT = '''
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
'''

WARNING_FORMAT = (
    '%(asctime)s: %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')


# default pprint.pformat function to use to output request environ
pformat = partial(pprint.pformat, indent=4, depth=None)


class Logger(object):
    def __init__(self, app=None):
        self.app = app

        if app: # pragma: no cover
            self.init_app(app)

    def init_app(self, app):
        app.config.setdefault('CARAFE_LOGGER_ENABLED', True)

        if app.debug or not app.config['CARAFE_LOGGER_ENABLED']: # pragma: no cover
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
        if not isinstance(loggers, list): # pragma: no cover
            loggers = [loggers]

        if not isinstance(handlers, list): # pragma: no cover
            handlers = [handlers]

        for logger in loggers:
            if isinstance(logger, basestring):
                logger = getLogger(logger)

            for handler in handlers:
                logger.addHandler(handler)

    def __getattr__(self, attr):
        # proxy attribute calls to current_app.logger as shortcut
        return getattr(current_app.logger, attr)


class HandlerDataMixin(object):
    '''Mixin class that exposes request data to log format.'''

    def get_request_environ(self):
        '''Return copy of request data for debugging purposes.'''
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


    def emit(self, record):
        '''Override parent method and attach request environ data to
        log record
        '''
        record.environ = pformat(self.get_request_environ())
        super(HandlerDataMixin, self).emit(record)


class SMTPHandler(HandlerDataMixin, SMTPHandlerBase):
    '''Override `emit()` function so that request data is available to log
    formatter
    '''

    def getSubject(self, record):
        '''Override with custom subject'''
        return '[{0}] Application Error: {1}'.format(
            current_app.name, request.url)


class RotatingFileHandler(HandlerDataMixin, RotatingFileHandlerBase):
    '''Override `emit()` function so that request data is available to log
    formatter
    '''
    pass


def create_rotating_file_handler(options):
    kargs = {
        'filename': options['CARAFE_LOGGER_RFILE_FILENAME'],
        'mode': options.get('CARAFE_LOGGER_RFILE_MODE', 'a'),
        'maxBytes': options.get('CARAFE_LOGGER_RFILE_MAXBYTES', 0),
        'backupCount': options.get('CARAFE_LOGGER_RFILE_BACKUPCOUNT', 0),
        'encoding': options.get('CARAFE_LOGGER_RFILE_ENCODING'),
        'delay': options.get('CARAFE_LOGGER_RFILE_DELAY', 0)
    }

    handler = RotatingFileHandler(**kargs)
    handler.setLevel(
        getattr(logging, options.get('CARAFE_LOGGER_RFILE_LEVEL', 'WARNING')))

    handler.setFormatter(Formatter(WARNING_FORMAT))

    return handler


def create_email_handler(options):
    if isinstance(options['CARAFE_LOGGER_SMTP_TOADDRS'], basestring):
        # convert to list
        options['CARAFE_LOGGER_SMTP_TOADDRS'] = [
            x.strip()
            for x in options['CARAFE_LOGGER_SMTP_TOADDRS'].split(',')
        ]

    kargs = {
        'mailhost': (
            options['CARAFE_LOGGER_SMTP_SERVER'],
            options['CARAFE_LOGGER_SMTP_PORT']
        ),
        'fromaddr': options['CARAFE_LOGGER_SMTP_FROMADDR'],
        'toaddrs': options['CARAFE_LOGGER_SMTP_TOADDRS'],
        'subject': 'Application Error',
        'credentials': (
            options['CARAFE_LOGGER_SMTP_USERNAME'],
            options['CARAFE_LOGGER_SMTP_PASSWORD']
        ),
        'secure': () if options.get('CARAFE_LOGGER_SMTP_USE_TLS') else None
    }

    handler = SMTPHandler(**kargs)
    handler.setLevel(
        getattr(logging, options.get('CARAFE_LOGGER_SMTP_LEVEL', 'ERROR')))

    handler.setFormatter(Formatter(ERROR_FORMAT))

    return handler
