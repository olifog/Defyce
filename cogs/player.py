import asyncio
import base64
import datetime

from extras.hypixel import PlayerNotFoundException, HypixelAPIError
from discord.ext import commands


class player(commands.Cog):
    """Player commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief="Verifying your account")
    async def verify(self, ctx, ign):
        """
        This command verifies your Minecraft account with your Discord account, so that you can use the rest of the bot's features.
        Usage: `>verify [mc username]`
        """
        pdata = await self.bot.db.verified.find_one({'discordid': ctx.author.id})

        if pdata is not None:
            await ctx.send("You're already verified as `" + pdata['displayname'] +
                           "`! Use `>unverify` to unverify.")
            return

        # Check for illegal characters
        allowed_chars = "abcdefghijklmnopqrstuvwxyz"
        allowed_chars += allowed_chars.upper()

        target = str(ctx.author)
        for char in ctx.author.name:
            if char not in allowed_chars:
                target = (base64.b64encode(str(ctx.author).encode()).decode('utf-8')[:5] + '#1234').strip('+/=-')
                break

        try:
            player = await self.bot.hypixelapi.getPlayer(name=ign)
        except PlayerNotFoundException:
            return await ctx.send("Can't find that MC ign on Hypixel!")

        try:
            guild = await self.bot.hypixelapi.getGuild(player=player.UUID)
            if guild.JSON['name'] not in ['Defy', 'Pace']:
                raise HypixelAPIError
        except HypixelAPIError:
            return await ctx.send("You must be in either Defy or Pace to verify!")

        try:
            daccount = player.JSON['socialMedia']['links']['DISCORD']
        except KeyError:  # They have no linked Discord account
            daccount = None

        if daccount == target or daccount == str(ctx.author):
            member = {'discordid': ctx.author.id, 'displayname': ign, 'uuid': player.UUID, 'online': False, 'remove': False}

            await self.bot.db.verified.insert_one(member)
            return await ctx.send(f"**{ctx.author.mention} Verified as {ign}!**")

        vmessage = "> Please follow the steps below to verify your MC account!"
        vmessage += "\n\n**How to verify:**\n\t*- Connect to* `mc.hypixel.net`"
        vmessage += "\n\t*- Go into your profile (right click on your head)"
        vmessage += "\n\t- Click on \'Social Media\', the Twitter logo"
        vmessage += "\n\t- Click on the Discord logo"
        vmessage += f"\n\t- Copy and paste* `{target}` *into chat"
        vmessage += f"\n\t- Come back to Discord and run* `{ctx.prefix + ctx.command.qualified_name} {ign}` *again!*"

        await ctx.send(vmessage)

    @commands.command(brief="Unverify")
    async def unverify(self, ctx):
        """
        Unverifies your account on the bot. You can always verify again with `>verify`.
        Usage: `>unverify`
        """
        msg = await ctx.send("*Finding user...*")
        player = await self.bot.db.verified.find_one({'discordid': ctx.author.id})

        if player is None:
            await msg.edit(content="**You aren't verified! Verify with `>verify`.**")
            return

        await msg.edit(content=f"*Unverifying your account, `{player['displayname']}`...*")

        await self.bot.db.verified.update_one({'_id': player['_id']}, {'$set': {'remove': True}})
        await msg.edit(content=f"**Unverified your account, `{player['displayname']}`!**")


def setup(bot):
    bot.add_cog(player(bot))
