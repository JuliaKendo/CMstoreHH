import re
import requests
import time
import functools

from environs import Env
from contextlib import contextmanager

from exceptions import (HhTokenError, HhInvalidAuthPage, HhAuthCodeError)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    StaleElementReferenceException,
    NoSuchElementException,
    TimeoutException
)
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

import settings

AUTHORIZE_CODE_PATTERN = r'''(?:code=).+$'''

env = Env()
env.read_env()
selenium_server = env('SELENIUM_SERVER')


@contextmanager
def start_chrome_driver(selenium_server_url):
    """Launch the Chrome driver.

    At the end of the work, it close up all open windows,
    exits the browser and services, and release up all resources.
    """
    driver = webdriver.Remote(selenium_server_url, DesiredCapabilities.CHROME)
    try:
        yield driver
    finally:
        driver.quit()


def wait_until_found(callback, *args):
    max_num_iterations = 10
    while True:
        if not max_num_iterations:
            raise TimeoutException

        try:
            found_element = callback(*args)
        except (
            NoSuchElementException,
            StaleElementReferenceException
        ):
            max_num_iterations -= 1
            time.sleep(1)
            continue

        return found_element


def check_element(driver, by, locator):
    return wait_until_found(driver.find_elements, by, locator)


def search_elements(driver, by, *args):
    found_items = None
    for locator in args:
        found_items = wait_until_found(driver.find_elements, by, locator)
        if found_items:
            return found_items

    if not found_items:
        raise HhInvalidAuthPage


def manage_auth_elements(driver):
    auth_area = 'oauth-authorize-primary-button'
    login_area = 'account-login-actions'

    if wait_until_found(driver.find_elements, By.CLASS_NAME, auth_area):
        # Обработка нажатия кнопки авторизации "Продолжить", кода вход в приложение уже выполнен.
        auth_form = driver.find_element(By.CLASS_NAME, auth_area)
        button_element = search_elements(auth_form, By.TAG_NAME, "button")[0]
        button_element.click()
        return

    email_element = search_elements(
        driver,
        By.XPATH,
        "//input[@placeholder='Email']",
        "//input[@placeholder='Электронная почта']"
    )[0]
    email_element.send_keys(env('HH_EMAIL'))
    pass_element = search_elements(
        driver,
        By.XPATH,
        "//input[@placeholder='Пароль']"
    )[0]
    pass_element.send_keys(env('HH_PASSWORD'))

    login_form = driver.find_element(By.CLASS_NAME, login_area)
    button_element = search_elements(login_form, By.TAG_NAME, "button")[0]
    button_element.click()


def get_authorize_code(url):
    with start_chrome_driver(f'http://{selenium_server}/wd/hub') as driver:

        driver.get(url)
        manage_auth_elements(driver)
        time.sleep(1)

        redirect_url = driver.current_url
        result_match = re.search(AUTHORIZE_CODE_PATTERN, redirect_url)
        if not result_match:
            raise HhAuthCodeError

        return result_match[0].replace('code=', '').split('&')[0]


def update_access_token(url, authorize_code):
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    params = {
        'client_id': env('HH_CLIENT_ID'),
        'client_secret': env('HH_CLIENT_SECRET'),
        'grant_type': 'authorization_code',
        'code': authorize_code
    }

    response = requests.post(url, headers=headers, params=params)
    response.raise_for_status()

    user_access_token = response.json()
    if settings.use_sqlite:
        cursor = settings.sqlite_conn.cursor()

        cursor.execute('SELECT token FROM Tokens WHERE id="access_token"')
        found_access_token = cursor.fetchone()
        if not found_access_token:
            cursor.execute(
                'INSERT INTO Tokens VALUES(?, ?);', (
                    'access_token', f'{user_access_token["access_token"]}'
            ))
        else:
            cursor.execute(
                'UPDATE Tokens SET token = ? WHERE id = ?', (
                    f'{user_access_token["access_token"]}', 'access_token'
            ))

        cursor.execute('SELECT token FROM Tokens WHERE id="refresh_token"')
        found_refresh_token = cursor.fetchone()
        if not found_refresh_token:
            cursor.execute(
                'INSERT INTO Tokens VALUES(?, ?);', (
                    'refresh_token', f'{user_access_token["refresh_token"]}'
            ))
        else:
            cursor.execute(
                'UPDATE Tokens SET token = ? WHERE id = ?', (
                    f'{user_access_token["refresh_token"]}', 'refresh_token'
            ))
        settings.sqlite_conn.commit()
    else:
        settings.redis_conn.hmset('hh_token', user_access_token)


def get_access_token():
    if settings.use_sqlite:
        cursor = settings.sqlite_conn.cursor()
        cursor.execute('SELECT token FROM Tokens WHERE id="access_token"')
        found_token = cursor.fetchone()
        if not found_token:
            raise HhTokenError
        hh_token, = found_token
        return hh_token
    hh_token = settings.redis_conn.hmget('hh_token', 'access_token')[0]
    if not hh_token:
        raise HhTokenError
    return hh_token.decode()


def sign_in_hh():
    def wrap(func):
        @functools.wraps(func)
        def run_func(*args):
            authorize_url = f"https://hh.ru/oauth/authorize\?response_type=code&client_id={env('HH_CLIENT_ID')}"
            access_url = 'https://hh.ru/oauth/token'
            while True:
                try:
                    return func(*args, get_access_token())

                except (HhTokenError, FileNotFoundError) :
                    authorize_code = get_authorize_code(authorize_url)
                    update_access_token(access_url, authorize_code)
                    continue

        return run_func
    return wrap
