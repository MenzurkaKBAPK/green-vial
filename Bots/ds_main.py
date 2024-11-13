import datetime
import logging
import logging.handlers
import re
import threading
from random import choice, randint
from time import sleep
from typing import Optional

import discord
import schedule

from discord import app_commands
from discord.ext import commands
from sqlalchemy.orm import Session

from config import (
    DISCORD_TOKEN,
    LOGGING_LEVEL,
    PERMISSION_LEVELS,
    PERMISSIONS
)
from data import db_session
from data.delayed_messages import DelayedMessage
from data.permisions import UserPermissions
from data.phrases import Phrase
from data.servers import Server
from data.stats import Stats
from data.users import User
from methods import Bot, get_emission_info, start_timer, style_channel
from yagpt_request import yagpt_interact

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

ABOBI = discord.Object(id=123452343241231)
MSC = datetime.timezone(
    datetime.timedelta(hours=3)
)

updated_emission = False
unsorted_data = dict()
db_sess: Session = None


@client.command()
async def ping(ctx: commands.Context):
    user = db_sess.query(User).filter(
        User.user_id == ctx.author.id
    ).first()
    user = db_sess.query(UserPermissions).filter(
        UserPermissions.user_id == user.id
    ).first()
    if user is None:
        return
    await ctx.reply("pong")


@client.command()
async def echo(ctx: commands.Context, *args):
    user = db_sess.query(User).filter(
        User.user_id == ctx.author.id
    ).first()
    user = db_sess.query(UserPermissions).filter(
        UserPermissions.user_id == user.id
    ).first()
    if user is None:
        return
    await ctx.reply(" ".join(args))


@client.command()
async def tag_me(ctx: commands.Context):
    user = db_sess.query(User).filter(
        User.user_id == ctx.author.id
    ).first()
    user = db_sess.query(UserPermissions).filter(
        UserPermissions.user_id == user.id
    ).first()
    if user is None:
        return
    await ctx.send(f"<@{ctx.author.id}>")


@client.command()
async def style(
    ctx: commands.Context,
    channels: commands.Greedy[discord.TextChannel],
    *,
    border="+",
):
    user = db_sess.query(User).filter(
        User.user_id == ctx.author.id
    ).first()
    user = db_sess.query(UserPermissions).filter(
        UserPermissions.user_id == user.id
    ).first()
    if user is None:
        return
    styled_channels = [style_channel(channel, border) for channel in channels]
    await ctx.send("\n\n".join(styled_channels))


@client.command()
async def image(ctx: commands.Context):
    user = db_sess.query(User).filter(
        User.user_id == ctx.author.id
    ).first()
    user = db_sess.query(UserPermissions).filter(
        UserPermissions.user_id == user.id
    ).first()
    if user is None:
        return
    img = discord.File("static/img/tree.jpg")
    embed = discord.Embed()
    embed.set_image(url="attachment://tree.jpg")
    await ctx.reply(file=img, embed=embed)


@client.command()
async def foo(ctx: commands.Context):
    user = db_sess.query(User).filter(
        User.user_id == ctx.author.id
    ).first()
    user = db_sess.query(UserPermissions).filter(
        UserPermissions.user_id == user.id
    ).first()
    if user is None:
        return
    some_url = "https://fallendeity.github.io/discord.py-masterclass/"
    embed = discord.Embed(
        title="Title",
        description="Description",
        url=some_url,
        color=discord.Color.random(),
        timestamp=datetime.datetime.utcnow(),
    )
    embed.add_field(name="Field name", value="Color sets that <")
    embed.add_field(
        name="Field name",
        value=("Color should be an integer or discord.Colour object"),
    )
    embed.add_field(
        name="Field name", value="You can't set image width/height"
    )
    embed.add_field(
        name="Non-inline field name",
        value=(
            "The number of inline fields that can "
            "shown on the same row is limited to 3"
        ),
        inline=False,
    )
    embed.set_author(
        name="Author",
        url=some_url,
        icon_url=(
            "https://cdn.discordapp.com/attachments/1112418314581442650"
            "/1124820259384332319/fd0daad3d291ea1d.png"
        ),
    )
    embed.set_image(
        url=(
            "https://cdn.discordapp.com/attachments/1028706344158634084"
            "/1124822236801544324/ea14e81636cb2f1c.png"
        )
    )
    embed.set_thumbnail(
        url=(
            "https://media.discordapp.net/attachments/1112418314581442650"
            "/1124819948317986926/db28bfb9bfcdd1f6.png"
        )
    )
    embed.set_footer(
        text="Footer",
        icon_url=(
            "https://cdn.discordapp.com/attachments/1112418314581442650"
            "/1124820375587528797/dc4b182a87ecee3d.png"
        ),
    )
    await ctx.send(embed=embed)


@client.command()
async def sync(ctx: commands.Context):
    user = db_sess.query(User).filter(
        User.user_id == ctx.author.id
    ).first()
    if not user:
        return
    user = db_sess.query(UserPermissions).filter(
        UserPermissions.user_id == user.id
    ).first()
    if not user:
        return
    perm_lvl = user.permission_level
    role, permissions = PERMISSION_LEVELS[perm_lvl]
    if PERMISSIONS["SYNC"] not in permissions:
        return
    await client.tree.sync()
    await ctx.send("Синхронизация произведена, жесть", ephemeral=True)


@client.command()
async def give_permissions(ctx: commands.Context,
                           target_user: discord.Member,
                           perm_level: int | str):
    user = db_sess.query(User).filter(
        User.user_id == ctx.author.id
    ).first()
    if not user:
        return
    user = db_sess.query(UserPermissions).filter(
        UserPermissions.user_id == user.id
    ).first()
    if not user:
        return
    perm_lvl = user.permission_level
    role, permissions = PERMISSION_LEVELS[perm_lvl]

    if PERMISSIONS["GIVE_PERMISSION"] not in permissions:
        return
    if perm_level <= perm_lvl:
        await ctx.reply(
            (
                "Недостаточно полномочий: "
                f"{role} не может выдать {PERMISSION_LEVELS[perm_level][0]}"
            ), ephemeral=True
        )
        return

    user = db_sess.query(User).filter(
        User.user_id == target_user.id
    ).first()
    if not user:
        user = User(user_id=target_user.id)
        db_sess.add(user)

    user_perm = db_sess.query(UserPermissions).filter(
        UserPermissions.user_id == user.id
    ).first()
    if user_perm:
        if perm_level < user_perm.permission_level:
            user_perm.permission_level = perm_level
    else:
        user_perm = UserPermissions(
            user_id=user.id,
            permission_level=perm_level
        )
        db_sess.add(user_perm)

    db_sess.commit()


@client.command()
async def remove_permissions(ctx: commands.Context,
                             target_user: discord.Member):
    user = db_sess.query(User).filter(
        User.user_id == ctx.author.id
    )
    if not user:
        return
    user = user.first()
    user = db_sess.query(UserPermissions).filter(
        UserPermissions.user_id == user.id
    )
    if not user:
        return
    user = user.first()
    perm_lvl = user.permission_level
    role, permissions = PERMISSION_LEVELS[perm_lvl]

    if PERMISSIONS["REMOVE_PERMISSIONS"] not in permissions:
        return

    user = db_sess.query(User).filter(
        User.user_id == target_user.id
    ).first()
    if not user:
        return

    user_perm = db_sess.query(UserPermissions).filter(
        UserPermissions.user_id == user.id
    ).first()
    if user_perm:
        if perm_lvl < user_perm.permission_level:

            db_sess.delete(user_perm)
            db_sess.commit()

            await ctx.reply(
                "Полномочия отозваны",
                ephemeral=True
            )
        else:

            await ctx.reply(
                (
                    "Недостаточно полномочий: "
                    f"{role} не может снять "
                    f"{PERMISSION_LEVELS[user_perm.permission_level][0]}"
                ), ephemeral=True
            )


@client.command()
async def употребить(ctx: commands.Context):
    user = db_sess.query(User).filter(
        User.user_id == ctx.author.id
    ).first()
    if not user:
        return
    user = db_sess.query(UserPermissions).filter(
        UserPermissions.user_id == user.id
    ).first()
    if user is None:
        return
    perm_lvl = user.permission_level
    role, permissions = PERMISSION_LEVELS[perm_lvl]

    if PERMISSIONS["DRUGS"] not in permissions:
        return

    await ctx.send(f"<@{ctx.author.id}> употребил 3 кг кокаина одним вдохом")


@client.tree.command(
    name="пинг",
    description="Звенькнуть по боту",
    guild=ABOBI,
)
async def test_command(interaction: discord.Interaction):
    await interaction.response.send_message("Звень!", ephemeral=True)


@client.tree.command(
    name="gpt",
    description="Сделать запрос в яндекс-гпт",
    guild=ABOBI
)
@app_commands.describe(message="Сообщение боту")
@app_commands.rename(message="сообщение")
async def gpt_command(inter: discord.Interaction,
                      message: str):
    await inter.response.defer()
    answer = yagpt_interact(message)
    await inter.followup.send(answer, ephemeral=False)


@client.tree.command(
    name="гэпэтэ",
    description="Наиболее правильный запрос в яндекс-гпт",
    guild=ABOBI
)
@app_commands.describe(message="Сообщение боту")
@app_commands.rename(message="сообщение")
async def gepete_command(inter: discord.Interaction,
                         message: str):
    await inter.response.defer()
    answer = yagpt_interact(message)
    answer = answer.replace("мечи", "члены").replace("Мечи", "Члены")
    answer = answer.replace("меч", "член").replace("Меч", "Член")
    await inter.followup.send(answer, ephemeral=False)


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
    await inter.response.defer(ephemeral=True)
    pattern = r"(\d+d)? ?(\d+h)? ?(\d+m)?"
    if not (delay and re.fullmatch(pattern, delay)):
        await inter.followup.send(
            "Дата и время должны быть указаны в следующем формате:\n"
            "0d 0h 0m"
            "\nКаждый элемент (дни, часы, минуты) опицонален"
            "\n\nЗвень!", ephemeral=True
        )
        return
    delay = delay.split()
    days = hours = minutes = 0
    for elem in delay:
        if elem[-1] == "d":
            days = int(elem[:-1])
        elif elem[-1] == "h":
            hours = int(elem[:-1])
        else:
            minutes = int(elem[:-1])
    delay = datetime.timedelta(
        days=days,
        hours=hours,
        minutes=minutes
    )
    now = datetime.datetime.now(MSC)
    date_time = now + delay
    year, month, day, hour, minute = (
        date_time.year,
        date_time.month,
        date_time.day,
        date_time.hour,
        date_time.minute
    )
    to = to.strip()
    pattern = r"<@\d{18}>"
    if not re.fullmatch(pattern, to):
        await inter.followup.send(
            "Звень! В поле **to** упомяните пользователя, наример:\n"
            f"<@{inter.user.id}>", ephemeral=True
        )
        return
    to = int(to[2:-1])
    if inter.guild.get_member(to) is None:
        await inter.followup.send(
            "Не удалось найти пользователя на сервере, динь(", ephemeral=True
        )
        return
    from_user = db_sess.query(User).filter(
        User.user_id == inter.user.id).first()
    if from_user is None:
        from_user = User(
            user_id=inter.user.id
        )
        db_sess.add(from_user)
    to_user = db_sess.query(User).filter(
        User.user_id == to).first()
    if to_user is None:
        to_user = User(
            user_id=to
        )
        db_sess.add(to_user)
    delayed_message = DelayedMessage(
        from_user_id=from_user.user_id,
        to_user_id=to_user.user_id,
        message=message,
        day=day,
        month=month,
        year=year,
        hour=hour,
        minute=minute
    )
    db_sess.add(delayed_message)
    db_sess.commit()
    await inter.followup.send(
        "Сообщение запланировано. Динь!", ephemeral=True
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
    await inter.response.defer(ephemeral=True)
    pattern = r"(\d\d\.\d\d(\.\d\d\d\d+)? )?\d{1,2}:\d\d"
    if not re.fullmatch(pattern, date_time):
        await inter.followup.send(
            "Дата и время должны быть указаны в одном из следующих форматов:\n"
            "\nDD:MM:YYYY HH:MM"
            "\nDD:MM HH:MM"
            "\nHH:MM"
            "\n\nГод может быть больше четырехзначного, время можно указывать "
            "в вормате H:MM\nЧасовой пояс - МСК (UTC+3)"
            "\nЗвень!", ephemeral=True
        )
        return
    date_time = date_time.split()
    if len(date_time) == 2:
        date, time = date_time
    else:
        date, time = None, date_time[0]
    del date_time
    hour, minute = map(int, time.split(":"))
    del time
    now = datetime.datetime.now(MSC)
    add = False
    if date is None:
        if now.hour > hour or (now.hour == hour and now.minute > minute):
            add = True
        date = f"{now.day}.{now.month}.{now.year}"
    date = list(map(int, date.split(".")))
    if len(date) == 2:
        date.append(now.year)
    day, month, year = date
    del date
    date_time = datetime.datetime(
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        tzinfo=MSC
    )
    if add:
        date_time += datetime.timedelta(days=1)
    if date_time < now:
        await inter.followup.send(
            "К сожалению, я не могу отправиь сообщение в прошлое. Дзинь!",
            ephemeral=True
        )
        return
    year, month, day, hour, minute = (
        date_time.year,
        date_time.month,
        date_time.day,
        date_time.hour,
        date_time.minute
    )
    to = to.strip()
    pattern = r"<@\d{18}>"
    if not re.fullmatch(pattern, to):
        await inter.followup.send(
            "Звень! В поле **to** упомяните пользователя, наример:\n"
            f"<@{inter.user.id}>", ephemeral=True
        )
        return
    to = int(to[2:-1])
    if inter.guild.get_member(to) is None:
        await inter.followup.send(
            "Не удалось найти пользователя на сервере, динь(", ephemeral=True
        )
        return
    from_user = db_sess.query(User).filter(
        User.user_id == inter.user.id).first()
    if from_user is None:
        from_user = User(
            user_id=inter.user.id
        )
        db_sess.add(from_user)
    to_user = db_sess.query(User).filter(
        User.user_id == to).first()
    if to_user is None:
        to_user = User(
            user_id=to
        )
        db_sess.add(to_user)
    delayed_message = DelayedMessage(
        from_user_id=from_user.user_id,
        to_user_id=to_user.user_id,
        message=message,
        day=day,
        month=month,
        year=year,
        hour=hour,
        minute=minute
    )
    db_sess.add(delayed_message)
    db_sess.commit()
    await inter.followup.send(
        "Сообщение запланировано. Динь!", ephemeral=True
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
    if msg.author == client.user:
        return

    await client.process_commands(msg)

    unsorted_data[(msg.guild.id, msg.author.id)] = unsorted_data.get(
        (msg.guild.id, msg.author.id), 0) + 1

    if randint(1, 1000) == 348:
        funny_phrases = db_sess.query(Phrase).all()
        response = choice(funny_phrases).phrase.replace("\\n", "\n")
        await msg.channel.send(response)


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
    now = datetime.datetime.now(MSC)
    delayed_messages = db_sess.query(DelayedMessage).filter().all()
    for dm in delayed_messages:
        dm_datetime = datetime.datetime(
            year=dm.year,
            month=dm.month,
            day=dm.day,
            hour=dm.hour,
            minute=dm.minute,
            tzinfo=MSC
        )
        if dm_datetime > now:
            continue
        user = await bot.fetch_user(f"{dm.to_user_id}")
        content = (
            f"Сообщение от <@{dm.from_user_id}>\n>>> {dm.message}"
        )
        await discord.DMChannel.send(user, content)
        db_sess.delete(dm)
    db_sess.commit()


def on_stats_update():
    global unsorted_data
    for key, value in unsorted_data.items():
        key = tuple(map(str, key))
        server = db_sess.query(Server).filter(
            Server.server_id == key[0]
        ).first()
        if not server:
            server = Server(
                server_id=key[0]
            )
            db_sess.add(server)
        user = db_sess.query(User).filter(
            User.user_id == key[1]
        ).first()
        if not user:
            user = User(user_id=key[1])
            db_sess.add(user)
        stats = db_sess.query(Stats).filter(
            Stats.user_id == user.id,
            Stats.server_id == server.id
        ).first()
        if not stats:
            stats = Stats(
                user_id=user.id,
                server_id=server.id,
                message_count=value
            )
            db_sess.add(stats)
        else:
            stats.message_count += value
    db_sess.commit()
    unsorted_data = dict()


def main():
    global db_sess
    db_session.global_init("db/main.db")
    db_sess = db_session.create_session()

    timer = threading.Thread(target=start_timer, name="timer")
    timer.start()

    schedule.every(45).seconds.do(client.dispatch, "emission_update", client)
    schedule.every().minute.at(":00").do(client.dispatch, "send_dms", client)
    schedule.every().minute.at(":00").do(on_stats_update)

    client.run(DISCORD_TOKEN, log_handler=None)


if __name__ == "__main__":
    main()


'''
    - Отложенные сообщения [сделано]
    - синхронизация по команде (только людей из вайтлиста)
    - работа с вайтлистом, сам вайтлист
    - вайтлист - таблица с полями [id, user_id, sync, add_whitelist,
    remove_whitelist...] <- каждый столбец - разрешение на действие
    - Спросить у траллки
'''
