#main.py
import os
from kivy.app import App
from kivy.lang import Builder
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
import matplotlib.pyplot as plt
from logic.db_manager import DBManager
from kivymd.app import MDApp
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.core.text import LabelBase
from logic.tracker import Tracker
import traceback


# -------------------------
# 補助関数群
# -------------------------

#日本語フォント
LabelBase.register(name="Roboto", fn_regular="C:/Windows/Fonts/HGRME.TTC")

def _snack(msg: str):
    """簡易トースト通知。KivyMD環境で例外や進捗を表示"""
    try:
        MDSnackbar(text=msg, duration=2).open()
    except Exception:
        print(f"[SNACK LOG] {msg}")

def _label(self, text):
        from kivymd.uix.label import MDLabel
        return MDLabel(
            text=text,
            halign="left",
            size_hint_y=None,
            height=30,
        )

# -------------------------
# 各画面クラス（UI層）
# -------------------------
class LoginScreen(MDScreen):
    def _snack(self, text: str):
        """KivyMD v2対応 Snackbar表示"""
        def _show(dt):
            snackbar = MDSnackbar(
                MDSnackbarText(
                    text=text,
                    halign="center",
                ),
                y=dp(24),
                pos_hint={"center_x": 0.5},
                size_hint_x=0.8,
                radius=[8],
            )
            snackbar.open()
            self.snackbar = snackbar  # 破棄防止
        # GUIが安定してから呼ぶ
        Clock.schedule_once(_show, 0.1)

    def login(self):
        app = MDApp.get_running_app()
        username = self.ids.username.text
        password = self.ids.password.text
        user_id = app.db.add_user(username, password)
        app.user_id = user_id
        app.switch_to_main_screen()

class RecordScreen(MDScreen):
    pass

class GraphScreen(MDScreen):
    pass

# -------------------------
# アプリ全体（App層）
# -------------------------
class LearningTrackerApp(MDApp):
    def build(self):
        self.title = "Learning Tracker"
        self.theme_cls.material_style = "M3"
        self.sm = MDScreenManager()
        # DB初期化
        self.db = DBManager()
        self.user_id = None
        kv_path = os.path.join(os.path.dirname(__file__), "ui", "app.kv")
        self.sm = Builder.load_file(kv_path)
        return self.sm
    
# -------------------------
# ログイン処理
# -------------------------
    def login(self, username, password):
        try:
            uid = self.db.get_user(username, password)
            if not uid:
                #　未登録なら新規作成
                self.db.add_user(username, password)
                uid = self.db.get_user(username, password)
            self.user_id = uid
            print(f"[DEBUG] Login success: user_id={self.user_id}")
            self.sm.current = "record"
            self.update_records()
        except Exception as e:
            print("[ERROR] login()", e)
            traceback.print_exc()

# -------------------------
# 記録追加
# -------------------------
    def add_record(self, subject: str, hours):
        print("[DEBUG] add_record called") 
        print(f"[DEBUG] subject={subject!r}, hours={hours!r}")
        
        try:
            if not self.user_id:
                _snack("未ログインです。先にログインしてください。")
                return
            
            # 空文字・None 対策
            if not hours or str(hours).strip() == "":
                self._snack("時間を入力してください。")
                return
            
            # 負数や0の禁止
            if hours <= 0:
                self._snack("0より大きい数を入力してください。")
                return

            # 型はここで固定（文字列が来ても潰す）
            hours = float(hours)

            # DB書き込み
            self.db.add_record(self.user_id, subject, hours)

            # 一覧更新
            self.db.add_record(self.user_id, subject, hours)
            self.update_records()
            _snack(f"追加: {subject} {hours}時間")

        except ValueError:
            self._snack("数値として認識できません。例: 1 または 1.5")

        except Exception as e:
            print("=== add_record() ERROR ===")
            print(repr(e))
            traceback.print_exc()
            _snack(f"エラー: {e}")

    def switch_to_main_screen(self):
        self.sm.current = "record"

    def register(self, username, password):
        self.db.add_user(username, password)
        self.show_dialog("登録完了", f"{username} を登録しました。")

# -------------------------
# 記録リスト更新
# -------------------------
    def update_records(self):
        try:
            screen = self.sm.get_screen("record")  # MDScreenManager 自身
            container = screen.ids.get("record_list", None)
            if container is None:
                print("record_list が見つからない。kvの id を確認しろ。")
                return

            container.clear_widgets()

            if not self.user_id:
                container.add_widget(Label(text="ログインしてください。", size_hint_y=None, height=30))
                return

            for rec in self.db.get_records(self.user_id):
                subj = rec.get("subject", "")
                hrs = rec.get("hours", 0)
                date = rec.get("date", "")
                container.add_widget(
                    Label(text=f"{date}｜{subj}：{hrs}時間", size_hint_y=None, height=30)
                )

        except Exception as e:
            print("=== update_records() ERROR ===")
            import traceback; traceback.print_exc()

    def show_dialog(self, title, text):

        def close_dialog(*_):
            dialog.dismiss()

        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDButton(
                    MDButtonText(text="OK"),
                    style="text",
                    on_release=close_dialog
                )
            ]
        )
        dialog.open()

# -------------------------
# グラフ画面表示
# -------------------------
    def show_graph(self):
        try:
            from matplotlib import pyplot as plt

            records = self.db.get_records(self.user_id)
            if not records:
                self._snack("記録がありません。")
                return

            # 日付別に合計時間を集計
            summary = {}
            for rec in records:
                date = rec["date"].split(" ")[0]
                summary[date] = summary.get(date, 0) + rec["hours"]

            plt.figure(figsize=(7, 4))
            plt.bar(summary.keys(), summary.values(), color="skyblue")
            plt.title("学習時間の推移")
            plt.xlabel("日付")
            plt.ylabel("時間（h）")
            plt.tight_layout()
            plt.show()
            
            # グラフ画面へ遷移
            self.root.ids.sm.current = "graph"

        except Exception as e:
            print("=== show_graph() ERROR ===")
            print(repr(e))
            import traceback
            traceback.print_exc()
            self._snack(f"グラフ表示でエラー: {e}")


if __name__ == "__main__":
    LearningTrackerApp().run()
