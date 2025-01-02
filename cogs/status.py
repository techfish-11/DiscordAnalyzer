import discord
from discord.ext import commands

class StatusCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name='status', description='Botのステータスを表示します。')
    async def status(self, ctx: discord.Interaction) -> None:
        await ctx.response.send_message("Bot Statusはこちら: https://status.sakana11.org")

async def setup(bot: commands.Bot):
    await bot.add_cog(StatusCog(bot))