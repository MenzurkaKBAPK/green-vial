import datetime
import re

import discord
from sqlalchemy.orm import Session

from data.delayed_messages import DelayedMessage
from data.users import User
from yagpt_request import yagpt_interact


MSC = datetime.timezone(
    datetime.timedelta(hours=3)
)


async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message("Звень!", ephemeral=True)


async def gpt_command(inter: discord.Interaction,
                      message: str):
    await inter.response.defer()
    answer = yagpt_interact(message)
    await inter.followup.send(answer, ephemeral=False)


async def gepete_command(inter: discord.Interaction,
                         message: str):
    await inter.response.defer()
    answer = yagpt_interact(message
                            ).replace("мечи", "члены"
                            ).replace("Мечи", "Члены"
                            ).replace("меч", "член"
                            ).replace("Меч", "Член")
    await inter.followup.send(answer, ephemeral=False)


async def delayed_sending(inter: discord.Interaction,
                          message: str,
                          to: str,
                          delay: str,
                          db_sess: Session):
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


async def scheduled_sending(inter: discord.Interaction,
                            message: str,
                            to: str,
                            date_time: str,
                            db_sess: Session):
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
