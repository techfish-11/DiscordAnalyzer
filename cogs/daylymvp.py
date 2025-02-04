from datetime import datetime, timedelta

import discord
from discord.ext import commands, tasks

from database import get_db_connection


# cogs/daylymvp.py


class DailyMVPCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.clear_mvp_data.start()

    @tasks.loop(hours=24)
    async def clear_mvp_data(self):
        print("Clearing MVP data.")
        conn = get_db_connection()
        cursor = conn.cursor()
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        cursor.execute("DELETE FROM message_points WHERE date = ?", (yesterday,))
        conn.commit()
        print(f"Deleted MVP data for {yesterday}.")

    @clear_mvp_data.before_loop
    async def before_clear_mvp_data(self):
        await self.bot.wait_until_ready()
        now = datetime.now()
        next_run = now.replace(hour=23, minute=59, second=0, microsecond=0)
        if now >= next_run:
            next_run += timedelta(days=1)
        await discord.utils.sleep_until(next_run)


async def setup(bot: commands.Bot):
    await bot.add_cog(DailyMVPCog(bot))
