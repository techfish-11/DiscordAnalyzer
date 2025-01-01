# cogs/growth.py
import discord
from discord.ext import commands
from datetime import datetime, timedelta
import numpy as np
from scipy import stats
from sklearn.metrics import r2_score
import matplotlib.pyplot as plt
import io

from database import calculate_growth_rate, get_db_connection
from config import TARGET_MEMBER_COUNT

class GrowthCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='growth')
    async def growth_command(self, ctx):
        """サーバーの成長推移を可視化し、予測グラフを表示。"""
        result = calculate_growth_rate()
        if result is None:
            await ctx.send("メンバーの増加率を計算するのに十分なデータがありません。")
            return

        growth_rate, total_members, total_days = result
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT join_date FROM members ORDER BY join_date')
        join_dates = cursor.fetchall()

        # データの準備
        dates = [datetime.strptime(row['join_date'], '%Y-%m-%d %H:%M:%S') for row in join_dates]
        counts = list(range(1, len(dates) + 1))

        # Unix timestamp化
        dates_numeric = np.array([d.timestamp() for d in dates])
        counts_array = np.array(counts)

        # 1) 線形回帰
        slope, intercept, r_value, p_value, std_err = stats.linregress(dates_numeric, counts_array)
        linear_pred = slope * dates_numeric + intercept

        # 2) 多項式回帰 (3次)
        poly_coefs = np.polyfit(dates_numeric, counts_array, 3)
        poly = np.poly1d(poly_coefs)
        poly_pred = poly(dates_numeric)

        linear_r2 = r2_score(counts_array, linear_pred)
        poly_r2 = r2_score(counts_array, poly_pred)
        better_model = 'polynomial' if poly_r2 > linear_r2 else 'linear'

        # 30日先まで予測
        future_days = np.linspace(dates_numeric[-1], dates_numeric[-1] + 30*24*3600, 100)
        if better_model == 'polynomial':
            future_growth = poly(future_days)
            target_idx = np.where(future_growth >= TARGET_MEMBER_COUNT)[0]
        else:
            future_growth = slope * future_days + intercept
            target_idx = np.where(future_growth >= TARGET_MEMBER_COUNT)[0]

        if len(target_idx) > 0:
            target_timestamp = future_days[target_idx[0]]
            future_date_estimate = datetime.fromtimestamp(target_timestamp)
        else:
            future_date_estimate = None

        # グラフ描画
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.set_facecolor('#1a1a1a')
        fig.patch.set_facecolor('#1a1a1a')

        # 実データ
        ax.plot(dates, counts, 'o', color='#2ecc71', markersize=4, label='Actual Members')

        # 予測
        future_dates = [datetime.fromtimestamp(ts) for ts in future_days]
        if better_model == 'polynomial':
            ax.plot(future_dates, future_growth, '--', color='#9b59b6', 
                    linewidth=2, label=f'Prediction (R² = {poly_r2:.3f})')
        else:
            ax.plot(future_dates, future_growth, '--', color='#9b59b6',
                    linewidth=2, label=f'Prediction (R² = {linear_r2:.3f})')

        ax.set_facecolor('#f8f9fa')
        ax.grid(True, linestyle='--', alpha=0.7, color='#dcdde1')
        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_ylabel('Member Count', fontsize=12, fontweight='bold')
        ax.set_title('Server Growth Projection', fontsize=14, fontweight='bold', pad=20)
        ax.axhline(y=TARGET_MEMBER_COUNT, color='#e74c3c', linestyle='--', label=f'Target: {TARGET_MEMBER_COUNT}')
        plt.xticks(rotation=30, ha='right')
        ax.legend(loc='upper left', frameon=True)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        file = discord.File(buf, filename='growth.png')
        
        # 過去30日の増加率など算出
        today = datetime.now()
        thirty_days_ago = today - timedelta(days=30)
        
        cursor.execute('''
            SELECT COUNT(*) 
            FROM members 
            WHERE datetime(join_date) <= datetime(?)
        ''', (thirty_days_ago.strftime('%Y-%m-%d %H:%M:%S'),))
        members_30_days_ago = cursor.fetchone()[0]

        recent_members = total_members - members_30_days_ago
        recent_growth_rate = recent_members / 30.0

        confidence_level = poly_r2 if better_model == 'polynomial' else linear_r2

        growth_message = (
            f"📊 **詳細成長分析レポート**\n"
            f"現在のメンバー数: **{total_members}**人\n"
            f"過去30日の1日あたり平均増加数: **{recent_growth_rate:.2f}**人\n"
            f"予測モデルの信頼度: **{confidence_level:.1%}**\n"
            f"使用モデル: **{better_model}**\n"
            f"目標達成まであと: **{TARGET_MEMBER_COUNT - total_members}**人\n"
        )

        if future_date_estimate:
            days_until = (future_date_estimate - datetime.now()).days
            growth_message += (
                f"予測目標達成日: **{future_date_estimate.strftime('%Y-%m-%d')}**\n"
                f"(約**{days_until}**日後)\n"
            )
        else:
            growth_message += "現在の成長率では目標達成日を予測できません。\n"

        await ctx.send(growth_message, file=file)
        plt.close()
        buf.close()

async def setup(bot: commands.Bot):
    await bot.add_cog(GrowthCog(bot))
