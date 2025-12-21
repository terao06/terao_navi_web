#!/bin/sh
# busyboxでも動くようにPOSIXシェルのみで実装
set -eu

SRC_DIR="/init/local_buckets"  # バケット構成のルート（ホストからマウント）

echo "⏳ Waiting for MinIO ..."
# MinIO が応答するまで alias 設定をリトライ
until mc alias set local http://teraid-s3:9000 minioadmin minioadmin >/dev/null 2>&1; do
  sleep 1
done
echo "✅ MinIO alias set."

# CORS設定を一時ファイルに出力
cat >/tmp/cors.json <<'JSON'
[
  {
    "AllowedOrigin": ["*"],
    "AllowedMethod": ["GET","HEAD"],
    "AllowedHeader": ["*"],
    "ExposeHeader": ["ETag"],
    "MaxAgeSeconds": 3000
  }
]
JSON

if [ ! -d "$SRC_DIR" ]; then
  echo "ℹ️ Source directory not found: $SRC_DIR (nothing to create/upload)"
  exit 0
fi

created_any=false

# `local_backets` 直下の各ディレクトリ名をバケット名として扱い、内容をミラーリング
for path in "$SRC_DIR"/*; do
  [ -d "$path" ] || continue
  bucket=$(basename "$path")

  echo "🪣 Ensuring bucket exists: $bucket"
  # 既存なら成功扱い
  mc mb --ignore-existing "local/$bucket" >/dev/null 2>&1 || true

  echo "📤 Uploading objects from $path to s3://$bucket ..."
  # 変更があれば上書き、再実行しても冪等
  mc mirror --overwrite "$path" "local/$bucket" || true

  echo "🔓 Make public (anonymous GET): $bucket"
  mc anonymous set download "local/$bucket" || true

  echo "🌐 Set CORS: $bucket"
  mc cors set "local/$bucket" /tmp/cors.json || true

  created_any=true
done

if [ "$created_any" = false ]; then
  echo "ℹ️ No bucket directories found under: $SRC_DIR"
else
  echo "🎉 Buckets ensured, objects uploaded, public-read and CORS applied."
fi
