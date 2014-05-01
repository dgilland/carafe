
import os
import logging
from logging.handlers import RotatingFileHandler

import carafe
from carafe.ext.logger import Logger
from .core import logger, Logger

from .base import TestBase

# monkey-patch smtplib so we don't send actual emails
inbox = {}

class Message(object):
    def __init__(self, from_address, to_address, fullmessage):
        self.from_address = from_address
        self.to_address = to_address
        self.fullmessage = fullmessage

class MockSMTP(object):
    def __init__(self, host, port, timeout):
        self.host = host
        self.port = port
        self.timeout = timeout

    def login(self,username,password):
        self.username = username
        self.password = password

    def sendmail(self, from_address, to_address, fullmessage):
        inbox.setdefault(self.username, [])
        inbox[self.username].append(Message(from_address, to_address, fullmessage))
        return []

    def quit(self):
        self.has_quit = True

import smtplib
smtplib.SMTP = MockSMTP

class TestLoggerBase(TestBase):
    @property
    def log_file(self):
        return getattr(self.__config__, 'CARAFE_LOGGER_RFILE_FILENAME', None)

    def get_log_lines(self):
        with open(self.log_file, 'r') as f:
            lines = f.readlines()

        return lines

    def inbox(self, username=None):
        if username:
            return inbox.get(username)
        else:
            return inbox.get(self.__config__.CARAFE_LOGGER_SMTP_USERNAME)

    def tearDown(self):
        if self.log_file:
            # delete log file
            os.system('rm {0}'.format(self.log_file))

        # reset inbox
        inbox.clear()

class TestRotatingFileLogger(TestLoggerBase):
    class __config__(object):
        CARAFE_LOGGER_RFILE_ENABLED = True
        CARAFE_LOGGER_RFILE_FILENAME = '_test_logger.log'

    def test_default_level(self):
        '''Test that default logging level is WARNING'''

        info_msg = 'info not logged'
        warn_msg = 'warning logged'

        @self.app.route('/log')
        def log():
            logger.info(info_msg)
            logger.warning(warn_msg)
            return ''

        self.client.get('/log')

        lines = self.get_log_lines()
        self.assertEqual(len(lines), 1)
        self.assertIn(warn_msg, lines[0])

class TestSMTPLogger(TestLoggerBase):
    class __config__(object):
        CARAFE_LOGGER_SMTP_ENABLED = True
        CARAFE_LOGGER_SMTP_SERVER = 'example.com'
        CARAFE_LOGGER_SMTP_PORT = 25
        CARAFE_LOGGER_SMTP_USERNAME = 'username'
        CARAFE_LOGGER_SMTP_PASSWORD = 'password'
        CARAFE_LOGGER_SMTP_FROMADDR = 'username@example.com'
        CARAFE_LOGGER_SMTP_TOADDRS = 'foo@example.com, bar@example.com'
        CARAFE_LOGGER_SMTP_USE_TLS = False

    def test_default_level(self):
        '''Test that default logging level is ERROR'''

        warn_msg = 'warning not logged'
        err_msg = 'error logged'
        @self.app.route('/log')
        def log():
            logger.warning(warn_msg)
            logger.error(err_msg)
            return ''

        self.client.get('/log')

        messages = self.inbox()
        self.assertEqual(len(messages), 1)

        msg = messages[0]
        self.assertEqual(msg.from_address, self.__config__.CARAFE_LOGGER_SMTP_FROMADDR)
        self.assertEqual(msg.to_address, str(self.__config__.CARAFE_LOGGER_SMTP_TOADDRS).replace(' ', '').split(','))
        self.assertIn(err_msg, msg.fullmessage)
        self.assertNotIn(warn_msg, msg.fullmessage)

class TestAdditionalLoggers(TestLoggerBase):
    class __config__(object):
        CARAFE_LOGGER_RFILE_ENABLED = True
        CARAFE_LOGGER_RFILE_FILENAME = '_test_logger.log'

        CARAFE_LOGGER_SMTP_ENABLED = True
        CARAFE_LOGGER_SMTP_SERVER = 'example.com'
        CARAFE_LOGGER_SMTP_PORT = 25
        CARAFE_LOGGER_SMTP_USERNAME = 'username'
        CARAFE_LOGGER_SMTP_PASSWORD = 'password'
        CARAFE_LOGGER_SMTP_FROMADDR = 'username@example.com'
        CARAFE_LOGGER_SMTP_TOADDRS = 'foo@example.com, bar@example.com'
        CARAFE_LOGGER_SMTP_USE_TLS = False

    def test_additional_loggers(self):
        warn_msg = 'warning logged'

        class nologgerconfig(self.__config__):
            CARAFE_LOGGER_RFILE_FILENAME = '_test_logger.log'
            CARAFE_LOGGER_RFILE_ENABLED = True

        class loggerconfig(self.__config__):
            CARAFE_LOGGER_RFILE_ADD_LOGGERS = ['mylogger']
            CARAFE_LOGGER_SMTP_ADD_LOGGERS = ['mylogger']

        mylogger = logging.getLogger('mylogger')
        mylogger.setLevel(logging.DEBUG)

        # create an app without additional loggers
        nologgerapp = self.create_app(nologgerconfig)

        @nologgerapp.route('/')
        def index_nologger():
            # this will be ignored by our logger
            mylogger.warning(warn_msg)
            return ''

        with nologgerapp.test_client() as c:
            c.get('/')

        self.assertEqual(len(self.get_log_lines()), 0)
        self.assertIsNone(self.inbox())

        # now create an app with additional logger
        loggerapp = self.create_app(loggerconfig)

        @loggerapp.route('/')
        def index_logger():
            mylogger.debug('not logged')
            mylogger.error(warn_msg)
            return ''

        with loggerapp.test_client() as c:
            c.get('/')

        lines = self.get_log_lines()
        self.assertEqual(len(lines), 1)
        self.assertIn(warn_msg, lines[0])

        self.assertEqual(len(self.inbox()), 1)

