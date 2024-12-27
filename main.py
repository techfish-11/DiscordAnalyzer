# ---------------------------------------
# Tokenは一番下のコードに貼り付けてください
# 22, 24, 26行目にIDを設定してください
# ---------------------------------------
import discord
from discord.ext import commands
import datetime
import sqlite3
from datetime import datetime
import re
import io
import matplotlib.pyplot as plt

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# 解析したいGuildID
GUILD_ID = 00000000000000
# お知らせを受け取るチャンネルID
CHANNEL_ID = 0000000000
# 目標のメンバー数
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
    guild = bot.get_guild(GUILD_ID)
    
    if guild is not None:
        conn = get_db_connection()
        with conn:
            conn.execute('DELETE FROM members')
        await record_existing_members(guild)
    else:
        print(f"サーバー {GUILD_ID} が見つかりませんでした。")

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

@bot.command(name='helpcommands')
async def help(ctx):
    embed = discord.Embed(title="サポートボット コマンド一覧", color=discord.Color.blue())
    embed.add_field(name="e!1000", value="現在のメンバー数と1000人達成までの残り人数を表示します。", inline=False)
    embed.add_field(name="e!progress", value="1000人達成までの進捗率を表示します。", inline=False)
    embed.add_field(name="<botをメンション>", value="レイテンシを確認します。", inline=False)
    await ctx.send(embed=embed)

@bot.event
async def on_message(message):

    date = message.created_at.strftime('%Y-%m-%d')
    record_message_count(date)

    await bot.process_commands(message)

@bot.command(name='growth')
async def growth(ctx):
    growth_rate, total_members, total_days = calculate_growth_rate()
    if growth_rate is None:
        await ctx.send("メンバーの増加率を計算するのに十分なデータがありません。")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT join_date FROM members ORDER BY join_date')
    join_dates = cursor.fetchall()

    dates = [datetime.strptime(member['join_date'], '%Y-%m-%d %H:%M:%S') for member in join_dates]
    counts = list(range(1, len(dates) + 1))

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_facecolor('#1a1a1a')
    fig.patch.set_facecolor('#1a1a1a')
    
    ax.plot(dates, counts, marker='o', color='#2ecc71', linestyle='-', 
            linewidth=2, markersize=4, label='Members')
    
    ax.set_facecolor('#f8f9fa')
    ax.grid(True, linestyle='--', alpha=0.7, color='#dcdde1')
    
    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax.set_ylabel('Member Count', fontsize=12, fontweight='bold')
    ax.set_title('Server Growth Over Time', fontsize=14, fontweight='bold', pad=20)

    ax.tick_params(axis='both', labelsize=10)
    plt.xticks(rotation=30, ha='right')

    ax.axhline(y=TARGET_MEMBER_COUNT, color='#e74c3c', linestyle='--', 
               label=f'Target: {TARGET_MEMBER_COUNT}')

    ax.legend(loc='upper left', frameon=True)

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    file = discord.File(buf, filename='growth.png')

    daily_growth = (total_members - 1) / total_days if total_days > 0 else 0
    days_to_target = int((TARGET_MEMBER_COUNT - total_members) / daily_growth) if daily_growth > 0 else 0

    growth_message = (
        f"📊 **サーバー成長レポート**\n"
        f"現在のメンバー数: **{total_members}**人\n"
        f"1日あたりの平均増加数: **{daily_growth:.1f}**人\n"
        f"目標達成まであと: **{TARGET_MEMBER_COUNT - total_members}**人\n"
        f"現在のペースで目標達成まで: 約**{days_to_target}**日"
    )

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

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_facecolor('#1a1a1a')
    fig.patch.set_facecolor('#1a1a1a')

    ax.plot(dates, counts, marker='o', color='#3498db', linestyle='-', 
            linewidth=2, markersize=4, label='Messages')

    ax.set_facecolor('#f8f9fa')
    ax.grid(True, linestyle='--', alpha=0.7, color='#dcdde1')

    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax.set_ylabel('Message Count', fontsize=12, fontweight='bold')
    ax.set_title('Daily Message Count', fontsize=14, fontweight='bold', pad=20)

    ax.tick_params(axis='both', labelsize=10)
    plt.xticks(rotation=30, ha='right')

    ax.legend(loc='upper left', frameon=True)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    file = discord.File(buf, filename='message_count.png')

    await ctx.send("📊 **日別メッセージ数のグラフ**", file=file)
    plt.close()
    buf.close()

# Token
bot.run('your_token_here')
