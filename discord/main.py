import logging
import logging.handlers
import threading
from time import sleep
from typing import Optional

import discord
import schedule

from discord import app_commands
from discord.ext import commands
from sqlalchemy.orm import Session

import commands.admin as admin
import commands.slash as slash
import errors.errors as errors
import events.events as events
from config import (
    DATABASE_URL,
    DISCORD_TOKEN,
    LOGGING_LEVEL,
)
from data import db_session
from methods import (
    Bot,
    get_emission_info,
    start_timer,
)

logger = logging.getLogger("discord")
logger.setLevel(LOGGING_LEVEL)
logging.getLogger("discord.http").setLevel(LOGGING_LEVEL)

handler = logging.handlers.RotatingFileHandler(
    filename="logs/discord.log",
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

intents = discord.Intents.all()
client = Bot(command_prefix="!", intents=intents)

ABOBI = discord.Object(id=720193412485349437)

updated_emission = False
unsorted_data = dict()
db_sess: Session = None
private_channels = dict()
private_channels_list = set()


@client.command()
async def ping(ctx: commands.Context):
    await admin.ping(
        ctx=ctx,
        db_sess=db_sess,
    )


@client.command()
async def sync(ctx: commands.Context):
    await admin.sync(
        ctx=ctx,
        db_sess=db_sess,
        client=client,
    )


@client.command()
async def give_permissions(ctx: commands.Context,
                           target_user: discord.Member,
                           perm_level: int | str):
    await admin.give_permissions(
        ctx=ctx,
        target_user=target_user,
        perm_level=perm_level,
        db_sess=db_sess,
    )


@client.command()
async def remove_permissions(ctx: commands.Context,
                             target_user: discord.Member):
    await admin.remove_permissions(
        ctx=ctx,
        target_user=target_user,
        db_sess=db_sess,
    )


@client.command()
@commands.has_guild_permissions(administrator=True)
async def add_new_channel(ctx: commands.Context,
                          channel_link: str):
    await admin.add_new_channel(
        ctx=ctx,
        channel_link=channel_link,
        db_sess=db_sess,
        client=client,
    )


@add_new_channel.error
async def add_new_channel_error(ctx: commands.Context, error):
    await errors.add_new_channel_error(
        ctx=ctx,
        error=error,
    )


@client.command()
@commands.has_guild_permissions(administrator=True)
async def remove_new_channel(ctx: commands.Context,
                             channel_link: str):
    await admin.remove_new_channel(
        ctx=ctx,
        channel_link=channel_link,
        db_sess=db_sess,
        client=client,
    )


@remove_new_channel.error
async def remove_new_channel_error(ctx: commands.Context, error):
    await errors.remove_new_channel_error(
        ctx=ctx,
        error=error,
    )


@client.command()
async def употребить(ctx: commands.Context):
    await admin.употребить(
        ctx=ctx,
        db_sess=db_sess,
    )


@client.tree.command(
    name="пинг",
    description="Звенькнуть по боту",
    guild=ABOBI,
)
async def slash_ping(interaction: discord.Interaction):
    await slash.slash_ping(
        interaction=interaction,
    )


@client.tree.command(
    name="gpt",
    description="Сделать запрос в яндекс-гпт",
    guild=ABOBI
)
@app_commands.describe(message="Сообщение боту")
@app_commands.rename(message="сообщение")
async def gpt_command(inter: discord.Interaction,
                      message: str):
    await slash.gpt_command(
        inter=inter,
        message=message,
    )


@client.tree.command(
    name="гэпэтэ",
    description="Наиболее правильный запрос в яндекс-гпт",
    guild=ABOBI
)
@app_commands.describe(message="Сообщение боту")
@app_commands.rename(message="сообщение")
async def gepete_command(inter: discord.Interaction,
                         message: str):
    await slash.gepete_command(
        inter=inter,
        message=message,
    )


@client.tree.command(
    name="отправить-через",
    description="Отправка сообщения через установленный промежуток времени",
    guild=ABOBI
)
@app_commands.describe(
    message="Сообщение для отправки",
    to="Пользователь, которому отправляется сообщение",
    delay="Время, по прошествии которого отправить сообщение"
)
@app_commands.rename(
    message="сообщение",
    to="кому",
    delay="задержка"
)
async def delayed_sending(inter: discord.Interaction,
                          message: str,
                          to: str,
                          delay: str):
    await slash.delayed_sending(
        inter=inter,
        message=message,
        to=to,
        delay=delay,
        db_sess=db_sess,
    )


@client.tree.command(
    name="отправить",
    description="Отправка сообщения пользователю в установленное время",
    guild=ABOBI
)
@app_commands.describe(
    message="Сообщение для отправки",
    to="Пользователь, которому отправляется сообщение",
    date_time="Когда отправить сообщение"
)
@app_commands.rename(
    message="сообщение",
    to="кому",
    date_time="дата-время"
)
async def scheduled_sending(inter: discord.Interaction,
                            message: str,
                            to: str,
                            date_time: str):
    await slash.scheduled_sending(
        inter=inter,
        message=message,
        to=to,
        date_time=date_time,
        db_sess=db_sess,
    )


@client.tree.command(
    name="тест",
    description="тест необязательных параметров",
    guild=ABOBI
)
@app_commands.describe(arg="тестовый опциональный аргумент")
@app_commands.rename(arg="аргумент")
async def test(inter: discord.Interaction,
               arg: Optional[str]):
    if arg:
        await inter.response.send_message(arg + " Звень!")
    else:
        await inter.response.send_message("Дилинь!")


@client.event
async def on_message(msg: discord.Message):
    await events.on_message(
        msg=msg,
    )


# rework
@client.event
async def on_emission_update(bot: Bot):
    global updated_emission
    if updated_emission:
        return
    if get_emission_info():
        updated_emission = True
        channel = bot.get_channel(1202743067816362034)
        await channel.send("@everyone emission!")
        sleep(600)
        updated_emission = False


@client.event
async def on_send_dms(bot: Bot):
    await events.on_send_dms(
        bot=bot,
        db_sess=db_sess,
    )


@client.event
async def on_voice_state_update(
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState):
    await events.on_voice_state_update(
        member=member,
        before=before,
        after=after,
        db_sess=db_sess,
        private_channels=private_channels,
        private_channels_list=private_channels_list,
    )


@client.event
async def on_guild_channel_delete(channel):
    await events.on_guild_channel_delete(
        channel=channel,
        db_sess=db_sess,
        private_channels=private_channels,
        private_channels_list=private_channels_list,
    )


def main():
    global db_sess
    db_session.global_init(db_url=DATABASE_URL)
    db_sess = db_session.create_session()

    timer = threading.Thread(target=start_timer, name="timer")
    timer.start()

    schedule.every(45).seconds.do(client.dispatch, "emission_update", client)
    schedule.every().minute.at(":00").do(client.dispatch, "send_dms", client)
    schedule.every().minute.at(":00").do(
        lambda: events.on_stats_update(db_sess=db_sess))

    client.run(DISCORD_TOKEN, log_handler=None)


if __name__ == "__main__":
    main()


# создать канал -> выйти -> дурной канал остался
# добавить периодическую проверку на пиватки
