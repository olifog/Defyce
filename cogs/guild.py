import typing
from datetime import datetime, timedelta

import discord
from discord.ext import commands, tasks
import operator
from bisect import bisect


class guild(commands.Cog):
    """Guild commands"""

    def __init__(self, bot):
        self.bot = bot
        self.exprequirements.start()

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

        accessguildname = guildname.lower()
        dispguildname = guildname[0].upper() + guildname[1:].lower()

        titles = {
            "week": " top GEXP earned over the entire week",
            "average": " average GEXP earned per day"
        }

        guild_data = await self.bot.db[accessguildname].find_one({})

        if guild_data is None:
            return await ctx.send("Please specify a guild- either Defy or Pace.")

        try:
            d = datetime.now(tz=self.bot.est) - timedelta(days=int(timeframe))
            timeframe = d.strftime("%Y-%m-%d")
            dispday = d.strftime("%d %b")
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

        embed = discord.Embed(timestamp=datetime.now(tz=self.bot.est), description=desc, title="<:top:730049558327066694> " + dispguildname + titles.get(timeframe, " top EXP for " + dispday))
        await ctx.send(embed=embed)

    @commands.command(brief="Guild total Exp earned (past week)")
    async def total(self, ctx, guildname):
        """
        Displays the guild's overall xp earned over the last week.

        Usage: `>total (guild name, Defy or Pace)`
        """

        accessguildname = guildname.lower()
        dispguildname = guildname[0].upper() + guildname[1:].lower()

        guild_data = await self.bot.db[accessguildname].find_one({})

        if guild_data is None:
            return await ctx.send("Please specify a guild- either Defy or Pace.")

        display_timeframes = ['All-time', 'Total this week', 'Average per day']
        timeframes = ['all', 'week', 'average']
        for x in range(7):
            d = (datetime.now(tz=self.bot.est) - timedelta(days=x))
            timeframes.append(d.strftime("%Y-%m-%d"))
            display_timeframes.append(d.strftime("%d %b"))

        totals = guild_data['total']

        desc = ""

        for x in range(len(timeframes)):
            desc += '*' + display_timeframes[x] + '* - **' + '{:,}'.format(round(totals[timeframes[x]])) + "** Guild Exp\n"

        embed = discord.Embed(timestamp=datetime.now(tz=self.bot.est), description=desc, title="<:top:730049558327066694> " + dispguildname + " total Guild Exp earned")
        await ctx.send(embed=embed)

    @tasks.loop(hours=168)
    async def exprequirements(self):
        await self.guildreqs('Defy')
        await self.guildreqs('Pace')

    async def guildreqs(self, guildname):
        accessguildname = guildname.lower()
        dispguildname = guildname[0].upper() + guildname[1:].lower()
        staff_chat = self.bot.get_channel(728665978682212382)

        guild_data = await self.bot.db[accessguildname].find_one({})

        ranks = ['Kick', 'Member', 'Veteran', 'Elite', 'Officer']
        exempt = ['Guild Master', 'Co Owner']
        reqs = [50000, 150000, 250000, 350000]

        results = []

        for player in guild_data['members']:
            if player['rank'] in exempt:
                continue

            rank = player['rank']

            warranted = bisect(reqs, player['exphistory']['week'])
            try:
                place = ranks.index(rank)
            except ValueError:
                continue

            if warranted == place:
                continue

            out = ""

            if warranted > place:
                out += "`" + player['name'] + "` - **PROMOTION** from *" + player['rank'] + "* to *" + ranks[warranted]
                diff = player['exphistory']['week'] - reqs[place]
                out += "*, above current requirements by **" + str(diff) + "**xp *(" + str(player['exphistory']['week']) + 'xp total)*'
            elif warranted == 0:
                out += "`" + player['name'] + "` - **KICK**, only ***" + str(player['exphistory']['week']) + "**xp* this week."
            else:
                out += "`" + player['name'] + "` - **DEMOTION*** from* " + player['rank'] + " *to* " + ranks[warranted]
                diff = reqs[place] - player['exphistory']['week']
                out += ", below current requirements by **" + str(diff) + "**XP *(" + str(player['exphistory']['week']) + 'XP total)*'

            if datetime.now(tz=self.bot.est) - player['joined'] <= 604800:
                out = "~~" + out + "~~"

            results.append(out)

        await staff_chat.send(dispguildname + " Guild rank checks")

        for x in range((len(results)//25)+1):
            embed = discord.Embed(description='\n'.join(results[x*25:(x+1)*25]))
            await staff_chat.send(embed=embed)


    @exprequirements.before_loop
    async def expreqwaiter(self):
        d = datetime.now(tz=self.bot.est)
        next_monday = d + timedelta(7 - d.weekday())
        sunday_night = next_monday - timedelta(minutes=1)

        await discord.utils.sleep_until(sunday_night)

    @commands.command()
    async def forcereqs(self, ctx, guildname):
        await self.guildreqs(guildname)

    @commands.command(brief="Check players under/above a certain weekly gexp threshold")
    async def check(self, ctx, guildname, operand, threshold, rank: typing.Optional[str] = ""):
        """
        Displays all the users that are above/below the weekly threshold that you give.

        Usage: `>check (guild name, Defy or Pace) (above/below) (threshold) [optional guild rank to isolate]`
        """

        accessguildname = guildname.lower()
        dispguildname = guildname[0].upper() + guildname[1:].lower()

        guild_data = await self.bot.db[accessguildname].find_one({})

        if guild_data is None:
            return await ctx.send("Please specify a guild- either Defy or Pace.")

        if operand.lower() == 'above':
            operand = operator.gt
        else:
            operand = operator.lt

        desc = ""
        count = 0

        for member in guild_data['members']:
            if (rank == "" or rank.lower() == member['rank'].lower()) and operand(member['exphistory']['week'], int(threshold)):
                if datetime.now(tz=self.est) - member['joined'] <= 604800:
                    desc += "~~"

                count += 1
                desc += member['name'] + ", *" + member['rank'] + "* | **" + '{:,}'.format(
                    member['exphistory']['week']) + "** XP ("

                if operand == operator.gt:
                    desc += "+" + str(member['exphistory']['week'] - int(threshold)) + ")"
                else:
                    desc += "-" + str(int(threshold) - member['exphistory']['week']) + ")"

                if datetime.now(tz=self.est) - member['joined'] <= 604800:
                    desc += "~~"

                desc += "\n"

        embed = discord.Embed(timestamp=datetime.now(tz=self.bot.est), description=desc,
                              title=dispguildname + " Exp check")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(guild(bot))
