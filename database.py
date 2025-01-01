# database.py
import sqlite3
import os
from datetime import datetime

DB_FILE = 'members.db'

def get_db_connection():
    """SQLiteコネクションを取得する。"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初回起動時に必要なテーブルを作成する。"""
    # すでにDBファイルがあれば作成はスキップ
    need_init = not os.path.exists(DB_FILE)

    conn = get_db_connection()
    with conn:
        if need_init:
            # membersテーブル
            conn.execute('''
                CREATE TABLE IF NOT EXISTS members (
                    member_id INTEGER PRIMARY KEY,
                    join_date TEXT
                )
            ''')

            # 日毎メッセージ数
            conn.execute('''
                CREATE TABLE IF NOT EXISTS message_count (
                    date TEXT PRIMARY KEY,
                    count INTEGER
                )
            ''')

            # 詳細メッセージポイント
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
            
            # アーカイブ用(オプション)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS message_points_archive
                AS SELECT * FROM message_points WHERE 0
            ''')

def record_member_join(member_id: int, join_date: str):
    """メンバー参加データをDBに記録（既存なら無視）。"""
    conn = get_db_connection()
    with conn:
        conn.execute('''
            INSERT OR IGNORE INTO members (member_id, join_date) 
            VALUES (?, ?)
        ''', (member_id, join_date))

def record_existing_members(guild):
    """ギルド内メンバーを一括記録（Bot起動時に呼び出し）。"""
    for member in guild.members:
        join_date = member.joined_at.strftime('%Y-%m-%d %H:%M:%S')
        record_member_join(member.id, join_date)

def record_message_count(date: str):
    """日ごとのメッセージ総数をカウントアップ。"""
    conn = get_db_connection()
    with conn:
        conn.execute('''
            INSERT INTO message_count (date, count) 
            VALUES (?, 1)
            ON CONFLICT(date) 
            DO UPDATE SET count = count + 1
        ''', (date,))

def calculate_growth_rate():
    """
    全メンバーのjoin_dateから、平均増加率などを計算。
    (データが足りない場合はNoneを返す)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT member_id, join_date FROM members ORDER BY join_date')
    members = cursor.fetchall()

    if len(members) < 2:
        return None

    first_join_date = datetime.strptime(members[0]['join_date'], '%Y-%m-%d %H:%M:%S')
    last_join_date = datetime.strptime(members[-1]['join_date'], '%Y-%m-%d %H:%M:%S')

    total_members = len(members)
    total_days = (last_join_date - first_join_date).days

    if total_days > 0:
        growth_rate = (total_members - 1) / total_days
    else:
        growth_rate = 0

    return growth_rate, total_members, total_days
