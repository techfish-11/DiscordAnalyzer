# main.py
import discord
from discord.ext import commands
import os
import asyncio

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

    # # cogsフォルダからCogをロード
    # for filename in os.listdir('./cogs'):
    #     if filename.endswith('.py'):
    #         extension_name = filename[:-3]
    #         try:
    #             await bot(f'cogs.{extension_name}')
    #             print(f'Loaded: cogs.{extension_name}')
    #         except Exception as e:
    #             print(f'Failed to load: cogs.{extension_name} - {e}')

    try:
        from cogs.member_welcome import MemberWelcomeCog
        from cogs.mvp import MVPCog
        from cogs.message_count import MessageCountCog
        from cogs.growth import GrowthCog
        from cogs.messagegraph import MessageGraphCog
        from cogs.daily_mvp import DailyMVPAnnouncement, DailyMVPManager

        # それぞれのCogを追加
        await bot.add_cog(MemberWelcomeCog(bot))
        print("Added: MemberWelcomeCog")

        await bot.add_cog(MVPCog(bot))
        print("Added: MVPCog")

        await bot.add_cog(MessageCountCog(bot))
        print("Added: MessageCountCog")

        await bot.add_cog(GrowthCog(bot))
        print("Added: GrowthCog")

        await bot.add_cog(MessageGraphCog(bot))
        print("Added: MessageGraphCog")

        await bot.add_cog(DailyMVPAnnouncement(bot))
        print("Added: DailyMVPAnnouncement")
        
        await bot.add_cog(DailyMVPManager(bot))
        print("Added: DailyMVPManager")

    except Exception as e:
        print(f"Error loading Cogs: {e}")


    # アプリコマンドを同期（slashコマンド等）
    await bot.tree.sync()

if __name__ == '__main__':
    asyncio.run(bot.start(TOKEN))
