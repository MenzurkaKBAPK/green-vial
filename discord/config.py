import logging
import os


def env(key, or_else=None):
    return os.getenv(key) or or_else


def get_database_url():
    user = env("POSTGRES_USER")
    password = env("POSTGRES_PASSWORD")
    host = env("POSTGRES_HOST", "localhost")
    port = env("POSTGRES_PORT", "5432")
    db_name = env("POSTGRES_DB")

    if all([user, password, host, port, db_name]):
        return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"

    return env("DATABASE_URL", "sqlite:///db/main.db?check_same_thread=False")


DEBUG = eval(str(env("DEBUG")))

DATABASE_URL = get_database_url()
DISCORD_TOKEN = env("DISCORD_TOKEN")
APPLICATION_ID = env("APPLICATION_ID")
YANDEX_CLOUD_CATALOG = env("YANDEX_CLOUD_CATALOG")
YANDEX_API_KEY = env("YANDEX_API_KEY")
YANDEX_GPT_MODEL = env("YANDEX_GPT_MODEL")

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
CHANNEL_TYPES = {
    "NEW_CHANNEL": 0
}
