import json
import re
import requests
import time
import functools

from environs import Env
from contextlib import contextmanager

from exceptions import (HhTokenError, HhInvalidAuthPage)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    StaleElementReferenceException,
    NoSuchElementException,
    TimeoutException
)
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

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


def search_elements(driver, *locator):
    found_items = wait_until_found(driver.find_elements, *locator)
    if not found_items:
        raise HhInvalidAuthPage

    return found_items


def get_authorize_code(url):
    with start_chrome_driver(f'http://{selenium_server}/wd/hub') as driver:

        driver.get(url)

        email_element = search_elements(driver, By.XPATH, "//input[@placeholder='Email']")[0]
        email_element.send_keys(env('HH_EMAIL'))
        pass_element = search_elements(driver, By.XPATH, "//input[@placeholder='Пароль']")[0]
        pass_element.send_keys(env('HH_PASSWORD'))

        account_login_container = driver.find_element(By.CLASS_NAME, 'account-login-actions')
        button_element = search_elements(account_login_container, By.TAG_NAME, "button")[0]   
        button_element.click()

        time.sleep(1)
        redirect_url = driver.current_url
        result_match = re.search(AUTHORIZE_CODE_PATTERN, redirect_url)
        if not result_match:
            return None

        return result_match[0].replace('code=','').split('&')[0]


def update_access_token(url, authorize_code):
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
    params={
        'client_id': env('HH_CLIENT_ID'),
        'client_secret': env('HH_CLIENT_SECRET'),
        'grant_type': 'authorization_code',
        'code': authorize_code
    }

    response = requests.post(url, headers=headers, params=params)
    response.raise_for_status()

    user_access_token = response.json()
    with open('hh_token.json', 'w') as file_handler:
        json.dump(user_access_token, file_handler)


def get_access_token():
    with open('hh_token.json') as file_handler:
        token_info = json.load(file_handler)
        return token_info['access_token']


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
