from html.parser import HTMLParser
from time import sleep

import discord
import requests
import schedule
from discord import TextChannel
from discord.member import Member, VoiceState
from discord.ext import commands
from sqlalchemy.orm import Session

from data.channel_settings import ChannelSettings
from data.servers import Server
from data.users import User


class HtmlToDict(HTMLParser):
    def __init__(self, *, convert_charrefs=True):
        self.convert_charrefs = convert_charrefs
        self.reset()

        self.data = dict()
        self.tags = []

    def data_reset(self):
        self.data = dict()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        if tag in ("meta", "link"):
            return
        if self.tags:
            data = self.data
            for t in self.tags:
                data = data[t]
            if tag not in data.keys():
                data[tag] = dict()
        else:
            if tag not in self.data.keys():
                self.data[tag] = dict()
        self.tags.append(tag)

    def handle_endtag(self, tag):
        if self.tags and self.tags[-1] == tag:
            self.tags.pop()

    def handle_data(self, html_data):
        if self.tags:
            data = self.data
            for t in self.tags:
                data = data[t]
            data["data"] = data.get("data", []) + [html_data]
        else:
            self.data["data"] = self.data.get("data", []) + [html_data]

    def feed(self, data):
        self.data_reset()
        super().feed(data)

        return self.data


class Bot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await self.tree.sync(guild=discord.Object(id=720193412485349437))
            self.synced = True
        print(f"We have logged in as {self.user}.")


def style_channel(channel: TextChannel, border):
    k = len(channel.name) + 5
    return border * k + f"\n{border} <#{channel.id}> {border}\n" + border * k


def get_emission_info():
    response = requests.get(
        "https://last-emission-stalcraft.vercel.app/RU"
    ).text
    parser = HtmlToDict()
    data = parser.feed(response)
    emission_info = data["html"]["body"]["div"]["body"]["main"]["article"]
    if "h4" in emission_info.keys() and "data" in emission_info["h4"].keys():
        return not any(
            "Risk Level" in data for data in emission_info["h4"]["data"]
        )
    return True


def start_timer():
    while True:
        schedule.run_pending()
        sleep(1)


def get_key_by_value(dict_, search_value):
    for key, value in dict_.items():
        if value == search_value:
            return key


async def create_channel(
        member: Member,
        voice_state: VoiceState,
        db_sess: Session):
    category = voice_state.channel.category

    server = db_sess.query(Server).filter_by(
        server_id=member.guild.id
    ).first()
    if not server:
        server = Server(
            server_id=member.guild.id
        )
        db_sess.add(server)
    server_id = server.id

    user = db_sess.query(User).filter_by(
        user_id=member.id
    ).first()
    if not user:
        user = User(
            user_id=member.id
        )
        db_sess.add(user)
        db_sess.commit()
    user_id = user.id

    channel_settings = db_sess.query(ChannelSettings).filter_by(
        server_id=server_id,
        user_id=user_id
    ).first()
    if not channel_settings:
        channel_settings = ChannelSettings(
            user_id=user_id,
            server_id=server_id,
            name=f"{member.display_name}'s channel",
            permissions="{}"
        )
    channel_name = channel_settings.name

    channel = await member.guild.create_voice_channel(
        name=channel_name,
        category=category
    )

    permissions = (
        eval(channel_settings.permissions)
        if channel_settings.permissions != "{}"
        else dict()
    )

    user_index = f"<class 'discord.member.Member'>/{user.user_id}"
    permissions[user_index] = permissions.get(user_index, dict())
    permissions[user_index]['manage_channels'] = True
    permissions[user_index]['read_messages'] = True
    permissions[user_index]['manage_roles'] = True

    new_overwrites = channel.overwrites
    for role_index, perms in permissions.items():
        role, id_ = role_index.split("/")
        if "discord.role.Role" in role:
            roles = await member.guild.fetch_roles()
            role_index = next(
                (role for role in roles if role.id == int(id_)),
                None
            )
        else:
            role_index = await member.guild.fetch_member(int(id_))
        for perm, value in perms.items():
            new_overwrites[role_index] = new_overwrites.get(
                role_index,
                discord.PermissionOverwrite()
            )
            new_overwrites[role_index]._values[perm] = value

    await channel.edit(overwrites=new_overwrites)

    return channel


async def delete_channel(
        member: Member,
        voice_state: VoiceState,
        owner_id: int | None,
        db_sess: Session):
    if owner_id:
        user_id = db_sess.query(User).filter_by(
            user_id=owner_id,
        ).first().id
        server_id = db_sess.query(Server).filter_by(
            server_id=member.guild.id
        ).first().id

        await save_channel_data(
            channel=voice_state.channel,
            user_id=user_id,
            guild_id=server_id,
            db_sess=db_sess
        )

    await voice_state.channel.delete()


async def save_channel_data(
        channel: discord.VoiceChannel,
        user_id: int,
        guild_id: int,
        db_sess: Session):
    channel_name = channel.name
    permissions = dict()
    for role, overwrite in channel.overwrites.items():
        permissions[f"{type(role)}/{role.id}"] = overwrite._values

    channel_settings = db_sess.query(ChannelSettings).filter_by(
        user_id=user_id,
        server_id=guild_id
    ).first()
    if not channel_settings:
        channel_settings = ChannelSettings(
            user_id=user_id,
            server_id=guild_id
        )
    channel_settings.name = channel_name
    channel_settings.permissions = str(permissions)

    db_sess.add(channel_settings)
    db_sess.commit()
