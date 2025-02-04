# cogs/message_count.py
import sys
import re

from database import record_message_count, get_db_connection

from discord.ext import commands

sys.path.insert(0, "/root/EvexDevelopers-SupportBot")


class MessageCountCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """メッセージを受け取ったときにDBへ記録。"""
        if message.author.bot:
            return

        print(f"Message from {message.author}: {message.content}")

        date_str = message.created_at.strftime("%Y-%m-%d")
        record_message_count(date_str)

        # 詳細メッセージポイント計算
        text_count = 1
        link_count = 1 if re.search(r"http[s]?://", message.content) else 0
        media_count = 1 if len(message.attachments) > 0 else 0
        reply_count = 1 if message.reference else 0

        total_points = (text_count * 10) + (link_count * 4) + \
            (media_count * 3) + (reply_count * 3)

        conn = get_db_connection()
        with conn:
            conn.execute("""
                INSERT INTO message_points 
                (user_id, date, text_count, link_count, media_count, reply_count, total_points)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, date) DO UPDATE SET
                text_count = text_count + ?,
                link_count = link_count + ?,
                media_count = media_count + ?,
                reply_count = reply_count + ?,
                total_points = total_points + ?
            """, (
                message.author.id, date_str, text_count, link_count, media_count, reply_count, total_points,
                text_count, link_count, media_count, reply_count, total_points
            ))

        await self.bot.process_commands(message)


async def setup(bot: commands.Bot):
    await bot.add_cog(MessageCountCog(bot))
