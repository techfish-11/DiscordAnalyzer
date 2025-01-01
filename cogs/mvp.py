# cogs/mvp.py
import discord
from discord.ext import commands
from database import get_db_connection
from datetime import datetime

class MVPCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='mvp')
    async def show_mvp(self, ctx):
        """当日の上位5ユーザーを表示。"""
        conn = get_db_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT user_id, total_points,
                   text_count, link_count, media_count, reply_count
            FROM message_points 
            WHERE date = ? 
            ORDER BY total_points DESC 
            LIMIT 5
        ''', (today,))
        
        rankings = cursor.fetchall()
        if not rankings:
            await ctx.send("本日のアクティビティはまだありません。")
            return

        embed = discord.Embed(
            title="🏆 Today's MVP Ranking",
            description=f"Date: {today}",
            color=0xffd700
        )

        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for i, row in enumerate(rankings):
            user_id = row['user_id']
            total_points = row['total_points']
            text = row['text_count']
            link = row['link_count']
            media = row['media_count']
            reply = row['reply_count']

            user = ctx.guild.get_member(user_id)
            if user:
                details = (
                    f"**Points**: {total_points}\n"
                    f"Text: {text} | Links: {link}\n"
                    f"Media: {media} | Replies: {reply}"
                )
                embed.add_field(
                    name=f"{medals[i]} Rank {i+1} - {user.display_name}",
                    value=details,
                    inline=False
                )

        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(MVPCog(bot))
