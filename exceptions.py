import googleapiclient
import logging
import functools
import requests

from json.decoder import JSONDecodeError
from requests import ConnectionError
from selenium.common.exceptions import TimeoutException
from redis.exceptions import ConnectionError as RedisConnectionError
from urllib3.exceptions import MaxRetryError

logger = logging.getLogger('CMstoreHH')

SLUG_TO_EXCEPTIONS_TITLE = {
    'unsupported_query_error': 'unsupported params, check query',
    'unsupported_command_error': 'unsupported command for the query',
    'connection_error': 'internet connection error or url forbidden',
    'json_decode_error': 'can not decode json',
    'hh_token_error': 'hh access token needs to be updated',
    'auth_page_timeout': 'authorization page timed out',
    'invalid_auth_page': 'invalid authorization page',
    'selenium_connection_error': 'connection error to selenium server',
    'no_employee_data': 'no employee data',
    'error_google_spreadsheet_auth': [],
    'redis_connection_error': 'redis connection error',
}


def get_slug_of_failure(exe):

    if isinstance(exe, (
        ConnectionError,
        requests.exceptions.HTTPError,
        googleapiclient.errors.HttpError
    )):
        return 'connection_error'
    elif isinstance(exe, HhTokenError):
        return 'hh_token_error'
    elif isinstance(exe, TimeoutException):
        return 'auth_page_timeout'
    elif isinstance(exe, HhInvalidAuthPage):
        return 'invalid_auth_page'
    elif isinstance(exe, MaxRetryError):
        return 'selenium_connection_error'
    elif isinstance(exe, NoEmployeeData):
        return 'no_employee_data'
    elif isinstance(exe, ErrorGoogleSpreadsheetAuth):
        return 'error_google_spreadsheet_auth' 
    elif isinstance(exe, RedisConnectionError):
        return 'redis_connection_error'         
    elif isinstance(exe, JSONDecodeError):
        return 'json_decode_error'
    elif isinstance(exe, KeyError):
        return 'unsupported_command_error'
    elif isinstance(exe, (ValueError, TypeError, NameError, IndexError)):
        return 'unsupported_query_error'

    if hasattr(exe, 'slug'):
        return exe.slug

    return 'unknown_error'


class HhTokenError(Exception):
    slug = None

    def __str__(self):
        return SLUG_TO_EXCEPTIONS_TITLE.get(self.slug, str(type(self)))


class HhInvalidAuthPage(Exception):
    slug = None

    def __str__(self):
        return SLUG_TO_EXCEPTIONS_TITLE.get(self.slug, str(type(self)))


class NoEmployeeData(Exception):
    slug = None

    def __str__(self):
        return SLUG_TO_EXCEPTIONS_TITLE.get(self.slug, str(type(self)))


class ErrorGoogleSpreadsheetAuth(Exception):
    slug = None

    def __str__(self):
        return SLUG_TO_EXCEPTIONS_TITLE.get(self.slug, str(type(self)))


def handle_errors():
    def wrap(func):
        @functools.wraps(func)
        def run_func(*args):
            try:
                return func(*args)
            except Exception as exe:
                title_of_error = SLUG_TO_EXCEPTIONS_TITLE.get(
                    get_slug_of_failure(exe), ''
                )
                logger.exception(title_of_error)
                return title_of_error

        return run_func
    return wrap