# tracker.py
import json
import os
from datetime import datetime
from collections import defaultdict


class Tracker:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        self.data_dir = os.path.join(base_dir, "data")
        self.file_path = os.path.join(self.data_dir, "records.json")

        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        # 常に空データで初期化
        self.data = self.load_data()

    def load_data(self):
        """JSONファイルからデータを読み込む"""
        if not os.path.exists(self.file_path):
            return []
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for record in data:
                    if "date" not in record:
                        record["date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    if "note" not in record:
                        record["note"] = ""
                return data
        except json.JSONDecodeError:
            return []

    def save_data(self):
        """データをJSONファイルに保存"""
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_entry(self, subject, hours, note=""):
        """新しい学習記録を追加"""
        new_record = {
            "subject": subject,
            "hours": hours,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "note": note
        }
        self.data.append(new_record)
        self.save_data()
        print(f"記録: {subject} {hours}時間（{new_record['date']}）")

    def summarize_by_date(self):
        """日付ごとの学習時間合計を返す"""
        summary = defaultdict(float)
        for record in self.data:
            date = record["date"].split(" ")[0]
            summary[date] += float(record["hours"])
        return dict(summary)

    def get_records(self):
        """全学習記録を返す"""
        return self.data

