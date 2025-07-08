import logging
import os

from dotenv import dotenv_values


BASE_DIR = os.path.dirname(os.path.realpath(__file__))
DOTENV_PATH = os.path.join(BASE_DIR, ".env")

if os.path.exists(DOTENV_PATH):
    config = dotenv_values(DOTENV_PATH)
else:
    config = dict()


def env(key):
    return config.get(key)


DEBUG = eval(str(env("DEBUG")))

API_HASH = env("API_HASH")
API_ID = env("API_ID")
API_TOKEN = env("API_TOKEN")

if DEBUG:
    LOGGING_LEVEL = logging.DEBUG
else:
    LOGGING_LEVEL = logging.INFO
