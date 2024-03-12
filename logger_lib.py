import logging
# import telegram
import requests


class NotificationLogHandler(logging.Handler):

    def __init__(self, token, chat_id):
        super().__init__()
        self.token = token
        self.chat_id = chat_id

    def emit(self, record):
        log_entry = self.format(record)
        if log_entry:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            params = {
                "chat_id": self.chat_id,
                "text": log_entry,
            }
            resp = requests.get(url, params=params)

            resp.raise_for_status()


def initialize_logger(logger, log_token, chat_id):
    format='%(asctime)s - [%(levelname)s] - (%(filename)s).%(funcName)s.%(lineno)s - [%(msg)s]'
    handler = NotificationLogHandler(log_token, chat_id)
    formatter = logging.Formatter(format)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)