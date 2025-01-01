import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
from datetime import datetime, timedelta


class AmexCoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.create_coin_db()

    def create_coin_db(self):
        conn = sqlite3.connect('coin.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            with conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        balance INTEGER DEFAULT 0,
                        last_login_bonus TEXT
                    )
                ''')
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        from_user INTEGER,
                        to_user INTEGER,
                        amount INTEGER,
                        timestamp TEXT,
                        FOREIGN KEY(from_user) REFERENCES users(user_id),
                        FOREIGN KEY(to_user) REFERENCES users(user_id)
                    )
                ''')

    @app_commands.command(name='loginbonus', description='2時間ごとに500AmexCoinを受け取れます')
    async def login_bonus(self, interaction: discord.Interaction):
        user_id = interaction.user.id  # interaction.author ではなく interaction.user を使用
        conn = sqlite3.connect('coin.db')
        cursor = conn.cursor()

        cursor.execute('SELECT balance, last_login_bonus FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()

        now = datetime.now()
        if result:
            last_login_bonus = datetime.strptime(result[1], '%Y-%m-%d %H:%M:%S') if result[1] else None
            if last_login_bonus and now - last_login_bonus < timedelta(hours=2):
                await interaction.response.send_message("ログインボーナスは2時間に1回までです。")
                return
            new_balance = result[0] + 500
            cursor.execute('UPDATE users SET balance = ?, last_login_bonus = ? WHERE user_id = ?',
                          (new_balance, now.strftime('%Y-%m-%d %H:%M:%S'), user_id))
        else:
            cursor.execute('INSERT INTO users (user_id, balance, last_login_bonus) VALUES (?, ?, ?)', 
                          (user_id, 500, now.strftime('%Y-%m-%d %H:%M:%S')))
        
        conn.commit()
        await interaction.response.send_message(f"🎁 ログインボーナス500AmexCoinを受け取りました！")

    @app_commands.command(name='pay', description='他のユーザーにAmexCoinを送金します')
    async def pay(self, interaction: discord.Interaction, user: discord.User, amount: int):
        if amount <= 0:
            await interaction.response.send_message("送金額は0より大きくなければなりません。")
            return

        from_user_id = interaction.user.id
        to_user_id = user.id

        if from_user_id == to_user_id:
            await interaction.response.send_message("自分自身にコインを送金することはできません。")
            return

        conn = sqlite3.connect('coin.db')
        cursor = conn.cursor()

        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (from_user_id,))
        from_user_balance = cursor.fetchone()

        if not from_user_balance or from_user_balance[0] < amount:
            await interaction.response.send_message("この取引を完了するのに十分なAmexCoinを持っていません。")
            return

        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (to_user_id,))
        to_user_balance = cursor.fetchone()

        if not to_user_balance:
            cursor.execute('INSERT INTO users (user_id, balance) VALUES (?, ?)', (to_user_id, 0))
            to_user_balance = (0,)

        new_from_user_balance = from_user_balance[0] - amount
        new_to_user_balance = to_user_balance[0] + amount

        cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_from_user_balance, from_user_id))
        cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_to_user_balance, to_user_id))
        cursor.execute('INSERT INTO transactions (from_user, to_user, amount, timestamp) VALUES (?, ?, ?, ?)',
                       (from_user_id, to_user_id, amount, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        conn.commit()
        await interaction.response.send_message(f"{user.mention} に {amount} AmexCoinを送金しました！")
    
    @app_commands.command(name='admincoin', description='管理者専用コマンド。全員に500AmexCoinを配布します。')
    async def admin_coin(self, interaction: discord.Interaction, command: str):
        admin_user_id = 1283023428730748940
        if interaction.user.id != admin_user_id:
            await interaction.response.send_message("このコマンドを実行する権限がありません。")
            return

        if command != 'all500':
            await interaction.response.send_message("無効なコマンドです。")
            return

        conn = sqlite3.connect('coin.db')
        cursor = conn.cursor()

        cursor.execute('SELECT user_id, balance FROM users')
        users = cursor.fetchall()

        for user_id, balance in users:
            new_balance = balance + 500
            cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, user_id))

        conn.commit()
        await interaction.response.send_message("全員に500AmexCoinを配布しました！")

async def setup(bot):
    await bot.add_cog(AmexCoin(bot))
