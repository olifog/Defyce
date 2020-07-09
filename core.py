import asyncio
import json
import logging
import os
import traceback
from datetime import datetime
from urllib import parse

import discord
import motor.motor_asyncio
from discord.ext import commands, tasks
from pytz import timezone

from extras.hypixel import HypixelAPI, PlayerNotFoundException
from extras.requesthandler import RequestHandler

logging.basicConfig(
    format="[%(asctime)s] [%(levelname)s:%(name)s] %(message)s", level=logging.INFO
)


class Defyce(commands.Bot):

    def __init__(self):
        super().__init__(
            command_prefix=[">"],
            case_insensitive=True,
            reconnect=True
        )

        with open('./data/settings.json') as settings:
            self.settings = json.load(settings)
            settings.close()

        uri = "mongodb://bot:" + parse.quote_plus(self.settings['bot_motor_password']) + "@51.81.32.153:27017/admin"
        self.motor_client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self.motor_client.defyce
        self.handler = RequestHandler(asyncio.get_event_loop())
        self.hypixelapi = HypixelAPI(self.settings['bot_api_key'], self.handler)
        self.logger = logging.getLogger(__name__)
        self.est = timezone("US/Eastern")

        self.owner = 404244659024429056
        self.guild = None
        self.uptime = datetime.now()

        self.theme = discord.Colour(16711680)

    async def on_message(self, message):
        if message.author.bot:
            return

        ctx = await self.get_context(message)
        await self.invoke(ctx)

    async def on_ready(self):
        self.remove_command('help')
        if not self.cogs:
            await self.load_mods()

        self.logger.info("Bot ready")

        self.guild = self.get_guild(637032923505098765)

        watch = discord.Activity(type=discord.ActivityType.watching, name=">help | Defyce")
        await self.change_presence(status=discord.Status.idle, activity=watch)

    async def load_mods(self):
        for ext in os.listdir('cogs'):
            try:
                if not ext.endswith(".py"):
                    continue
                self.load_extension(f"cogs.{ext.replace('.py', '')}")
                self.logger.info(f"Loaded {ext}")
            except:
                self.logger.critical(f"{ext} failed:\n{traceback.format_exc()}")

    async def get_pic(self, url, filename='picture.png'):
        async with self.session.get(url) as rsp:
            init_bytes = await rsp.read()
        return discord.File(BytesIO(init_bytes), filename=filename)

    def run(self):
        super().run(self.settings['discord_token'])


Defyce().run()
