import json
import logging
import logging.handlers
import os
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
tags = dict()


@bot.on(events.NewMessage(pattern="/all"))
async def all_command(event):
    message = ""
    async for user in bot.iter_participants(event.chat):
        if user.bot:
            continue
        message += f"@{user.username}\n"

    if event.is_reply:
        await event.respond(message, reply_to=event.reply_to_msg_id)
    else:
        await event.respond(message)

    logging.info(f"`/all` command received from {event.sender_id}")


@bot.on(events.NewMessage(pattern='/tag'))
async def tag_handler(event):
    if "/tags" in event.raw_text:
        return

    chat_id = event.chat_id

    if chat_id not in tags:
        tags[chat_id] = {}

    args = event.raw_text.split()
    if len(args) < 3:
        await event.reply("Использование: /tag @user <tag>")
        return

    username = args[1]
    if not username.startswith('@'):
        await event.reply("Укажите username, начиная с @")
        return

    username = username[1:]
    tag = args[2].lower()

    if tag not in tags[chat_id]:
        tags[chat_id][tag] = []

    if username not in tags[chat_id][tag]:
        tags[chat_id][tag].append(username)
        await event.reply(f"Пользователь @{username} добавлен в тег '{tag}'")
    else:
        await event.reply(f"Пользователь @{username} уже есть в теге '{tag}'")

    logging.info(f"`/tag @{username} {tag}` command "
                 f"received from {event.sender_id}")


@bot.on(events.NewMessage(pattern='/ping'))
async def ping_handler(event):
    chat_id = event.chat_id

    args = event.raw_text.split()

    if len(args) == 1:
        await event.reply("pong!")
        logging.info(f"`/ping` command received from {event.sender_id}")
        return

    if chat_id not in tags or not tags[chat_id]:
        await event.reply("В этом чате еще нет тегов")
        return

    tag = args[1].lower()
    if tag not in tags[chat_id] or not tags[chat_id][tag]:
        await event.reply(f"Тег '{tag}' не найден или пуст в этом чате")
        return

    users_to_ping = "\n".join([f"@{u}" for u in tags[chat_id][tag]])
    message = f"Пинг по тегу '{tag}':\n{users_to_ping}"

    if event.is_reply:
        await event.respond(message, reply_to=event.reply_to_msg_id)
    else:
        await event.respond(message)

    logging.info(f"`/ping {tag}` command received from {event.sender_id}")


@bot.on(events.NewMessage(pattern='/tags'))
async def list_tags_handler(event):
    chat_id = event.chat_id

    if chat_id not in tags or not tags[chat_id]:
        await event.reply("В этом чате еще нет тегов")
        return

    tag_list = "\n".join([f"• {tag}: {len(users)} пользователей\n" +
                          "\n".join((f"[{user}](http://t.me/{user})"
                                     for user in users)) + "\n"
                         for tag, users in tags[chat_id].items()])

    await event.reply(f"Теги в этом чате:\n{tag_list}", parse_mode="md")

    logging.info(f"`/tags` command received from {event.sender_id}")


@bot.on(events.NewMessage(pattern='/untag'))
async def untag_handler(event):
    chat_id = event.chat_id

    args = event.raw_text.split()
    if len(args) < 3:
        await event.reply("Использование: /untag @user <tag>")
        return

    username = args[1]
    if not username.startswith('@'):
        await event.reply("Укажите username, начиная с @")
        return

    username = username[1:]
    tag = args[2].lower()

    if chat_id not in tags or tag not in tags[chat_id]:
        await event.reply(f"Тег '{tag}' не найден в этом чате")
        return

    if username in tags[chat_id][tag]:
        tags[chat_id][tag].remove(username)
        await event.reply(f"Пользователь @{username} удален из тега '{tag}'")

        if not tags[chat_id][tag]:
            del tags[chat_id][tag]
    else:
        await event.reply(f"Пользователь @{username} не найден в теге '{tag}'")

    logging.info(f"`/untag @{username} {tag}` command "
                 f"received from {event.sender_id}")


def start_bot():
    try:
        bot.start()
    except errors.FloodWaitError as e:
        logging.warning(f"FloodWaitError, have to sleep {e.seconds} seconds")
        sleep(e.seconds)
        start_bot()


def start_cycle():
    try:
        bot.run_until_disconnected()
    except errors.FloodWaitError as e:
        logging.warning(f"FloodWaitError, have to sleep {e.seconds} seconds")
        sleep(e.seconds)
        start_cycle()


def save_tags(filename='tags.json'):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json_data = {str(chat_id): tags for chat_id, tags in tags.items()}
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        return True, None
    except (IOError, TypeError) as e:
        return False, e


def load_tags(filename='tags.json'):
    global tags
    if not os.path.exists(filename):
        return False, "There is no such file"

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            tags = {int(chat_id): tags for chat_id, tags in data.items()}
        return True, None
    except (IOError, json.JSONDecodeError, ValueError) as e:
        return False, e


def main():
    print("   --==[ Green Vial Bot CLI ]==--\n")

    print("Trying to load tags from the tags.json file...")
    res, err = load_tags()
    if res:
        print("Successfully loaded the files\n")
    else:
        print(f"An error occurred while loading files: {err}\n")
    
    start_bot()
    start_cycle()

    res, err = save_tags()
    if res:
        print("Successfully saved the files\n")
    else:
        print(f"An error occurred while saving files: {err}\n")
    print("Bye!!")


if __name__ == "__main__":
    main()
