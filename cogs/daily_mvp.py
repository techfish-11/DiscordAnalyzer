# cogs/daily_mvp.py
import discord
from discord.ext import commands, tasks
from datetime import datetime, time, timedelta
import pytz
import sqlite3

from database import get_db_connection

# JSTでのMVP発表時間
ANNOUNCEMENT_TIME = time(hour=23, minute=59, tzinfo=pytz.timezone('Asia/Tokyo'))
# 毎日0時にポイントリセット
RESET_TIME = time(hour=0, minute=0, tzinfo=pytz.timezone('Asia/Tokyo'))

class DailyMVPAnnouncement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.daily_mvp_announcement.start()

    def cog_unload(self):
        self.daily_mvp_announcement.cancel()

    @tasks.loop(time=ANNOUNCEMENT_TIME)
    async def daily_mvp_announcement(self):
        """毎日23:59 (JST) にMVPを集計して告知。"""
        conn = get_db_connection()
        cursor = conn.cursor()
        today = datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y-%m-%d')

        cursor.execute('''
            SELECT user_id, SUM(total_points) as daily_points 
            FROM message_points 
            WHERE date = ? 
            GROUP BY user_id 
            ORDER BY daily_points DESC 
            LIMIT 5
        ''', (today,))
        
        rankings = cursor.fetchall()
        
        # 公開するチャンネルID
        ANNOUNCEMENT_CHANNEL_ID = 123456789  # 実際のチャンネルIDを入れてください
        channel = self.bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
        
        if channel and rankings:
            embed = discord.Embed(
                title="🌟 本日のMVP発表 🌟",
                description=f"{today}の活動ランキング",
                color=0xffd700
            )
            
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
            for i, row in enumerate(rankings):
                user_id = row['user_id']
                points = row['daily_points']
                user = channel.guild.get_member(user_id)
                if user:
                    embed.add_field(
                        name=f"{medals[i]} 第{i+1}位",
                        value=f"{user.mention}\n獲得ポイント: {points}点",
                        inline=False
                    )
            
            await channel.send(embed=embed)

    @daily_mvp_announcement.before_loop
    async def before_daily_mvp(self):
        await self.bot.wait_until_ready()

class DailyMVPAnnouncement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_mvp_announcement.is_running()  # タスクがすでに実行中か確認

    async def cog_load(self):
        if not self.daily_mvp_announcement.is_running():
            self.daily_mvp_announcement.start()
    def cog_unload(self):
        self.reset_daily_points.cancel()

    @tasks.loop(time=RESET_TIME)
    async def reset_daily_points(self):
        """毎日0:00 (JST) に前日のポイントをアーカイブ・削除。"""
        try:
            conn = get_db_connection()
            with conn:
                # アーカイブテーブルは既に存在する前提
                yesterday = (datetime.now(pytz.timezone('Asia/Tokyo')) - timedelta(days=1)).strftime('%Y-%m-%d')
                conn.execute('''
                    INSERT INTO message_points_archive
                    SELECT * FROM message_points
                    WHERE date = ?
                ''', (yesterday,))

                conn.execute('DELETE FROM message_points WHERE date = ?', (yesterday,))

            print(f"[{datetime.now()}] Daily points have been reset.")
        except Exception as e:
            print(f"Error resetting daily points: {e}")

    @reset_daily_points.before_loop
    async def before_reset(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(DailyMVPAnnouncement(bot))
    await bot.add_cog(DailyMVPManager(bot))
