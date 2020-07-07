import discord
from discord.ext import commands, tasks
from datetime import datetime
from extras import checks


class server(commands.Cog):
    """Server commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        wchan = self.bot.guild.get_channel(678440881954619413)

        desc = "Head over to <#678442072755273749> to verify yourself!\n\n"
        desc += "Please follow all our rules at <#672565003420958723>\n"
        desc += "Read the news in <#672565239476256781>"

        embed = discord.Embed(timestamp=datetime.utcnow(), description=desc)
        embed.set_author(name="Welcome to the server!",
                         icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f1/Heart_coraz%C3%B3n.svg/1200px-Heart_coraz%C3%B3n.svg.png")
        embed.set_footer(text="Defyce Guild",
                         icon_url="https://cdn.discordapp.com/attachments/677996730741948431/678268510400544790/Screenshot_2020-02-14_at_19.36.43.png")
        await wchan.send(embed=embed, content="Hi " + member.mention + "!")

        uverified = self.bot.guild.get_role(678446619871543316)
        music = self.bot.guild.get_role(637033089838874664)
        newroles = [self.bot.guild.default_role, uverified, music]
        await member.edit(roles=newroles)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        dbplayer = await self.bot.db.verified.find_one({'discordid': member.id})

        if dbplayer is not None:
            await self.bot.db.verified.delete_many({'_id': dbplayer['_id']})


def setup(bot):
    bot.add_cog(server(bot))
