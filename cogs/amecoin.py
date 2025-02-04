import os
import sqlite3
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands


DB_FILE = "coin.db"


class AmexCoin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.create_coin_db()

    def create_coin_db(self) -> None:
        """
        Bot起動時にデータベースファイルが存在しない場合は作成
        すでにある場合はテーブル作成はスキップ
        """
        if not os.path.exists(DB_FILE):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("PRAGMA journal_mode = WAL;")
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        balance INTEGER DEFAULT 0,
                        last_login_bonus TEXT
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        from_user INTEGER,
                        to_user INTEGER,
                        amount INTEGER,
                        timestamp TEXT,
                        FOREIGN KEY(from_user) REFERENCES users(user_id),
                        FOREIGN KEY(to_user) REFERENCES users(user_id)
                    )
                """)

    def get_connection(self) -> sqlite3.Connection:
        """
        毎回新しくConnectionを取得するためのヘルパー
        トランザクション管理を手動で行うために isolation_level=None を設定
        busy_timeout を設定して、ロック競合時に多少リトライするようにする
        """
        conn = sqlite3.connect(DB_FILE, isolation_level=None)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 3000;")
        return conn

    @app_commands.command(name="loginbonus", description="2時間ごとに500AmexCoinを受け取れます")
    async def login_bonus(self, interaction: discord.Interaction) -> None:
        """
        2時間毎に500コインをユーザーへ付与
        last_login_bonus列を確認し、2時間経っていない場合はエラーメッセージ
        """
        user_id = interaction.user.id
        now = datetime.now()

        try:
            with self.get_connection() as conn:
                conn.execute("BEGIN EXCLUSIVE")
                cursor = conn.cursor()

                cursor.execute("SELECT balance, last_login_bonus FROM users WHERE user_id = ?", (user_id,))
                row = cursor.fetchone()

                if row:
                    balance, last_bonus_str = row
                    last_bonus = datetime.strptime(last_bonus_str, "%Y-%m-%d %H:%M:%S") if last_bonus_str else None

                    if last_bonus and now - last_bonus < timedelta(hours=2):
                        conn.execute("ROLLBACK")
                        await interaction.response.send_message("ログインボーナスは2時間に1回までです。")
                        return

                    new_balance = balance + 500
                    cursor.execute(
                        "UPDATE users SET balance = ?, last_login_bonus = ? WHERE user_id = ?",
                        (new_balance, now.strftime("%Y-%m-%d %H:%M:%S"), user_id)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO users (user_id, balance, last_login_bonus) VALUES (?, ?, ?)",
                        (user_id, 500, now.strftime("%Y-%m-%d %H:%M:%S"))
                    )

                conn.execute("COMMIT")

            await interaction.response.send_message("🎁 ログインボーナス500AmexCoinを受け取りました！")

        except Exception as e:
            print(f"[ERROR in login_bonus]: {e}")
            await interaction.response.send_message("ログインボーナスの処理中にエラーが発生しました。")

    @app_commands.command(name="pay", description="他のユーザーにAmexCoinを送金します")
    async def pay(self, interaction: discord.Interaction, user: discord.User, amount: int) -> None:
        """
        他ユーザーにコインを送金。
        自分への送金や、残高不足の場合はエラーメッセージ。
        """
        from_user_id = interaction.user.id
        to_user_id = user.id

        if amount <= 0:
            await interaction.response.send_message("送金額は0より大きくなければなりません。")
            return
        elif from_user_id == to_user_id:
            await interaction.response.send_message("自分自身にコインを送金することはできません。")
            return

        now = datetime.now()

        try:
            with self.get_connection() as conn:
                conn.execute("BEGIN EXCLUSIVE")
                cursor = conn.cursor()

                cursor.execute("SELECT balance FROM users WHERE user_id = ?", (from_user_id,))
                row = cursor.fetchone()
                if not row or row[0] < amount:
                    conn.execute("ROLLBACK")
                    await interaction.response.send_message("この取引を完了するのに十分なAmexCoinを持っていません。")
                    return
                from_balance = row[0]

                cursor.execute("SELECT balance FROM users WHERE user_id = ?", (to_user_id,))
                row = cursor.fetchone()
                if not row:
                    cursor.execute("INSERT INTO users (user_id, balance) VALUES (?, ?)", (to_user_id, 0))
                    to_balance = 0
                else:
                    to_balance = row[0]

                new_from_balance = from_balance - amount
                new_to_balance = to_balance + amount

                cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_from_balance, from_user_id))
                cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_to_balance, to_user_id))

                cursor.execute(
                    "INSERT INTO transactions (from_user, to_user, amount, timestamp) VALUES (?, ?, ?, ?)",
                    (from_user_id, to_user_id, amount, now.strftime("%Y-%m-%d %H:%M:%S"))
                )

                conn.execute("COMMIT")

            await interaction.response.send_message(f"{user.mention} に {amount} AmexCoinを送金しました！")

        except Exception as e:
            print(f"[ERROR in pay]: {e}")
            await interaction.response.send_message("送金処理中にエラーが発生しました。")

    @app_commands.command(name="admincoin", description="管理者専用コマンド。全員に500AmexCoinを配布します。")
    async def admin_coin(self, interaction: discord.Interaction, command: str):
        admin_user_id = 1241397634095120438
        if interaction.user.id != admin_user_id:
            await interaction.response.send_message("このコマンドを実行する権限がありません。")
            return
        elif command != "all500":
            await interaction.response.send_message("無効なコマンドです。")
            return

        conn = sqlite3.connect("coin.db")
        cursor = conn.cursor()

        cursor.execute("SELECT user_id, balance FROM users")
        users = cursor.fetchall()

        for user_id, balance in users:
            new_balance = balance + 500
            cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))

        conn.commit()
        await interaction.response.send_message("全員に500AmexCoinを配布しました！")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AmexCoin(bot))
