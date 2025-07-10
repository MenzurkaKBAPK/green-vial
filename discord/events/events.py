import datetime
from random import choice, randint

import discord
from sqlalchemy.orm import Session

from config import CHANNEL_TYPES
from data.channels import Channels
from data.delayed_messages import DelayedMessage
from data.phrases import Phrase
from data.servers import Server
from data.stats import Stats
from data.users import User
from methods import (
    Bot,
    create_channel,
    delete_channel,
    get_key_by_value,
    save_channel_data,
)


MSC = datetime.timezone(
    datetime.timedelta(hours=3)
)


async def on_message(msg: discord.Message,
                     client: Bot,
                     unsorted_data: dict,
                     db_sess: Session):
    if msg.author == client.user:
        return

    await client.process_commands(msg)

    unsorted_data[(msg.guild.id, msg.author.id)] = unsorted_data.get(
        (msg.guild.id, msg.author.id), 0) + 1

    if randint(1, 1000) == 348:
        funny_phrases = db_sess.query(Phrase).all()
        response = choice(funny_phrases).phrase.replace("\\n", "\n")
        await msg.channel.send(response)


async def on_send_dms(bot: Bot,
                      db_sess: Session):
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


async def on_voice_state_update(
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
        db_sess: Session,
        private_channels: dict,
        private_channels_list: dict):
    if after.channel:
        server_id = member.guild.id
        channel_id = after.channel.id

        guild = db_sess.query(Server).filter_by(
            server_id=server_id
        ).first()
        if not guild:
            return

        channel = db_sess.query(Channels).filter_by(
            server_id=guild.id,
            channel_id=channel_id,
            channel_type=CHANNEL_TYPES["NEW_CHANNEL"]).first()

        if channel:
            new_voice_channel = await create_channel(
                member=member,
                voice_state=after,
                db_sess=db_sess
            )

            await member.move_to(new_voice_channel)

            private_channels[member.id] = (server_id, new_voice_channel.id)
            private_channels_list.add((server_id, new_voice_channel.id))

    if before.channel:
        server_id = member.guild.id
        channel_id = before.channel.id

        if (server_id, channel_id) in private_channels.values() \
           and not before.channel.members:

            owner_id = get_key_by_value(
                private_channels, (server_id, channel_id))
            await delete_channel(
                member=member,
                owner_id=owner_id,
                voice_state=before,
                db_sess=db_sess
            )

            try:
                del private_channels[owner_id]
            except KeyError:
                pass
            try:
                private_channels_list.remove((server_id, channel_id))
            except KeyError:
                pass


async def on_guild_channel_delete(channel,
                                  db_sess: Session,
                                  private_channels: dict,
                                  private_channels_list: dict):
    if isinstance(channel, discord.VoiceChannel):
        guild_id = channel.guild.id
        channel_id = channel.id
        if (guild_id, channel_id) in private_channels.values():
            owner_id = get_key_by_value(
                private_channels, (guild_id, channel_id))
            if owner_id is None:
                return

            user_id = db_sess.query(User).filter_by(
                user_id=owner_id
            ).first().id
            guild_id = db_sess.query(Server).filter_by(
                server_id=channel.guild.id
            ).first().id

            await save_channel_data(
                channel=channel,
                user_id=user_id,
                guild_id=guild_id,
                db_sess=db_sess
            )

            try:
                del private_channels[owner_id]
            except KeyError:
                pass
            try:
                private_channels_list.remove((guild_id, channel_id))
            except KeyError:
                pass


def on_stats_update(db_sess: Session):
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
