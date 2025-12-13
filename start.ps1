# ---------------------------------------------------------
# Learning Tracker 起動スクリプト (For Windows/WSL2)
# ---------------------------------------------------------

# 1. 実行ポリシーの変更と仮想環境の有効化
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
. .\kivyenv\Scripts\Activate.ps1

# 2. WSL2のIPアドレスを自動取得
# 複数のIPが返ってくる場合があるため、最初の1つ目を取得して整形
$wsl_ip_raw = wsl hostname -I
$wsl_ip = $wsl_ip_raw.Trim().Split(" ")[0]

# 3. 環境変数: DBホスト設定
$env:DB_HOST = $wsl_ip

# 4. 環境変数: DBパスワード設定
# 秘密ファイル (my_secrets.ps1) があればそこから読み込む
if (Test-Path ".\my_secrets.ps1") {
    . .\my_secrets.ps1
    Write-Host "Local secrets loaded." -ForegroundColor Gray
} else {
    # ファイルがない場合（採用担当者など）は仮の値をセットするか、入力を求める
    if ([string]::IsNullOrEmpty($env:DB_PASSWORD)) {
        Write-Host "Warning: DB_PASSWORD is not set." -ForegroundColor Yellow
        # $env:DB_PASSWORD = Read-Host "Please enter DB Password"
    }
}

# 5. 起動情報の表示
Write-Host "--------------------------------" -ForegroundColor Cyan
Write-Host "Target DB Host : $env:DB_HOST" -ForegroundColor Green
Write-Host "Target DB User : hamziro" -ForegroundColor Green
Write-Host "Starting Application..." -ForegroundColor Cyan
Write-Host "--------------------------------" -ForegroundColor Cyan

# 6. アプリ起動
python main.py

# 終了時に画面をすぐ閉じたくない場合はコメントアウトを外す
# Read-Host "Press Enter to close..."