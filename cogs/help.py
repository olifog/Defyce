import typing

import discord
from discord.ext import commands


class help(commands.Cog):
    """Help command"""

    def __init__(self, bot):
        self.bot = bot

    async def get_command_help_embed(self, commandname):  # returns Embed + potential discord.File
        command = self.bot.get_command(commandname)

        if command is None:
            embed = discord.Embed(colour=self.bot.theme, description=f"Sorry, I can't find the command `{commandname}`")
            return embed, None

        title = command.brief
        desc = command.help
        embed = discord.Embed(colour=self.bot.theme, description=desc)
        embed.set_author(name=title, icon_url="https://i.ibb.co/H2cfZ4X/Artboard-1.png")
        return embed, None

    @commands.command()
    async def help(self, ctx, *, command: typing.Optional[str]):
        if command is not None:
            embed, pic = await self.get_command_help_embed(command)
            return await ctx.send(embed=embed, file=pic)

        await ctx.send("Full help command in progress")


def setup(bot):
    bot.add_cog(help(bot))
