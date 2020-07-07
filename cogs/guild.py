import typing
from datetime import datetime, timedelta

import discord
from discord.ext import commands


class guild(commands.Cog):
    """Guild commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief="Guild top Exp")
    async def top(self, ctx, guildname, timeframe: typing.Optional[str] = "0"):
        """
        Displays the guild's top Exp earners. You can view top exp from any day in the past week, the entire week, or average per day.
        Usage: `>top (guild name, Defy or Pace) [optional timeframe]`

        Running the command without any timeframe will show the current top GEXP leaderboard.

        **Options for the timeframe:**
        - `week` - displays the leaderboard for GEXP earned in the entire last week
        - `average` - displays the leaderboard for average GEXP earned per day
        - days ago, a number from `1`-`6` - displays the GEXP leaderboard for the specified day
        """

        titles = {
            "week": " top GEXP earned over the entire week",
            "average": " average GEXP earned per day"
        }

        guild_data = await self.bot.db[guildname.lower()].find_one({})

        if guild_data is None:
            return await ctx.send("Please specify a guild- either Defy or Pace.")

        try:
            d = datetime.now(tz=self.bot.est) - timedelta(days=int(timeframe))
            timeframe = d.strftime("%Y-%m-%d")
            dispday = d.strftime("%m/%d/%Y")
        except Exception:
            dispday = "ERROR"

        topdata = guild_data['top'][timeframe]

        desc = ""

        x = 0
        for player in topdata:
            x += 1
            desc += str(x) + ") "
            desc += "*" + player['player']

            discordid = player.get('discord')
            try:
                if discordid:
                    member = ctx.guild.get_member(int(discordid))
                    desc += " (" + member.mention + ")"
            except AttributeError:
                pass

            desc += "* - **"
            desc += str(round(player['xp']))
            desc += "** Guild EXP\n"

        embed = discord.Embed(timestamp=datetime.now(tz=self.bot.est), description=desc)
        embed.set_author(name=titles.get(timeframe, guildname + " top EXP for " + dispday),
                         icon_url="https://i.imgur.com/GMm53sH.png")
        await ctx.send(embed=embed)

    @commands.command(brief="Guild total Exp earned (past week)")
    async def total(self, ctx, guildname):
        """
        Displays the guild's overall xp earned over the last week.
        Usage: `>total (guild name, Defy or Pace)`
        """

        guild_data = await self.bot.db[guildname.lower()].find_one({})

        if guild_data is None:
            return await ctx.send("Please specify a guild- either Defy or Pace.")

        display_timeframes = ['All-time', 'Total week', 'Average per day']
        timeframes = ['all', 'week', 'average']
        for x in range(7):
            d = (datetime.now(tz=self.bot.est) - timedelta(days=x))
            timeframes.append(d.strftime("%Y-%m-%d"))
            display_timeframes.append(d.strftime("%m/%d/%Y"))

        totals = guild_data['total']

        desc = ""

        for x in range(len(timeframes)):
            desc += display_timeframes[x] + ' - **' + str(totals[timeframes[x]]) + "** Guild Exp"

        embed = discord.Embed(timestamp=datetime.now(tz=self.bot.est), description=desc)
        embed.set_author(name=guildname + "total Guild Exp earned",
                         icon_url="https://i.imgur.com/GMm53sH.png")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(guild(bot))
