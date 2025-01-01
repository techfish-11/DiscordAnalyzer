# cogs/messagegraph.py
import discord
from discord.ext import commands
from database import get_db_connection
import numpy as np
import matplotlib.pyplot as plt
import io
from datetime import datetime, timedelta

class MessageGraphCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='messagegraph')
    async def message_graph(self, ctx):
        """日別メッセージ数の可視化 + 明日分の予測を描画。"""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT date, count FROM message_count ORDER BY date')
        data = cursor.fetchall()

        if not data:
            await ctx.send("まだメッセージが記録されていません。")
            return

        dates = [datetime.strptime(row['date'], '%Y-%m-%d') for row in data]
        counts = [row['count'] for row in data]

        # 予測ロジック（7日EMA or 2点以上なら線形回帰）
        if len(dates) >= 7:
            ema_window = 7
            ema = np.convolve(counts, np.ones(ema_window)/ema_window, mode='valid')
            last_ema = ema[-1]
            predicted_count = int(last_ema)
        elif len(dates) >= 2:
            x = np.array([d.toordinal() for d in dates])
            y = np.array(counts)
            coefs = np.polyfit(x, y, 1)
            poly = np.poly1d(coefs)
            tomorrow = dates[-1] + timedelta(days=1)
            x_tomorrow = tomorrow.toordinal()
            predicted_count = int(poly(x_tomorrow))
        else:
            predicted_count = counts[-1] if counts else 0

        # グラフ描画
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.set_facecolor('#1a1a1a')
        fig.patch.set_facecolor('#1a1a1a')

        ax.plot(dates, counts, marker='o', color='#3498db', linestyle='-', 
                linewidth=2, markersize=4, label='Messages')

        if len(dates) >= 7:
            ema_dates = dates[ema_window-1:]
            ax.plot(ema_dates, ema, color='#f1c40f', linestyle='--', 
                    linewidth=2, label=f'{ema_window}-Day EMA')
            ax.plot(dates[-1] + timedelta(days=1), predicted_count, marker='x', 
                    color='#e74c3c', linestyle='None', markersize=8, 
                    label='Predicted Tomorrow')
        elif len(dates) >= 2:
            tomorrow = dates[-1] + timedelta(days=1)
            ax.plot(tomorrow, predicted_count, marker='x', color='#e74c3c', 
                    linestyle='None', markersize=8, label='Predicted Tomorrow')

        ax.set_facecolor('#f8f9fa')
        ax.grid(True, linestyle='--', alpha=0.7, color='#dcdde1')

        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_ylabel('Message Count', fontsize=12, fontweight='bold')
        ax.set_title("Daily Message Count with Tomorrow's Prediction", fontsize=14, 
                     fontweight='bold', pad=20)

        ax.tick_params(axis='both', labelsize=10)
        plt.xticks(rotation=30, ha='right')

        ax.legend(loc='upper left', frameon=True)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        file = discord.File(buf, filename='message_count.png')

        # 結果メッセージ
        if len(dates) >= 7:
            recent_counts = counts[-ema_window:]
            avg_recent = np.mean(recent_counts)
            std_recent = np.std(recent_counts)
            prediction_text = (
                f"📈 **予測**: 明日のメッセージ数は **{predicted_count}** 件と予想されます。\n"
                f"過去{ema_window}日間の平均: **{avg_recent:.2f}** 件\n"
                f"標準偏差: **{std_recent:.2f}** 件"
            )
        elif len(dates) >= 2:
            x = np.array([d.toordinal() for d in dates])
            y = np.array(counts)
            # 相関をちょっと計算
            r_value = np.corrcoef(x, y)[0,1]
            prediction_text = (
                f"📈 **予測**: 明日のメッセージ数は **{predicted_count}** 件と予想されます。\n"
                f"回帰直線: y ≈ {round(np.polyfit(x, y, 1)[0],2)}x + {round(np.polyfit(x, y, 1)[1],2)}\n"
                f"相関係数 (R): {r_value:.2f}"
            )
        else:
            prediction_text = f"📈 **予測**: 明日のメッセージ数は **{predicted_count}** 件と予想されます。"

        await ctx.send("📊 **日別メッセージ数のグラフ**\n" + prediction_text, file=file)
        plt.close()
        buf.close()

async def setup(bot: commands.Bot):
    await bot.add_cog(MessageGraphCog(bot))
