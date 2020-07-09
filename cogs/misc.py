from datetime import datetime

import discord
import humanize
from discord.ext import commands


class misc(commands.Cog):
    """Miscellaneous commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief="Bot info")
    async def info(self, ctx):
        """
        Check the bot's ping, latency and info.
        Usage: `>info`
        """
        process_time = round(((datetime.utcnow() - ctx.message.created_at).total_seconds()) * 1000)

        e = discord.Embed(color=self.bot.theme)
        e.add_field(
            name="**Latency:**",
            value=f"{round(self.bot.latency * 1000)}ms"
        )
        e.add_field(
            name="**Process time:**",
            value=f"{process_time}ms",
            inline=False
        )

        uptime = humanize.naturaltime(self.bot.uptime)
        e.add_field(name="Owner:", value="Moose#0064")
        e.add_field(name="Uptime:", value=f"Been up since {uptime}")

        e.set_thumbnail(url=ctx.me.avatar_url)
        await ctx.send(embed=e)

    @commands.command()
    async def load_users_from_hplus(self, ctx):
        hplus = self.bot.motor_client.hypixelPlusDB

        async for player in hplus.players.find({}):
            doc = {"discordid": player['discordid'],
                   "uuid": player['uuid'],
                   "displayname": player['displayname']}
            await self.bot.db.insert_one(doc)

        await ctx.send("Loaded")

    @commands.command()
    async def resetnicks(self, ctx):
        for member in ctx.guild.members:
            try:
                await member.edit(nick=member.name)
            except Exception:
                pass


def setup(bot):
    bot.add_cog(misc(bot))
