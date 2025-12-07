# Learning Tracker(Server-Side Edition)
**PostgreSQL + WSL2 + 自動バックアップ運用を実装した、実務想定の発展版** 
> [!IMPORTANT]
> このブランチ (`feature/postgresql`) は、インフラ構築と運用自動化のスキルを実証するための**クライアント・サーバー構成版**です。
> アプリケーションの動作には **WSL2 (Ubuntu)** および **PostgreSQL** の環境構築が必須となります。
> 簡易的な動作確認を行いたい場合は、スタンドアローン構成の **[`main`](https://github.com/Hamziro-dev/learning-tracker/tree/main)** ブランチをご利用ください。  

![result](https://github.com/user-attachments/assets/0534be88-6561-49bd-80fe-44f42ec72245)

## ブランチとエディション構成
本リポジトリでは、異なる**運用環境（デプロイメントモデル）** に対応するため、以下の2つのブランチを並行して管理しています。
両者はデータベース接続方式およびインフラ要件が根本的に異なるため、マージせずに独立した構成としています。

| ブランチ | アーキテクチャ | DB構成 | インフラ要件 |
|:-|:-|:-|:-|
| **[`main`](https://github.com/Hamziro-dev/learning-tracker/tree/main)** | **スタンドアローン型** | **SQLite** | **Pythonのみ**<br>(ローカル完結・外部依存なし) |
| **[`feature/postgresql`](https://github.com/Hamziro-dev/learning-tracker/tree/feature/postgresql)** | **クライアント・サーバー型** | **PostgreSQL** | **WSL2 + DB Server**<br>(ネットワーク接続・3層構成) |

> [!NOTE]
> - **main：** データの永続化をローカルファイルで行う、ポータビリティを最優先した構成です。
> - **feature/postgresql：** データの永続化を外部RDBMSで行う、スケーラビリティと運用自動化（バックアップ等）を重視した構成です。

## 技術仕様 (Feature Branch)
| カテゴリ | 技術 | 備考 |
|---|---|---|
| 言語 | Python 3.13 | |
| GUIフレームワーク | Kivy 2.3.1 | Windows側で動作 |
| **Database** | **PostgreSQL 16** | **WSL2 (Ubuntu) 上で稼働** |
| **Infra** | **WSL2 / Linux** | クライアント・サーバー構成 |
| **Ops** | **Bash / Cron** | 自動バックアップ・世代管理 |

## システム設計 (本ブランチの変更点)

### ▼ クライアント・サーバー構成
本バージョンでは、クライアント（Windows/Python）とデータベース（Linux/PostgreSQL）を分離した **3層スキーマ構成** を採用しています。
Windows上のアプリから、TCP/IP経由でWSL2上のDBサーバーへ接続し、データを永続化します。

**ネットワーク構成：**
- **Client：** Windows 11 (Python / Psycopg2)
- **Server：** WSL2 Ubuntu 24.04 (PostgreSQL)
- **Connection：** TCP/IP (localhost:5432)

## 動作環境・セットアップ
本ブランチの動作には、以下のインフラ構築が必要です。

### 1. インフラ構築 (WSL2 / Ubuntu)
```bash
# PostgreSQLのインストール
sudo apt update && sudo apt install postgresql postgresql-contrib libpq-dev -y

# 外部接続の許可設定 (postgresql.conf / pg_hba.conf)
# Windows側からのTCP/IP接続を許可する設定を実施
```

### 2. アプリケーションのセットアップ (Windows)

```bash
# リポジトリのクローンとブランチ切り替え
git clone [https://github.com/Hamziro-dev/learning-tracker.git](https://github.com/Hamziro-dev/learning-tracker.git)
cd learning-tracker
git checkout feature/postgresql

# 仮想環境と依存ライブラリ (psycopg2含む)
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# アプリ起動
python main.py
```

## 運用自動化
本環境では、データの保全性を高めるため、以下の運用スクリプトを稼働させています。

- バックアップ：pg_dump を用いてDBダンプを取得し、gzip圧縮して保存。

- 世代管理：7日以上前のバックアップファイルを自動削除。

- スケジューリング：Cron により毎日AM 3:00に自動実行。

- スクリプト本体：backup.sh

## ライセンス
MIT License

- 開発ログはこちら → [Qiita: ハム二郎の学習記録](https://qiita.com/Hamziro_dev)