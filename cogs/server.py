import discord
from discord.ext import commands, tasks
from datetime import datetime
from extras import checks


class server(commands.Cog):
    """Server commands"""

    def __init__(self, bot):
        self.bot = bot
        self.queue = []

        self.guildroles = {"Officer": 637490030834745355,
                           "Veteran": 729696584744435823,
                           "Elite": 637490560726204417,
                           "Member": 678462346577969202}

        self.verified = 637033088328663057
        self.guest = 678446619871543316

        self.hypixelroles = {"MVP++": 712315223070998564,
                             "MVP+": 712315207719845949,
                             "MVP": 712315188694745148,
                             "VIP+": 712315169954463796,
                             "VIP": 712315157719810118}

        self.applicables = [self.guest, self.verified]

        for role in self.guildroles.values():
            self.applicables.append(role)

        for role in self.hypixelroles.values():
            self.applicables.append(role)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        wchan = self.bot.guild.get_channel(728665600683147315)

        desc = "Head over to <#678442072755273749> to verify yourself!\n\n"
        desc += "Please follow all our rules at <#672565003420958723>\n"
        desc += "Read the news in <#672565239476256781>"

        embed = discord.Embed(timestamp=datetime.utcnow(), description=desc)
        embed.set_author(name="Welcome to the server!",
                         icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f1/Heart_coraz%C3%B3n.svg/1200px-Heart_coraz%C3%B3n.svg.png")
        embed.set_footer(text="Defyce Guild",
                         icon_url="https://cdn.discordapp.com/attachments/677996730741948431/678268510400544790/Screenshot_2020-02-14_at_19.36.43.png")
        await wchan.send(embed=embed, content="Hi " + member.mention + "!")

        uverified = self.bot.guild.get_role(self.guest)
        music = self.bot.guild.get_role(637033089838874664)
        newroles = [self.bot.guild.default_role, uverified, music]
        await member.edit(roles=newroles)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        dbplayer = await self.bot.db.verified.find_one({'discordid': member.id})

        if dbplayer is not None:
            await self.bot.db.verified.delete_many({'_id': dbplayer['_id']})

    async def strip_applicables(self, roles):
        ret = []
        for role in roles:
            if role.id not in self.applicables:
                ret.append(role)

        return ret


    @tasks.loop(seconds=1)
    async def update_next_member(self):
        try:
            player = self.queue[0]
        except IndexError:
            cursor = self.bot.db.verified.find({})
            self.queue = await cursor.to_list(length=250)
            return

        duser = self.bot.guild.get_member(player['discordid'])

        newroles = await self.strip_applicables(duser.roles)

        if player['remove'] is True:
            newnick = duser.name
            newroles.append(self.bot.guild.get_role(self.guest))
            await self.bot.db.verified.delete_many({'_id': player['_id']})
        else:
            pdata = await self.bot.hypixelapi.getPlayer(uuid=player['uuid'])

            try:
                online = pdata['lastLogout'] < pdata['lastLogin']
            except KeyError:
                online = False

            await self.bot.db.verified.update_one({'_id': player['_id']}, {"displayname": pdata.getName(), "online": online})

            newnick = pdata.getName() + " [" + str(round(pdata.getLevel(), 2)) + "]"

            try:
                newroles.append(self.bot.guild.get_role(self.hypixelroles[pdata.getRank()]))
            except KeyError:
                pass

            try:
                newroles.append(self.bot.guild.get_role(self.guildroles[pdata.JSON[]]))




def setup(bot):
    bot.add_cog(server(bot))
