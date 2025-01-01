import discord
from discord.ext import commands, tasks
import datetime
import sqlite3
from datetime import datetime, time, timezone, timedelta
import pytz
import re
import io
import numpy as np
import matplotlib.pyplot as plt
import os

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

GUILD_ID = 1255359848644608035
CHANNEL_ID = 1255362057709289493
TARGET_MEMBER_COUNT = 1000

def create_message_count_table():
    conn = sqlite3.connect('members.db')
    with conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS message_count (
                date TEXT PRIMARY KEY,
                count INTEGER
            )
        ''')

def create_mvp_tables():
    conn = sqlite3.connect('members.db')
    with conn:
        # 既存のメッセージカウントテーブル
        conn.execute('''
            CREATE TABLE IF NOT EXISTS message_points (
                user_id INTEGER,
                date TEXT,
                text_count INTEGER DEFAULT 0,
                link_count INTEGER DEFAULT 0,
                media_count INTEGER DEFAULT 0,
                reply_count INTEGER DEFAULT 0,
                total_points INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, date)
            )
        ''')


def calculate_daily_mvp():
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    
    # メッセージの種類ごとの点数を定義
    POINT_SYSTEM = {
        'text': 10,      # テキストメッセージ
        'link': 4,       # リンク
        'media': 3,      # 画像/動画
        'reply': 3       # 返信
    }
    
    # ユーザーごとの点数を集計するクエリ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS message_points (
            user_id INTEGER,
            date TEXT,
            text_count INTEGER DEFAULT 0,
            link_count INTEGER DEFAULT 0,
            media_count INTEGER DEFAULT 0,
            reply_count INTEGER DEFAULT 0,
            total_points INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, date)
        )
    ''')

def record_message_count(date):
    conn = get_db_connection()
    with conn:
        conn.execute('''
            INSERT INTO message_count (date, count) 
            VALUES (?, 1)
            ON CONFLICT(date) 
            DO UPDATE SET count = count + 1
        ''', (date,))

def get_db_connection():
    conn = sqlite3.connect('members.db')
    conn.row_factory = sqlite3.Row
    return conn

def record_member_join(member_id, join_date):
    conn = get_db_connection()
    with conn:
        conn.execute('INSERT OR IGNORE INTO members (member_id, join_date) VALUES (?, ?)',
                     (member_id, join_date))

async def record_existing_members(guild):
    conn = get_db_connection()
    for member in guild.members:
        join_date = member.joined_at.strftime('%Y-%m-%d %H:%M:%S')
        record_member_join(member.id, join_date)

def calculate_growth_rate():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT member_id, join_date FROM members')
    members = cursor.fetchall()

    if len(members) < 2:
        return None

    first_member = members[0]
    last_member = members[-1]

    first_join_date = datetime.strptime(first_member['join_date'], '%Y-%m-%d %H:%M:%S')
    last_join_date = datetime.strptime(last_member['join_date'], '%Y-%m-%d %H:%M:%S')

    total_members = len(members)
    total_days = (last_join_date - first_join_date).days

    if total_days > 0:
        growth_rate = (total_members - 1) / total_days
    else:
        growth_rate = 0

    return growth_rate, total_members, total_days

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')
    create_message_count_table()
    create_mvp_tables()
    guild = bot.get_guild(GUILD_ID)
    
    if guild is not None:
        conn = get_db_connection()
        with conn:
            conn.execute('DELETE FROM members')
        await record_existing_members(guild)
    else:
        print(f"サーバー {GUILD_ID} が見つかりませんでした。")

    # Load cogs from the /cogs folder
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
    
    # Sync commands
    await bot.tree.sync()

@bot.event
async def on_member_join(member):
    guild = bot.get_guild(GUILD_ID)
    channel = guild.get_channel(CHANNEL_ID)

    if guild is not None and channel is not None:
        remaining_members = TARGET_MEMBER_COUNT - len(guild.members)
        await channel.send(f"ようこそ {member.mention} さん！現在のメンバー数: {len(guild.members)}人。\n"
                           f"あと {remaining_members} 人で {TARGET_MEMBER_COUNT}人達成です！")

    join_date = member.joined_at.strftime('%Y-%m-%d %H:%M:%S')
    record_member_join(member.id, join_date)

    if len(guild.members) >= TARGET_MEMBER_COUNT:
        await celebrate_1000_members(guild, channel)

async def celebrate_1000_members(guild, channel):
    await channel.send(f"🎉🎉🎉 {TARGET_MEMBER_COUNT}人達成！🎉🎉🎉\n"
                       f"{guild.name}のメンバーが{TARGET_MEMBER_COUNT}人になりました！皆さんありがとうございます！")

@bot.command(name='1000')
async def member_count(ctx):
    guild = ctx.guild
    if guild is not None:
        remaining_members = TARGET_MEMBER_COUNT - len(guild.members)
        await ctx.send(f"現在のメンバー数: {len(guild.members)}人。\n"
                       f"あと {remaining_members} 人で {TARGET_MEMBER_COUNT}人達成です！")
    else:
        await ctx.send("このコマンドはサーバー内でのみ使用できます。")

@bot.command(name='progress')
async def progress(ctx):
    guild = ctx.guild
    if guild is not None:
        current_member_count = len(guild.members)
        progress_percentage = (current_member_count / TARGET_MEMBER_COUNT) * 100
        await ctx.send(f"{TARGET_MEMBER_COUNT}人達成までの現在の進捗率: {progress_percentage:.2f}%")
    else:
        await ctx.send("このコマンドはサーバー内でのみ使用できます。")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    date = message.created_at.strftime('%Y-%m-%d')
    
    # Record basic message count
    record_message_count(date)
    
    # Initialize counts
    text_count = 1  # Base text message
    link_count = 0
    media_count = 0
    reply_count = 0
    
    # Check for links
    if re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message.content):
        link_count = 1
    
    # Check for media attachments
    if len(message.attachments) > 0:
        media_count = 1
    
    # Check for replies
    if message.reference:
        reply_count = 1

    # Calculate total points
    total_points = (text_count * 10) + (link_count * 4) + (media_count * 3) + (reply_count * 3)

    # Update database with detailed counts
    conn = get_db_connection()
    with conn:
        conn.execute('''
            INSERT INTO message_points 
            (user_id, date, text_count, link_count, media_count, reply_count, total_points)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, date) DO UPDATE SET
            text_count = text_count + ?,
            link_count = link_count + ?,
            media_count = media_count + ?,
            reply_count = reply_count + ?,
            total_points = total_points + ?
        ''', (message.author.id, date, text_count, link_count, media_count, reply_count, total_points,
              text_count, link_count, media_count, reply_count, total_points))

    await bot.process_commands(message)

@bot.command(name='growth')
async def growth(ctx):
    import numpy as np
    from scipy import stats
    from sklearn.metrics import r2_score
    
    growth_rate, total_members, total_days = calculate_growth_rate()
    if growth_rate is None:
        await ctx.send("メンバーの増加率を計算するのに十分なデータがありません。")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT join_date FROM members ORDER BY join_date')
    join_dates = cursor.fetchall()

    # データの準備とクリーニング
    dates = [datetime.strptime(member['join_date'], '%Y-%m-%d %H:%M:%S') for member in join_dates]
    counts = list(range(1, len(dates) + 1))
    
    # 時系列データの数値変換
    dates_numeric = np.array([d.timestamp() for d in dates])  # Unix timestamp for better precision
    counts_array = np.array(counts)
    
    # 高度な回帰分析
    # 1. 線形回帰
    slope, intercept, r_value, p_value, std_err = stats.linregress(dates_numeric, counts_array)
    linear_pred = slope * dates_numeric + intercept
    
    # 2. 多項式回帰 (3次)
    poly_coefs = np.polyfit(dates_numeric, counts_array, 3)
    poly = np.poly1d(poly_coefs)
    poly_pred = poly(dates_numeric)
    
    # モデル評価
    linear_r2 = r2_score(counts_array, linear_pred)
    poly_r2 = r2_score(counts_array, poly_pred)
    
    # より良いモデルを選択
    better_model = 'polynomial' if poly_r2 > linear_r2 else 'linear'
    
    # 成長予測
    future_days = np.linspace(dates_numeric[-1], 
                            dates_numeric[-1] + 30*24*3600, 100)  # 30日先まで予測
    
    if better_model == 'polynomial':
        future_growth = poly(future_days)
        target_idx = np.where(future_growth >= TARGET_MEMBER_COUNT)[0]
    else:
        future_growth = slope * future_days + intercept
        target_idx = np.where(future_growth >= TARGET_MEMBER_COUNT)[0]
    
    # 目標達成日の推定
    if len(target_idx) > 0:
        target_timestamp = future_days[target_idx[0]]
        future_date_estimate = datetime.fromtimestamp(target_timestamp)
    else:
        future_date_estimate = None

    # グラフ作成
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_facecolor('#1a1a1a')
    fig.patch.set_facecolor('#1a1a1a')
    
    # 実データのプロット
    ax.plot(dates, counts, 'o', color='#2ecc71', markersize=4, label='Actual Members')
    
    # 予測線のプロット
    future_dates = [datetime.fromtimestamp(ts) for ts in future_days]
    if better_model == 'polynomial':
        ax.plot(future_dates, future_growth, '--', color='#9b59b6', 
                linewidth=2, label=f'Prediction (R² = {poly_r2:.3f})')
    else:
        ax.plot(future_dates, future_growth, '--', color='#9b59b6', 
                linewidth=2, label=f'Prediction (R² = {linear_r2:.3f})')
    
    # 信頼区間の計算と表示
    if better_model == 'linear':
        confidence = 0.95
        n = len(dates_numeric)
        std_error = np.sqrt(np.sum((counts_array - linear_pred) ** 2) / (n - 2))
        pi = t.ppf((1 + confidence) / 2, n - 2)
        
        prediction_interval = pi * std_error * np.sqrt(1 + 1/n + 
            (future_days - np.mean(dates_numeric))**2 / 
            np.sum((dates_numeric - np.mean(dates_numeric))**2))
        
        ax.fill_between(future_dates, 
                       future_growth - prediction_interval,
                       future_growth + prediction_interval,
                       color='#9b59b6', alpha=0.2, label='95% Prediction Interval')
    
    ax.set_facecolor('#f8f9fa')
    ax.grid(True, linestyle='--', alpha=0.7, color='#dcdde1')
    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax.set_ylabel('Member Count', fontsize=12, fontweight='bold')
    ax.set_title('Server Growth Projection', fontsize=14, fontweight='bold', pad=20)
    
    plt.xticks(rotation=30, ha='right')
    ax.axhline(y=TARGET_MEMBER_COUNT, color='#e74c3c', linestyle='--', 
               label=f'Target: {TARGET_MEMBER_COUNT}')
    ax.legend(loc='upper left', frameon=True)
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    file = discord.File(buf, filename='growth.png')

    # 過去30日の成長率計算を修正
    today = datetime.now()
    thirty_days_ago = today - timedelta(days=30)
    
    # 30日前と現在のメンバー数を取得
    cursor.execute('''
        SELECT COUNT(*) 
        FROM members 
        WHERE datetime(join_date) <= datetime(?)
    ''', (thirty_days_ago.strftime('%Y-%m-%d %H:%M:%S'),))
    members_30_days_ago = cursor.fetchone()[0]
    
    # 過去30日間の増加数を計算
    recent_members = total_members - members_30_days_ago
    recent_growth_rate = recent_members / 30.0
    
    # モデルの信頼度を計算
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

@bot.command(name='messagegraph')
async def message_graph(ctx):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT date, count FROM message_count ORDER BY date')
    data = cursor.fetchall()

    dates = [datetime.strptime(row['date'], '%Y-%m-%d') for row in data]
    counts = [row['count'] for row in data]

    # Enhanced prediction using exponential moving average for better accuracy
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
        ax.plot(dates[-1] + timedelta(days=1), predicted_count, marker='x', color='#e74c3c', 
                linestyle='None', markersize=8, label='Predicted Tomorrow')
    elif len(dates) >= 2:
        tomorrow = dates[-1] + timedelta(days=1)
        ax.plot(tomorrow, predicted_count, marker='x', color='#e74c3c', 
                linestyle='None', markersize=8, label='Predicted Tomorrow')

    ax.set_facecolor('#f8f9fa')
    ax.grid(True, linestyle='--', alpha=0.7, color='#dcdde1')

    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax.set_ylabel('Message Count', fontsize=12, fontweight='bold')
    ax.set_title('Daily Message Count with Tomorrow\'s Prediction', fontsize=14, 
                 fontweight='bold', pad=20)

    ax.tick_params(axis='both', labelsize=10)
    plt.xticks(rotation=30, ha='right')

    ax.legend(loc='upper left', frameon=True)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    file = discord.File(buf, filename='message_count.png')

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
        slope, intercept = np.polyfit(x, y, 1)
        r_value = np.corrcoef(x, y)[0,1]
        prediction_text = (
            f"📈 **予測**: 明日のメッセージ数は **{predicted_count}** 件と予想されます。\n"
            f"回帰直線: y = {slope:.2f}x + {intercept:.2f}\n"
            f"相関係数 (R): {r_value:.2f}"
        )
    else:
        prediction_text = f"📈 **予測**: 明日のメッセージ数は **{predicted_count}** 件と予想されます。"

    await ctx.send("📊 **日別メッセージ数のグラフ**\n" + prediction_text, file=file)
    plt.close()
    buf.close()

@bot.command(name='mvp')
async def show_mvp(ctx):
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
    for i, (user_id, total_points, text, link, media, reply) in enumerate(rankings):
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


# MVP発表用の時間設定 (JST 23:55)
ANNOUNCEMENT_TIME = time(hour=23, minute=59, tzinfo=pytz.timezone('Asia/Tokyo'))

class DailyMVPAnnouncement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.daily_mvp_announcement.start()

    def cog_unload(self):
        self.daily_mvp_announcement.cancel()

    @tasks.loop(time=ANNOUNCEMENT_TIME)
    async def daily_mvp_announcement(self):
        # MVPの計算
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
        
        # 発表用チャンネルの取得（チャンネルIDは適切に設定してください）
        ANNOUNCEMENT_CHANNEL_ID = 123456789  # ここに実際のチャンネルIDを設定
        channel = self.bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
        
        if channel and rankings:
            embed = discord.Embed(
                title="🌟 本日のMVP発表 🌟",
                description=f"{today}の活動ランキング",
                color=0xffd700
            )
            
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
            for i, (user_id, points) in enumerate(rankings):
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

class DailyMVPManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.reset_daily_points.start()

    def cog_unload(self):
        self.reset_daily_points.cancel()

    @tasks.loop(time=time(hour=0, minute=0, tzinfo=pytz.timezone('Asia/Tokyo')))
    async def reset_daily_points(self):
        try:
            conn = sqlite3.connect('members.db')
            with conn:
                # 前日のデータをアーカイブテーブルに保存（オプション）
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS message_points_archive
                    AS SELECT * FROM message_points WHERE 0
                ''')
                
                yesterday = (datetime.now(pytz.timezone('Asia/Tokyo')) - timedelta(days=1)).strftime('%Y-%m-%d')
                conn.execute('''
                    INSERT INTO message_points_archive
                    SELECT * FROM message_points
                    WHERE date = ?
                ''', (yesterday,))

                # 前日のデータを削除
                conn.execute('DELETE FROM message_points WHERE date = ?', (yesterday,))

            print(f"[{datetime.now()}] Daily points have been reset.")
        except Exception as e:
            print(f"Error resetting daily points: {e}")

    @reset_daily_points.before_loop
    async def before_reset(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(DailyMVPAnnouncement(bot))
    await bot.add_cog(DailyMVPManager(bot))

if __name__ == '__main__':
    import asyncio
    asyncio.run(setup(bot))
    bot.run('token')
