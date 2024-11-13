from html.parser import HTMLParser
from time import sleep

import discord
import requests
import schedule
from discord import TextChannel
from discord.ext import commands


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
