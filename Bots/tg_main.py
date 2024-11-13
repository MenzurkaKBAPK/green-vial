import logging
import logging.handlers
from time import sleep

from telethon import TelegramClient, errors, events

from config import (
    API_HASH,
    API_ID,
    API_TOKEN,
    LOGGING_LEVEL
)


logging.basicConfig(level=LOGGING_LEVEL)
logger = logging.getLogger("telethon")
logger.setLevel(LOGGING_LEVEL)

handler = logging.handlers.RotatingFileHandler(
    filename="logs/telegram.log",
    encoding="utf-8",
    maxBytes=32 * 1024 * 1024,
    backupCount=5,
)
dt_fmt = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(
    "[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

bot = TelegramClient('Vial', API_ID, API_HASH).start(bot_token=API_TOKEN)


@bot.on(events.NewMessage(pattern="/all"))
async def all_command(event):
    message = ""
    async for user in bot.iter_participants(event.chat):
        if user.bot:
            continue
        message += f"@{user.username}\n"
    await event.respond(message)
    logging.info(f"All command received from {event.sender_id}")


def start_bot():
    try:
        bot.start()
    except errors.FloodWaitError as e:
        logging.warning(f"FloodWaitError, have to sleep {e.seconds} seconds")
        sleep(e.seconds)
        start_cycle()


def start_cycle():
    try:
        bot.run_until_disconnected()
    except errors.FloodWaitError as e:
        logging.warning(f"FloodWaitError, have to sleep {e.seconds} seconds")
        sleep(e.seconds)
        start_cycle()


def main():
    start_bot()
    start_cycle()


if __name__ == "__main__":
    main()
