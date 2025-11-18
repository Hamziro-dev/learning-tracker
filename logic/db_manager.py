import sqlite3
import os
from datetime import datetime

class DBManager:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        self.db_path = os.path.join(data_dir, "tracker.db")

        self.conn = sqlite3.connect(self.db_path)
        self.create_tables()

    # -------------------------------
    # テーブル作成
    # -------------------------------
    def create_tables(self):
        cur = self.conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject_name TEXT NOT NULL,
                color_code TEXT DEFAULT '#4CAF50',
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject_id INTEGER,
                subject TEXT,
                hours REAL,
                date TEXT,
                note TEXT,
                goal_hours REAL,
                status TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(subject_id) REFERENCES subjects(id)
            )
        """)
        self.conn.commit()

    # -------------------------------
    # ユーザー操作
    # -------------------------------
    def add_user(self, username, password):
        cur = self.conn.cursor()
        cur.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", (username, password))
        self.conn.commit()

    def get_user(self, username, password):
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
        row = cur.fetchone()
        return row[0] if row else None  # ← 型をintで保証する

    # -------------------------------
    # 教科操作
    # -------------------------------
    def add_subject(self, user_id, subject_name, color_code="#4CAF50"):
        cur = self.conn.cursor()
        cur.execute("INSERT INTO subjects (user_id, subject_name, color_code) VALUES (?, ?, ?)",
                    (user_id, subject_name, color_code))
        self.conn.commit()

    def get_subjects(self, user_id):
        cur = self.conn.cursor()
        cur.execute("SELECT id, subject_name, color_code FROM subjects WHERE user_id=?", (user_id,))
        return cur.fetchall()

    # -------------------------------
    # 学習記録操作
    # -------------------------------
    def add_record(self, user_id, subject, hours, date=None, note="", goal_hours=None, status="完了"):
        if not date:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO records (user_id, subject, hours, date, note, goal_hours, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, subject, hours, date, note, goal_hours, status))
        self.conn.commit()

    def get_records(self, user_id):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT subject, hours, date, note, goal_hours, status
            FROM records
            WHERE user_id=?
            ORDER BY date DESC
        """, (user_id,))
        rows = cur.fetchall()
        return [
            {
                "subject": r[0],
                "hours": r[1],
                "date": r[2],
                "note": r[3],
                "goal_hours": r[4],
                "status": r[5],
            }
            for r in rows
        ]

    def summarize_by_date(self, user_id):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT date(date), SUM(hours) FROM records
            WHERE user_id=?
            GROUP BY date(date)
            ORDER BY date(date)
        """, (user_id,))
        return {row[0]: row[1] for row in cur.fetchall()}

