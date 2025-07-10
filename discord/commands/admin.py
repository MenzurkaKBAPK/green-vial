import datetime
import re

import discord
from discord.ext import commands
from sqlalchemy.orm import Session

from data.channels import Channels
from data.permisions import UserPermissions
from data.servers import Server
from data.users import User
from config import (
    CHANNEL_TYPES,
    PERMISSIONS,
    PERMISSION_LEVELS,
)
from methods import Bot


async def ping(ctx: commands.Context, db_sess: Session):
    user = db_sess.query(User).filter(
        User.user_id == ctx.author.id
    ).first()
    user = db_sess.query(UserPermissions).filter(
        UserPermissions.user_id == user.id
    ).first()
    if user is None:
        return
    await ctx.reply("pong")


async def give_permissions(ctx: commands.Context,
                           target_user: discord.Member,
                           perm_level: int | str,
                           db_sess: Session):
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


async def remove_permissions(ctx: commands.Context,
                             target_user: discord.Member,
                             db_sess: Session):
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


async def add_new_channel(ctx: commands.Context,
                          channel_link: str,
                          db_sess: Session,
                          client: Bot):
    link_pattern = (
        r"https:\/\/discord\.com\/channels\/(\d{18,19})\/(\d{18,19})"
    )
    match_ = re.fullmatch(link_pattern, channel_link)
    if match_:
        server_id = match_.group(1)
        server = db_sess.query(Server).filter_by(
            server_id=server_id
        ).first()
        if not server:
            server = Server(
                server_id=server_id
            )
            db_sess.add(server)
        server_id = server.id

        channel_id = match_.group(2)

        guild = await client.fetch_guild(server.server_id)
        voice_channel = await guild.fetch_channel(channel_id)

        if isinstance(voice_channel, discord.VoiceChannel):
            bot_member = (
                guild.me if guild.me else await guild.fetch_member(
                    ctx.bot.user.id)
            )
            if bot_member is None:
                await ctx.reply(
                    "Не удалось получить объект бота.",
                    ephemeral=True
                    )
                return
            permissions = voice_channel.permissions_for(bot_member)
            if permissions.move_members:
                channel = db_sess.query(Channels).filter_by(
                    server_id=server_id,
                    channel_id=channel_id
                ).first()
                if channel:
                    await ctx.reply(
                        (
                            "Канал уже записан и "
                            "для чего-то используется"
                        ), ephemeral=True
                    )
                    return
                channel = Channels(
                    server_id=server_id,
                    channel_id=channel_id,
                    channel_type=CHANNEL_TYPES["NEW_CHANNEL"]
                )
                db_sess.add(channel)
                db_sess.commit()
                await ctx.reply(
                    (
                        "Запись создана, канал будет "
                        "использоваться для создания личных комнат"
                    ), ephemeral=True
                )
            else:
                await ctx.reply(
                    (
                        "У бота недостаточно прав для "
                        "перемещения участника из канала."
                    ), ephemeral=True
                )
        db_sess.commit()
    else:
        await ctx.reply(
            (
                "Ссылка не соответствует шаблону "
                "`https://discord.com/channels/"
                "0000000000000000000/0000000000000000000`"
            ), ephemeral=True
        )


async def remove_new_channel(ctx: commands.Context,
                             channel_link: str,
                             db_sess: Session,
                             client: Bot):
    link_pattern = (
        r"https:\/\/discord\.com\/channels\/(\d{18,19})\/(\d{18,19})"
    )
    match_ = re.fullmatch(link_pattern, channel_link)
    if match_:
        server_id = match_.group(1)
        server = db_sess.query(Server).filter_by(
            server_id=server_id
        ).first()
        if not server:
            server = Server(
                server_id=server_id
            )
            db_sess.add(server)
        server_id = server.id

        channel_id = match_.group(2)

        guild = await client.fetch_guild(server.server_id)
        voice_channel = await guild.fetch_channel(channel_id)

        if isinstance(voice_channel, discord.VoiceChannel):
            channel = db_sess.query(Channels).filter_by(
                server_id=server_id,
                channel_id=channel_id
            ).first()
            if not channel:
                await ctx.reply(
                    (
                        "Канал не записан в базе"
                    ), ephemeral=True
                )
                return
            db_sess.delete(channel)
            await ctx.reply(
                (
                    "Запись удалена, канал больше не будет "
                    "использоваться"
                ), ephemeral=True
            )
        db_sess.commit()
    else:
        await ctx.reply(
            (
                "Ссылка не соответствует шаблону "
                "`https://discord.com/channels/"
                "0000000000000000000/0000000000000000000`"
            ), ephemeral=True
        )


async def sync(ctx: commands.Context, db_sess: Session, client: Bot):
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
    _, permissions = PERMISSION_LEVELS[perm_lvl]
    if PERMISSIONS["SYNC"] not in permissions:
        return
    await client.tree.sync()
    await ctx.send("Синхронизация произведена, жесть", ephemeral=True)


async def употребить(ctx: commands.Context,
                     db_sess: Session):
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
    _, permissions = PERMISSION_LEVELS[perm_lvl]

    if PERMISSIONS["DRUGS"] not in permissions:
        return

    await ctx.send(f"<@{ctx.author.id}> употребил 3 кг кокаина одним вдохом")


async def foo(ctx: commands.Context, db_sess: Session):
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
