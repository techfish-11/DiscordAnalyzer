# main.py
import discord
from discord.ext import commands
import asyncio
import os

# 自作モジュール
from config import TOKEN, GUILD_ID
from database import init_db, record_existing_members

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')

    # DB初期化（テーブル作成）
    init_db()

    # サーバー情報を取得
    guild = bot.get_guild(GUILD_ID)
    if guild:
        record_existing_members(guild)
    else:
        print(f"サーバー {GUILD_ID} が見つかりませんでした。")

    # cogsフォルダからCogをロード
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            extension_name = filename[:-3]
            try:
                await bot.load_extension(f'cogs.{extension_name}')
                print(f'Loaded: cogs.{extension_name}')
            except Exception as e:
                print(f'Failed to load: cogs.{extension_name} - {e}')

    # アプリコマンドを同期（slashコマンド等）
    await bot.tree.sync()

if __name__ == '__main__':
    asyncio.run(bot.start(TOKEN))
