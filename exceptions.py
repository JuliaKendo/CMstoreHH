import googleapiclient
import logging
import functools
import requests
import rollbar

from aiogram.utils import exceptions
from json.decoder import JSONDecodeError
from requests import ConnectionError
from selenium.common.exceptions import TimeoutException
from redis.exceptions import ConnectionError as RedisConnectionError
from urllib3.exceptions import MaxRetryError

from notify_rollbar import init_rollbar

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


async def handle_tg_errors(update, exception):
    """
    Exceptions handler. Catches all exceptions within task factory tasks.
    :param update:
    :param exception:
    :return: stdout logging
    """

    init_rollbar()
    rollbar.report_exc_info(level='error')

    if isinstance(exception, exceptions.CantDemoteChatCreator):
        logger.exception("Can't demote chat creator")
        return True

    if isinstance(exception, exceptions.TerminatedByOtherGetUpdates):
        logger.exception('Terminated by other getUpdates request; Make sure that only one bot instance is running')
        return True

    if isinstance(exception, exceptions.MessageNotModified):
        logger.exception('Message is not modified')
        return True

    if isinstance(exception, exceptions.MessageCantBeDeleted):
        logger.exception('Message cant be deleted')
        return True

    if isinstance(exception, exceptions.MessageToDeleteNotFound):
        logger.exception('Message to delete not found')
        return True

    if isinstance(exception, exceptions.MessageTextIsEmpty):
        logger.exception('MessageTextIsEmpty')
        return True

    if isinstance(exception, exceptions.Unauthorized):
        logger.exception(f'Unauthorized: {exception}')
        return True

    if isinstance(exception, exceptions.InvalidQueryID):
        logger.exception(f'InvalidQueryID: {exception} \nUpdate: {update}')
        return True

    if isinstance(exception, exceptions.TelegramAPIError):
        logger.exception(f'TelegramAPIError: {exception} \nUpdate: {update}')
        return True

    if isinstance(exception, exceptions.RetryAfter):
        logger.exception(f'RetryAfter: {exception} \nUpdate: {update}')
        return True
    
    if isinstance(exception, exceptions.CantParseEntities):
        logger.exception(f'CantParseEntities: {exception} \nUpdate: {update}')
        return True

    logger.exception(f'Update: {update} \n{exception}')


def handle_errors():
    def wrap(func):
        @functools.wraps(func)
        def run_func(*args):
            init_rollbar()
            try:
                return func(*args)
            except Exception as exe:
                rollbar.report_exc_info()
                title_of_error = SLUG_TO_EXCEPTIONS_TITLE.get(
                    get_slug_of_failure(exe), ''
                )
                if title_of_error:
                    logger.exception(title_of_error)
                else:
                    logger.exception(exe)
                raise exe

            finally:
                rollbar.wait()

        return run_func
    return wrap
