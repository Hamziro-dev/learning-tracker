#main.py
# --------------------------------------------------------
# 日本語フォントセットアップ（Kivy import の完全前）
# --------------------------------------------------------
import os
from kivymd.font_definitions import theme_font_styles

BASE_DIR = os.path.dirname(__file__)
FONT_DIR = os.path.join(BASE_DIR, "fonts")
JP_FONT = os.path.join(FONT_DIR, "NotoSansJP-Regular.ttf")

from kivy.core.text import LabelBase
LabelBase.register(
    name="JPFont",
    fn_regular=JP_FONT,
    fn_bold=JP_FONT,
    fn_italic=JP_FONT,
    fn_bolditalic=JP_FONT,
)

import traceback
from datetime import datetime

from kivy.lang import Builder
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path, resource_find
from kivy.config import Config

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText

from logic.db_manager import DBManager

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

# main.py の RecordScreen クラスを置換

class RecordScreen(MDScreen):
    # ストップウォッチの状態管理用変数
    session_id = None
    start_time = None
    event = None  # Clockイベントの格納用

    def toggle_stopwatch(self):
        """開始/停止ボタンが押された時の処理"""
        app = MDApp.get_running_app()
        
        # 画面上の入力欄から科目名を取得（idは kvファイルで定義する必要あり）
        subject = self.ids.txt_subject.text
        if not subject:
            app._snack("科目名を入力してください")
            return

        if self.session_id is None:
            # === 開始処理 ===
            # 1. DBに記録開始
            self.session_id = app.db.start_session(app.user_id, subject)
            
            # 2. 開始時刻をメモリに保持（計算用）
            self.start_time = datetime.now()
            
            # 3. 0.1秒ごとに update_timer を呼ぶようスケジュール
            self.event = Clock.schedule_interval(self.update_timer, 0.1)
            
            # 4. ボタンの見た目を変える（Start -> Stop）
            self.ids.btn_toggle.text = "STOP"
            app._snack("計測開始")
            
        else:
            # === 停止処理 ===
            # 1. スケジュール停止
            if self.event:
                self.event.cancel()
                self.event = None
            
            # 2. DBに記録終了
            app.db.stop_session(self.session_id)
            
            # 3. リセット
            self.session_id = None
            self.start_time = None
            self.ids.btn_toggle.text = "START"
            self.ids.lbl_timer.text = "00:00:00"
            app._snack("計測終了・保存完了")
            
            # リストを更新（Appクラスのメソッドを呼ぶ）
            app.update_records()

    def update_timer(self, dt):
        """Clockによって定期的に呼ばれ、ラベルを更新する"""
        if self.start_time:
            # 経過時間を計算
            delta = datetime.now() - self.start_time
            
            # "H:M:S" 形式に整形（ミリ秒は捨てる）
            # deltaには days, seconds, microseconds がある
            total_seconds = int(delta.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
            
            # 画面のラベルを更新
            self.ids.lbl_timer.text = time_str

class GraphScreen(MDScreen):
    pass

# -------------------------
# アプリ全体（App層）
# -------------------------
class LearningTrackerApp(MDApp):
    def build(self):
        self.title = "学習記録トラッカー"
        self.theme_cls.material_style = "M2"
        # --------------------------------------------------------
        # KivyMD への日本語フォントの適用
        # --------------------------------------------------------
        target_font = "JPFont"
        
        # 日本語化すべきテキスト用スタイルのプレフィックス
        # これ以外のスタイル（Iconなど）は一切触らないことで安全を確保する
        text_style_prefixes = ["Display", "Headline", "Title", "Label", "Body"]

        for style_name, style_value in self.theme_cls.font_styles.items():
            
            # 🛡️ ホワイトリストチェック: 
            # スタイル名が "Display", "Body" などで始まるものだけを対象にする
            if not any(style_name.startswith(prefix) for prefix in text_style_prefixes):
                continue

            # パターンA: MD3スタイル (辞書型: {'large': {...}, 'medium': {...}})
            if isinstance(style_value, dict):
                for role, settings in style_value.items():
                    if isinstance(settings, dict) and "font-name" in settings:
                        settings["font-name"] = target_font

            # パターンB: レガシースタイル (リスト型)
            elif isinstance(style_value, (list, tuple)) and len(style_value) >= 4:
                self.theme_cls.font_styles[style_name] = [
                    target_font,
                    style_value[1],
                    style_value[2],
                    style_value[3]
                ]

        # --------------------------------------------------------

        # DB初期化
        self.db = DBManager()
        self.user_id = None
        kv_path = os.path.join(os.path.dirname(__file__), "ui", "app.kv")
        root = Builder.load_file(kv_path)
        self.sm = root
        return root

# LearningTrackerAppクラス内の _snack をこれに差し替え
    def _snack(self, text: str):
        """
        Kivy 2.3.1 + KivyMD の非互換性回避のため、
        MDSnackbarではなく標準Popupを使用する。
        """
        if not self.root:
            print(f"[SNACK LOG] {text}")
            return

        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        
        def _show(dt):
            try:
                # 日本語フォントを適用して豆腐化を防ぐ
                content = Label(text=text, font_name="JPFont")
                
                popup = Popup(
                    title="通知",
                    title_font="JPFont",
                    content=content,
                    size_hint=(0.8, 0.2),
                    auto_dismiss=True
                )
                popup.open()
            except Exception as e:
                print(f"[SNACK ERROR] {e}")

        Clock.schedule_once(_show, 0.1)
    
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
                container.add_widget(MDLabel(text="ログインしてください。", size_hint_y=None, height=30))
                return

            for rec in self.db.get_records(self.user_id):
                subj = rec.get("subject", "")
                hrs = rec.get("hours", 0)
                date = rec.get("date", "")
                container.add_widget(
                    MDLabel(text=f"{date}｜{subj}：{hrs}時間", size_hint_y=None, height=30)
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
            import matplotlib
            import matplotlib.pyplot as plt
            import matplotlib.font_manager as fm
            from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
            base_dir = os.path.dirname(__file__)
            font_dir = os.path.join(base_dir, "fonts")
            jp_font_path = os.path.join(font_dir, "NotoSansJP-Regular.ttf")

            # ▼ Matplotlib にフォントを登録
            fm.fontManager.addfont(jp_font_path)
            font_prop = fm.FontProperties(fname=jp_font_path)
            matplotlib.rcParams["font.family"] = font_prop.get_name()

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
            plt.title("学習時間の推移", fontproperties=font_prop)
            plt.xlabel("日付", fontproperties=font_prop)
            plt.ylabel("時間（h）", fontproperties=font_prop)
            plt.tight_layout()
            plt.show()
            
            # グラフ画面へ遷移
            self.sm.current = "graph"

        except Exception as e:
            print("=== show_graph() ERROR ===")
            print(repr(e))
            import traceback
            traceback.print_exc()
            self._snack(f"グラフ表示でエラー: {e}")


if __name__ == "__main__":
    LearningTrackerApp().run()
