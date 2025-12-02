#!/bin/bash

# ==========================================
# 設定エリア
# ==========================================
BACKUP_DIR="$HOME/backups"
DB_NAME="learning_tracker_db"
DB_USER="hamziro"
export PGPASSWORD="YOUR_DB_PASSWORD_HERE" 

# ファイル名に日付をつける (例: db_backup_20251203.sql.gz)
DATE=$(date +"%Y%m%d")
FILE_NAME="db_backup_$DATE.sql.gz"

# ==========================================
# 1. バックアップ実行 (pg_dump)
# ==========================================
# pg_dump: DBの中身をテキストとして吐き出すコマンド
# | gzip: それをパイプで繋いで圧縮する (容量節約)
echo "[INFO] Starting backup: $FILE_NAME"
pg_dump -h localhost -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/$FILE_NAME

# 結果判定 ($? は直前のコマンドの成功/失敗が入る変数)
if [ $? -eq 0 ]; then
  echo "[SUCCESS] Backup created successfully."
else
  echo "[ERROR] Backup failed!"
  exit 1
fi

# ==========================================
# 2. 古いファイルの削除 (世代管理)
# ==========================================
# 7日以上前の古いバックアップファイルを検索して削除する
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete
echo "[INFO] Old backups cleaned up."
