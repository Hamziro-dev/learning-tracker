import psycopg2
from psycopg2.extras import RealDictCursor
import datetime

class DBManager:
    def __init__(self):
        # === PostgreSQL接続設定 ===
        # 本来は環境変数から読み込むべきだが、学習用MVPとしてベタ書きを許容する
        try:
            self.conn = psycopg2.connect(
                host="localhost",
                dbname="learning_tracker_db",
                user="hamziro",
                password="1234",
                cursor_factory=RealDictCursor  # これにより辞書型(row['key'])で取得可能になる
            )
            self.conn.autocommit = False # 明示的にcommitする設定
            self.cursor = self.conn.cursor()
            
            # テーブル作成実行
            self.create_tables()
            
        except Exception as e:
            print(f"[DB INIT ERROR] 接続失敗: {e}")
            raise e

    def create_tables(self):
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
            self.conn.rollback() # エラー時は必ずロールバック
            print(f"[Create Table Error] {e}")

    # -------------------------
    # 記録管理（手動）
    # -------------------------
    def add_record(self, subject, hours):
        """手動で時間を記録する"""
        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # プレースホルダを ? から %s に変更
        sql = "INSERT INTO logs (subject_name, hours, date) VALUES (%s, %s, %s)"
        try:
            self.cursor.execute(sql, (subject, hours, now_str))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"[Add Record Error] {e}")

    def get_records(self):
        """全記録を取得（リスト表示用）"""
        sql = "SELECT * FROM logs ORDER BY id DESC"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        
        results = []
        for row in rows:
            # PostgreSQLのRealDictCursorはNoneを返すことがあるため安全策
            display_date = row["date"] if row["date"] else row["started_at"]
            
            duration_str = "00:00:00"
            hours_float = 0.0
            
            # パターンA: 手動入力
            if row["hours"] is not None:
                hours_float = float(row["hours"])
                duration_str = f"{hours_float}時間"

            # パターンB: ストップウォッチ記録
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
                    duration_str = "エラー"
                    hours_float = 0.0

            results.append({
                "subject": row["subject_name"],
                "duration": duration_str,
                "hours": hours_float,
                "date": display_date
            })
        return results

    # -------------------------
    # ストップウォッチ機能
    # -------------------------
    def start_session(self, subject_name):
        """計測開始"""
        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # PostgreSQL特有: IDを取得するために RETURNING id をつける
        sql = "INSERT INTO logs (subject_name, started_at) VALUES (%s, %s) RETURNING id"
        
        try:
            self.cursor.execute(sql, (subject_name, now_str))
            new_id = self.cursor.fetchone()['id'] # 戻り値からIDを取り出す
            self.conn.commit()
            return new_id
        except Exception as e:
            self.conn.rollback()
            print(f"[Start Session Error] {e}")
            return None

    def stop_session(self, session_id):
        """計測終了"""
        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # プレースホルダを %s に変更
        sql = "UPDATE logs SET ended_at = %s WHERE id = %s"
        try:
            self.cursor.execute(sql, (now_str, session_id))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"[Stop Session Error] {e}")

    def __del__(self):
        try:
            self.conn.close()
        except:
            pass