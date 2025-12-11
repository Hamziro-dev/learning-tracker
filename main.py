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

import logging
logging.getLogger('matplotlib.font_manager').disabled = True
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('mpl').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
import matplotlib.ticker as ticker
import math

# -------------------------
# 各画面クラス（UI層）
# -------------------------
class RecordScreen(MDScreen):
    session_id = None
    start_time = None
    event = None

    def toggle_stopwatch(self):
        """開始/停止ボタンが押された時の処理"""
        app = MDApp.get_running_app()
        
        subject = self.ids.txt_subject.text
        if not subject:
            app._snack("科目名を入力してください")
            return

        if self.session_id is None:
            # === 開始処理 ===
            self.session_id = app.db.start_session(subject)
            self.start_time = datetime.now()
            self.event = Clock.schedule_interval(self.update_timer, 0.1)
            self.ids.btn_toggle.text = "STOP"
            app._snack("計測開始")
            
        else:
            # === 停止処理 ===
            if self.event:
                self.event.cancel()
                self.event = None

            app.db.stop_session(self.session_id)
            self.session_id = None
            self.start_time = None
            self.ids.btn_toggle.text = "START"
            self.ids.lbl_timer.text = "00:00:00"
            app._snack("計測終了・保存完了")
            app.update_records()

    def update_timer(self, dt):
        """Clockによって定期的に呼ばれ、ラベルを更新する"""
        if self.start_time:
            delta = datetime.now() - self.start_time
            total_seconds = int(delta.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            time_str = f"{hours:02}:{minutes:02}:{seconds:02}"

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
        self.theme_cls.theme_style = "Dark" 
        self.theme_cls.primary_palette = "Blue"
        
# --------------------------------------------------------
# KivyMD への日本語フォントの適用
# --------------------------------------------------------
        target_font = "JPFont"
        text_style_prefixes = ["Display", "Headline", "Title", "Label", "Body"]

        for style_name, style_value in self.theme_cls.font_styles.items():
            
            if not any(style_name.startswith(prefix) for prefix in text_style_prefixes):
                continue

            if isinstance(style_value, dict):
                for role, settings in style_value.items():
                    if isinstance(settings, dict) and "font-name" in settings:
                        settings["font-name"] = target_font

            elif isinstance(style_value, (list, tuple)) and len(style_value) >= 4:
                self.theme_cls.font_styles[style_name] = [
                    target_font,
                    style_value[1],
                    style_value[2],
                    style_value[3]
                ]

        # --------------------------------------------------------
        # DBマネージャーのインスタンス化
        # --------------------------------------------------------
        self.db = DBManager()
        
        kv_path = os.path.join(os.path.dirname(__file__), "ui", "app.kv")
        root = Builder.load_file(kv_path)
        self.sm = root
        
        self.update_records() 
        
        return root
    
    def on_start(self):
        """
        ユーザーに画面を見せつつ、裏でDB接続を行う。
        """
        # 1. ここで初めてPostgreSQLに接続
        if hasattr(self.db, 'connect'):
             self.db.connect()
        
        # 2. 接続完了後にデータを取得して表示
        self.update_records()
    
    def _snack(self, text: str):
        if not self.root:
            print(f"[SNACK LOG] {text}")
            return

        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        
        def _show(dt):
            try:
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
# 記録追加
# -------------------------
    def add_record(self, subject: str, hours):
        
        try:         
            if not hours or str(hours).strip() == "":
                self._snack("時間を入力してください。")
                return
            
            if hours <= 0:
                self._snack("0より大きい数を入力してください。")
                return

            hours = float(hours)

            self.db.add_record(subject, hours)

            self.update_records()
            self._snack(f"追加: {subject} {hours}時間")

        except ValueError:
            self._snack("数値として認識できません。例: 1 または 1.5")

        except Exception as e:
            print("=== add_record() ERROR ===")
            print(repr(e))
            traceback.print_exc()
            self._snack(f"エラー: {e}")

    def switch_to_main_screen(self):
        self.sm.current = "record"

# -------------------------
# 記録リスト更新
# -------------------------
    def update_records(self):
        try:
            screen = self.sm.get_screen("record") 
            container = screen.ids.get("record_list", None)
            if container is None:
                print("record_list が見つからない。kvの id を確認してください。")
                return

            container.clear_widgets()

            for rec in self.db.get_records():
                subj = rec.get("subject", "")
                
                duration = rec.get("duration", "")
                date = rec.get("date", "")
                
                container.add_widget(
 
                MDLabel(text=f"{date}｜{subj}：{duration}", size_hint_y=None, height=30)
                )

        except Exception as e:
            print("=== update_records() ERROR ===")
            import traceback; traceback.print_exc()

# -------------------------
# グラフ画面表示
# -------------------------
    def show_graph(self):
        try:
            base_dir = os.path.dirname(__file__)
            font_dir = os.path.join(base_dir, "fonts")
            jp_font_path = os.path.join(font_dir, "NotoSansJP-Regular.ttf")

            # Matplotlib にフォントを登録
            fm.fontManager.addfont(jp_font_path)
            font_prop = fm.FontProperties(fname=jp_font_path)
            matplotlib.rcParams["font.family"] = font_prop.get_name()

            records = self.db.get_records()

            if not records:
                self._snack("記録がありません。")
                return
            
            summary = {}
            for rec in records:
                date = rec["date"].split(" ")[0]
                summary[date] = summary.get(date, 0) + rec["hours"]

            plt.figure(figsize=(7, 4))
            
            bars = plt.bar(summary.keys(), summary.values(), color="skyblue")
            
            plt.title("学習時間の推移", fontproperties=font_prop)
            plt.xlabel("日付", fontproperties=font_prop)
            plt.ylabel("時間（h）", fontproperties=font_prop)
            
            max_hours = max(summary.values()) if summary.values() else 0
            
            upper_limit = math.ceil(max_hours) + 1 if max_hours > 0 else 1
            plt.ylim(0, upper_limit)

            plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
            
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    # 小数点1位まで表示 (例: 1.5h, 0.1h)
                    plt.text(bar.get_x() + bar.get_width()/2., height,
                             f'{height:.1f}h',
                             ha='center', va='bottom', fontproperties=font_prop, fontsize=9)

            plt.tight_layout()
            
            canvas = FigureCanvasKivyAgg(plt.gcf())
            screen = self.sm.get_screen("graph")
            graph_layout = screen.ids.graph_area 
            graph_layout.clear_widgets()
            graph_layout.add_widget(canvas)
            
            self.sm.current = "graph"

        except Exception as e:
            print("=== show_graph() ERROR ===")
            print(repr(e))
            import traceback
            traceback.print_exc()
            self._snack(f"グラフ表示でエラー: {e}")


if __name__ == "__main__":
    LearningTrackerApp().run()
