import sqlite3
import os
import datetime

class DBManager:
    def __init__(self):
        # データベースファイルのパス設定
        base_dir = os.path.dirname(os.path.dirname(__file__))  # logicの親ディレクトリ
        db_path = os.path.join(base_dir, "app_data.db")
        
        # データベース接続
        # check_same_thread=False はKivyのようなGUIアプリでスレッドエラーを防ぐために必要
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # カラム名でアクセスできるようにする
        self.cursor = self.conn.cursor()
        
        # テーブル作成
        self.create_tables()

    def create_tables(self):
        """必要なテーブルを全て作成する"""
        # ユーザーテーブル (password_hash を含む)
        sql_users = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
        """
        self.cursor.execute(sql_users)

        # 学習ログテーブル (ストップウォッチ用 & 手動記録用)
        # started_at, ended_at は文字列で保存
        # hours は手動入力用（ストップウォッチの場合は計算で出すが、今回は共存させる）
        sql_logs = """
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
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
    # ユーザー管理
    # -------------------------
    def add_user(self, name, password):
        """ユーザー登録（簡易ハッシュ化）"""
        import hashlib
        p_hash = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            sql = "INSERT INTO users (name, password_hash) VALUES (?, ?)"
            self.cursor.execute(sql, (name, p_hash))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            # 既に同名ユーザーがいる場合など
            print(f"[DB ERROR] User {name} already exists.")
            return None

    def get_user(self, name, password):
        """ログイン認証（IDを返す、失敗ならNone）"""
        import hashlib
        p_hash = hashlib.sha256(password.encode()).hexdigest()
        
        sql = "SELECT id FROM users WHERE name = ? AND password_hash = ?"
        self.cursor.execute(sql, (name, p_hash))
        result = self.cursor.fetchone()
        
        if result:
            return result["id"]
        else:
            return None

    # -------------------------
    # 記録管理（手動）
    # -------------------------
    def add_record(self, user_id, subject, hours):
        """手動で時間を記録する"""
        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        sql = "INSERT INTO logs (user_id, subject_name, hours, date) VALUES (?, ?, ?, ?)"
        self.cursor.execute(sql, (user_id, subject, hours, now_str))
        self.conn.commit()

    def get_records(self, user_id):
        """ユーザーの全記録を取得（リスト表示用）"""
        # dateがある場合はそれを、なければstarted_atを表示用に使うなどの工夫が可能
        # ここでは単純に全件取得
        sql = "SELECT * FROM logs WHERE user_id = ? ORDER BY id DESC"
        self.cursor.execute(sql, (user_id,))
        rows = self.cursor.fetchall()
        
        # 辞書型に変換して返す
        results = []
        for row in rows:
            # 日付の表示ロジック: dateがあればdate, なければstarted_at
            display_date = row["date"] if row["date"] else row["started_at"]
            
            # 時間の表示ロジック: hoursがあればhours, なければ計算...だが今回はhours優先
            # ストップウォッチ記録の場合、hoursがNULLの可能性があるため計算が必要
            hours = row["hours"]
            if hours is None and row["started_at"] and row["ended_at"]:
                # 終了済みのストップウォッチデータなら差分計算
                try:
                    fmt = '%Y-%m-%d %H:%M:%S'
                    start_dt = datetime.datetime.strptime(row["started_at"], fmt)
                    end_dt = datetime.datetime.strptime(row["ended_at"], fmt)
                    delta = end_dt - start_dt
                    hours = round(delta.total_seconds() / 3600, 2)
                except:
                    hours = 0
            
            results.append({
                "subject": row["subject_name"],
                "hours": hours if hours else 0,
                "date": display_date
            })
        return results

    # -------------------------
    # ストップウォッチ機能
    # -------------------------
    def start_session(self, user_id, subject_name):
        """計測開始"""
        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        sql = "INSERT INTO logs (user_id, subject_name, started_at) VALUES (?, ?, ?)"
        self.cursor.execute(sql, (user_id, subject_name, now_str))
        self.conn.commit()
        
        return self.cursor.lastrowid

    def stop_session(self, session_id):
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