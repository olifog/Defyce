import asyncio
import base64
from datetime import datetime

from extras.hypixel import PlayerNotFoundException, GuildNotFoundException
from discord.ext import commands
import typing
import humanize
import discord


class player(commands.Cog):
    """Player commands"""

    def __init__(self, bot):
        self.bot = bot

        self.images = {'[MVP++] ': "https://i.imgur.com/piZBayK.png",
                       "[MVP+] ": "https://i.imgur.com/K01LqaX.png",
                       "[MVP] ": "https://i.imgur.com/ErJr6vy.png",
                       "[VIP+] ": "https://i.imgur.com/wOzD3Qd.png",
                       "[VIP] ": "https://i.imgur.com/cRj2FM2.png",
                       "": "https://user-images.githubusercontent.com/49322497/70186527-61601080-16ec-11ea-8e0e-49c0f5e4edde.png"}

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
                raise GuildNotFoundException
        except GuildNotFoundException:
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

    @commands.command()
    async def profile(self, ctx, user: typing.Optional[str]):
        """Profile command"""

        if user is None or user.startswith('@'):
            if user is None:
                user = ctx.author
            else:
                user = ctx.message.mentions[0]

            pdata = await self.bot.db.verified.find_one({'discordid': user.id})

            if pdata is None:
                return await ctx.send("Sorry, user not verified! Use `>profile ign` to see any mc user's profile.")

            user = pdata['displayname']


        player = await self.bot.hypixelapi.getPlayer(name=user)

        rank = player.getRank()

        if rank:
            rank = "[" + rank + "] "
        else:
            rank = ""

        desc = "__**Stats**__\n"
        desc += "*Level:* `" + str(round(player.getLevel(), 2)) + "`\n"
        try:
            desc += "*MC Version:* `" + player.JSON['mcVersionRp'] + '`\n'
        except:
            pass
        desc += "*Karma:* `" + str(player.JSON['karma']) + "`\n"

        try:
            firstlogin = datetime.fromtimestamp(player.JSON['firstLogin'] / 1000.0, tz=self.bot.est)
            desc += "*First Login:* `" + firstlogin.strftime("%m/%d/%Y") + "`\n"
        except:
            pass

        try:
            online = player.JSON['lastLogout'] < player.JSON['lastLogin']
        except:
            online = False

        if online:
            statusimg = "https://i.imgur.com/0LNiVAV.png"
        else:
            statusimg = "https://webkit.org/blog-files/color-gamut/Webkit-logo-P3.png"

        lastlogin = datetime.fromtimestamp(player.JSON['lastLogin'] / 1000.0, tz=self.bot.est)
        ago = datetime.now(tz=self.bot.est) - lastlogin

        desc += "*Last Login:* `" + lastlogin.strftime("%m/%d/%Y") + "` (" + humanize.naturaltime(ago) + ")\n\n"

        embed = discord.Embed(timestamp=datetime.now(tz=self.bot.est), description=desc)
        embed.set_thumbnail(url=self.images[rank])

        full_render = await self.bot.handler.getPic("https://visage.surgeplay.com/full/256/" + player.UUID, 'full.png')
        face_render = await self.bot.handler.getPic("https://visage.surgeplay.com/face/" + player.UUID, 'face.png')

        embed.set_image(url="attachment://full.png")
        embed.set_author(name=rank + player.getName(),
                         url="https://hypixel.net/player/" + player.getName(),
                         icon_url="attachment://face.png")
        embed.set_footer(text="Defyce Guild",
                         icon_url=statusimg)

        await ctx.send(embed=embed, files=[full_render, face_render])


def setup(bot):
    bot.add_cog(player(bot))
