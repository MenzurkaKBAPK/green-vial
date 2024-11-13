import logging
import os

from dotenv import dotenv_values


BASE_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
DOTENV_PATH = os.path.join(BASE_DIR, ".env")

if os.path.exists(DOTENV_PATH):
    config = dotenv_values(DOTENV_PATH)
else:
    config = dict()


def env(key):
    return config.get(key)


DEBUG = eval(env("DEBUG"))

DISCORD_TOKEN = env("DISCORD_TOKEN")
APPLICATION_ID = env("APPLICATION_ID")
YANDEX_CLOUD_CATALOG = env("YANDEX_CLOUD_CATALOG")
YANDEX_API_KEY = env("YANDEX_API_KEY")
YANDEX_GPT_MODEL = env("YANDEX_GPT_MODEL")
API_HASH = env("API_HASH")
API_ID = env("API_ID")
API_TOKEN = env("API_TOKEN")

if DEBUG:
    LOGGING_LEVEL = logging.DEBUG
else:
    LOGGING_LEVEL = logging.INFO

PERMISSIONS = {
    "SYNC": 0,
    "GIVE_PERMISSION": 1,
    "REMOVE_PERMISSIONS": 2,
    "DRUGS": 3
}
PERMISSION_LEVELS = {
    0: ("Menzurka", list(PERMISSIONS.values())),
    1: ("Admin", list(PERMISSIONS.values())),
    2: ("Moderator", [0, 3]),
    3: ("Helper", [3])
}
