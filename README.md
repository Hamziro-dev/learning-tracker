# Learning Tracker   
日々の学習時間を「見える化」し、継続を支援するデスクトップアプリ
![result](https://github.com/user-attachments/assets/0534be88-6561-49bd-80fe-44f42ec72245)

## 概要
学習項目ごとの時間をストップウォッチ形式で計測・記録し、過去の積み上げを可視化するGUIアプリケーションです。<br>
「勉強時間を手軽に記録したいが、既存のスマホアプリではPC作業中に気が散る」という自身の課題を解決するために開発しました。
Python (Kivy/KivyMD) を採用し、Windows等のデスクトップ環境でローカルかつ軽量に動作します。<br>
また、UI/状態管理/永続化/テストの基礎を一つの成果物で同時に鍛え、以下の2つを積み上げる目的もあります。<br>
（1）学習ログの記録・可視化<br>
（2）GUI・DB・テストの実装経験

## 特徴
【シンプルな計測】科目名を入力してボタンを押すだけのミニマルなUI。<br>
【正確な記録】アプリを閉じても計測が途切れないデータ永続化設計。<br>
【即時の可視化】SQLiteデータベースによる履歴のリスト表示・グラフ化機能。<br>
【YAGNI原則に基づく設計】過剰な認証機能を排除し、起動から1秒で計測開始できるシングルユーザー特化仕様。<br>

## 技術仕様
| カテゴリ | 技術 | 備考 |
|---|---|---|
| 言語 | Python 3.13 | |
| GUIフレームワーク | Kivy 2.3.1 / KivyMD | マテリアルデザイン適用 |
| データベース | SQLite3 | ローカル永続化 |
| アーキテクチャ | MVC風構成 | UIとロジックの分離 |

## システム設計

### ▼ システム構成図
Windows等のクライアントPC上で完結するスタンドアローン構成です。<br>
外部サーバーとの通信を行わないため、オフライン環境でも動作し、学習データのプライバシーが保護されます。<br>

<img width="381" height="436" alt="システム構成 drawio" src="https://github.com/user-attachments/assets/a787011d-b1b2-421c-976d-1353b7ad19c7" /><br>

### ▼ ER図（データ設計）
YAGNI原則に基づき、認証機能を排除したシングルユーザー・シングルテーブル構成を採用しました。<br>
実用最小限の設計により、高速な動作と堅牢なデータ整合性を実現しています。<br>

<img width="521" height="231" alt="ER図 drawio" src="https://github.com/user-attachments/assets/3a72d166-c34c-4c96-b33e-39f900e89321" /><br>

## 動作環境・セットアップ

```bash
# リポジトリのクローン
git clone [https://github.com/Hamziro-dev/learning-tracker.git](https://github.com/Hamziro-dev/learning-tracker.git)
cd learning-tracker

# 仮想環境の作成と有効化
python -m venv venv
# Windowsの場合
.\venv\Scripts\activate

# 依存ライブラリのインストール
pip install -r requirements.txt

# アプリの起動
python main.py
```

## ディレクトリ構成

learning-tracker/<br>
├── data/ (app_data.db)<br>
├── logic/ (db_manager.py)<br>
├── ui/ (app.kv)<br>
├── fonts/ <br>
└── main.py  <br>

## 💡工夫した点
【非同期とイベントループの理解】Kivy Clock を使用し、GUIをフリーズさせずに正確なタイマー処理を実装しました。<br>
【堅牢なデータ設計】単純なカウンターではなく、開始時刻・終了時刻を記録するログ形式を採用し、アプリクラッシュ時やリロード時のデータ整合性を担保しました。<br>
【保守性の向上】当初は main.py にベタ書きしていたSQL処理を DBManager クラスに切り出し、責務を分離しました。<br>

## ライセンス
MIT License

- 開発ログはこちら → [Qiita: ハム二郎の学習記録](https://qiita.com/Hamziro_dev)