import psycopg2
from psycopg2.extras import RealDictCursor
import datetime
import os

class DBManager:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self):
        """アプリ起動後（on_start）または再接続時に呼ばれる"""
        # 既に生きた接続があれば何もしない
        if self.conn is not None and self.conn.closed == 0:
            return

        try:
            # 【対策1】keepalives設定を追加
            # これにより、無通信状態でも裏で「信号」を送り、切断を防ぐ
            self.conn = psycopg2.connect(
                host=os.environ.get("DB_HOST", "localhost"),
                dbname="learning_tracker_db",
                user="hamziro",
                password=os.environ.get("DB_PASSWORD", "YOUR_PASSWORD"),
                cursor_factory=RealDictCursor,
                # ▼ 追加設定
                keepalives=1,           # Keepaliveを有効化
                keepalives_idle=30,     # 30秒無通信なら信号を送る
                keepalives_interval=10, # 応答なければ10秒ごとに再送
                keepalives_count=5      # 5回失敗したら切断とみなす 
            )
            self.conn.autocommit = False
            self.cursor = self.conn.cursor()
            
            # 接続成功時にテーブル作成
            self.create_tables()
            print("[INFO] PostgreSQL Connected (with Keepalive).")

        except Exception as e:
            print(f"[ERROR] Postgres Connection Failed: {e}")
            self.conn = None
            self.cursor = None

    def _ensure_connection(self):
        """
        SQL実行直前に呼び出し、接続が切れていたら再接続するヘルパーメソッド
        """
        if self.conn is None or self.conn.closed != 0:
            print("[WARN] Connection lost. Reconnecting...")
            self.conn = None
            self.connect()

    def create_tables(self):
        if not self.conn or not self.cursor:
            return
        
        """PostgreSQL用のテーブル作成"""
        # SQLite: INTEGER PRIMARY KEY AUTOINCREMENT
        # Postgres: SERIAL PRIMARY KEY
        sql_logs = """
        CREATE TABLE IF NOT EXISTS logs (
            id SERIAL PRIMARY KEY,
            subject_name TEXT,
            started_at TEXT,
            ended_at TEXT,
            hours REAL,
            date TEXT
        );
        """
        try:
            self.cursor.execute(sql_logs)
            self.conn.commit()
        except Exception as e:
            print(f"[Error create_tables] {e}")
            self.conn.rollback()

    # -------------------------
    # 記録管理（手動）
    # -------------------------
    def add_record(self, subject, hours):
        self._ensure_connection() # 念の為チェック
        if not self.conn:
            return
        
        try:
            now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = "INSERT INTO logs (subject_name, hours, date) VALUES (%s, %s, %s)"
            self.cursor.execute(sql, (subject, hours, now_str))
            self.conn.commit()
        except psycopg2.OperationalError:
            # エラーが出たら再接続して1回だけリトライ
            print("[Retry] add_record recovering connection...")
            self.conn = None
            self.connect()
            if self.conn:
                self.cursor.execute(sql, (subject, hours, now_str))
                self.conn.commit()

    def get_records(self):
        self._ensure_connection()
        if not self.conn:
            return []
        
        try:
            sql = "SELECT * FROM logs ORDER BY id DESC"
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()
            
            results = []
            for row in rows:
                display_date = row["date"] if row["date"] else row["started_at"]
                
                duration_str = "00:00:00"
                hours_float = 0.0

            if row["hours"] is not None:
                    hours_float = float(row["hours"])
                    duration_str = f"{hours_float}時間"
            elif row["started_at"] and row["ended_at"]:
                try:
                    fmt = '%Y-%m-%d %H:%M:%S'
                    start_dt = datetime.datetime.strptime(row["started_at"], fmt)
                    end_dt = datetime.datetime.strptime(row["ended_at"], fmt)
                    delta = end_dt - start_dt
                    total_seconds = delta.total_seconds()
                    hours_float = round(total_seconds / 3600, 4) 
                    ts = int(total_seconds)
                    h, remainder = divmod(ts, 3600)
                    m, s = divmod(remainder, 60)
                    duration_str = f"{h:02}:{m:02}:{s:02}"
                except:
                    pass
            
            results.append({
                "subject": row["subject_name"],
                "duration": duration_str,
                "hours": hours_float,
                "date": display_date
                })
            return results
        except Exception as e:
            print(f"[Get Records Error] {e}")
            self.conn = None # 次回再接続させる
            return []

    # -------------------------
    # ストップウォッチ機能
    # -------------------------
    def start_session(self, subject_name):
        self._ensure_connection()
        if not self.conn:
            return None
        
        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = "INSERT INTO logs (subject_name, started_at) VALUES (%s, %s) RETURNING id"
        
        try:
            self.cursor.execute(sql, (subject_name, now_str))
            new_id = self.cursor.fetchone()['id']
            self.conn.commit()
            return new_id
        except Exception as e:
            print(f"[Start Session Error] {e}")
            self.conn.rollback()
            return None

    def stop_session(self, session_id):
        """
        【対策2】ここが一番重要。長時間経過後に呼ばれるため切断されやすい。
        エラーが発生したら再接続してリトライする処理を追加。
        """
        self._ensure_connection()
        if not self.conn: return

        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = "UPDATE logs SET ended_at = %s WHERE id = %s"

        try:
            # 1回目のトライ
            self.cursor.execute(sql, (now_str, session_id))
            self.conn.commit()
            print("[INFO] Session stopped successfully.")

        except psycopg2.OperationalError:
            # 切断エラーを検知したら、ここに来る
            print("[WARN] Connection dead during stop_session. Retrying...")
            
            # 再接続を試みる
            self.conn = None
            self.connect()
            
            if self.conn:
                # 2回目のトライ（リトライ）
                try:
                    self.cursor.execute(sql, (now_str, session_id))
                    self.conn.commit()
                    print("[INFO] Retry successful.")
                except Exception as e:
                    print(f"[ERROR] Retry failed: {e}")
            else:
                print("[FATAL] Could not reconnect.")

    def __del__(self):
        try:
            if self.conn: self.conn.close()
        except: pass