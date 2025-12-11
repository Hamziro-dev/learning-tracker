import sqlite3
import os
import datetime

class DBManager:
    def __init__(self):
        self.conn = None
        self.cursor = None
        
        # パス設定
        base_dir = os.path.dirname(os.path.dirname(__file__))
        self.db_path = os.path.join(base_dir, "app_data.db")

    def connect(self):
        """アプリ起動後（on_start）に呼ばれる接続メソッド"""
        if self.conn is not None:
            return

        try:
            # 接続処理
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # カラム名でアクセス可能にする
            self.cursor = self.conn.cursor()
            
            # テーブル作成
            self.create_tables()
            print(f"[INFO] SQLite Connected: {self.db_path}")
            
        except Exception as e:
            print(f"[ERROR] SQLite Connection Failed: {e}")
            self.conn = None
            self.cursor = None

    def create_tables(self):
        if not self.conn or not self.cursor:
            return
        """必要なテーブルを全て作成する"""

        # 学習ログテーブル (ストップウォッチ用 & 手動記録用)
        # started_at, ended_at は文字列で保存
        # hours は手動入力用（ストップウォッチの場合は計算で出すが、今回は共存させる）
        sql_logs = """
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_name TEXT,
            started_at TEXT,
            ended_at TEXT,
            hours REAL,
            date TEXT
        );
        """
        self.cursor.execute(sql_logs)
        self.conn.commit()

    # -------------------------
    # 記録管理（手動）
    # -------------------------
    def add_record(self, subject, hours):
        if not self.conn or not self.cursor:
            return
        """手動で時間を記録する"""
        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        sql = "INSERT INTO logs (subject_name, hours, date) VALUES (?, ?, ?)"
        self.cursor.execute(sql, (subject, hours, now_str))
        self.conn.commit()

    def get_records(self):
        if not self.conn or not self.cursor:
            return []
        
        sql = "SELECT * FROM logs ORDER BY id DESC"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        
        results = []
        for row in rows:
            display_date = row["date"] if row["date"] else row["started_at"]
            
            # 初期化
            duration_str = "00:00:00"
            hours_float = 0.0
            
            # パターンA: 手動入力で hours がある場合
            if row["hours"] is not None:
                hours_float = float(row["hours"])
                duration_str = f"{hours_float}時間"

            # パターンB: ストップウォッチ記録（started_at / ended_at あり）
            elif row["started_at"] and row["ended_at"]:
                try:
                    fmt = '%Y-%m-%d %H:%M:%S'
                    start_dt = datetime.datetime.strptime(row["started_at"], fmt)
                    end_dt = datetime.datetime.strptime(row["ended_at"], fmt)
                    delta = end_dt - start_dt
                    
                    # === ここが重要：両方作る ===
                    
                    # 1. グラフ用 (数値: 小数点以下も保持)
                    total_seconds = delta.total_seconds()
                    hours_float = round(total_seconds / 3600, 4) 
                    
                    # 2. リスト表示用 (文字列: HH:MM:SS)
                    ts = int(total_seconds)
                    h, remainder = divmod(ts, 3600)
                    m, s = divmod(remainder, 60)
                    duration_str = f"{h:02}:{m:02}:{s:02}"
                    
                except Exception as e:
                    print(f"[Calc Error] {e}")
                    duration_str = "エラー"
                    hours_float = 0.0

            results.append({
                "subject": row["subject_name"],
                "duration": duration_str, # リスト表示で使う
                "hours": hours_float,     # グラフ集計で使う (これを復活させた！)
                "date": display_date
            })
        return results

    # -------------------------
    # ストップウォッチ機能
    # -------------------------
    def start_session(self, subject_name):
        if not self.conn or not self.cursor:
            return
        """計測開始"""
        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        sql = "INSERT INTO logs (subject_name, started_at) VALUES (?, ?)"
        self.cursor.execute(sql, (subject_name, now_str))
        self.conn.commit()
        
        return self.cursor.lastrowid

    def stop_session(self, session_id):
        if not self.conn or not self.cursor:
            return
        """計測終了"""
        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 終了時刻を更新
        sql = "UPDATE logs SET ended_at = ? WHERE id = ?"
        self.cursor.execute(sql, (now_str, session_id))
        self.conn.commit()

    def __del__(self):
        """クラス破棄時に接続を閉じる"""
        try:
            self.conn.close()
        except:
            pass