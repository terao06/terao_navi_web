# Terao Nav Admin

寺尾ナビゲーション管理システムのバックエンドアプリケーション

## 概要

このアプリケーションはDjangoで構築された管理システムです。企業、ユーザー、アプリケーション、マニュアル管理機能を提供します。

## 技術スタック

- **バックエンド**: Django 4.2.27
- **データベース**: MySQL 8.0
- **ストレージ**: MinIO (S3互換)
- **コンテナ化**: Docker & Docker Compose
- **言語**: Python 3.12

## 必要な環境

- Docker Desktop (Windows/Mac) または Docker Engine (Linux)
- Docker Compose

## プロジェクト構成

```
terao_navi_web/
├── applications/          # アプリケーション管理モジュール
├── companies/             # 企業管理モジュール
├── manuals/              # マニュアル管理モジュール
├── users/                # ユーザー管理モジュール
├── terao_navi_web/      # プロジェクト設定
├── templates/            # HTMLテンプレート
├── docker/               # Dockerファイル
├── local_setting/        # ローカル開発用設定
├── local_data/           # ローカルデータ保存用
├── docker-compose.yml    # Docker Compose設定
├── manage.py             # Django管理コマンド
└── requirements.txt      # Python依存パッケージ
```

## セットアップと実行手順

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd terao_navi_web
```

### 2. Dockerコンテナの起動

```powershell
docker-compose up -d --build
```

このコマンドで以下のサービスが起動します：
- **navi_admin_db** (MySQL): ポート `33307`
- **navi_admin_web** (Django): ポート `8004`
- **navi_admin_s3** (MinIO): ポート `9000` (API), `9001` (コンソール)
- **phpmyadmin**: ポート `8013`

### 3. データベースのマイグレーション

初回起動時、またはモデル変更後にマイグレーションを実行します：

```powershell
docker-compose exec navi_admin_web python manage.py migrate
```

### 4. スーパーユーザーの作成

管理画面にアクセスするためのスーパーユーザーを作成します：

```powershell
docker-compose exec navi_admin_web python manage.py createsuperuser
```

### 5. アプリケーションへのアクセス

- **Django管理画面**: http://localhost:8004/admin/
- **Django アプリケーション**: http://localhost:8004/
- **MinIOコンソール**: http://localhost:9001/ (ユーザー: `minioadmin`, パスワード: `minioadmin`)
- **phpMyAdmin**: http://localhost:8013/ (ユーザー: `root`, パスワード: `rootpassword`)

## 開発時のコマンド

### コンテナの停止

```powershell
docker-compose stop
```

### コンテナの起動（再起動）

```powershell
docker-compose start
```

### コンテナの完全削除

```powershell
docker-compose down
```

データも削除する場合：

```powershell
docker-compose down -v
```

### ログの確認

全サービスのログ：
```powershell
docker-compose logs -f
```

特定のサービスのログ：
```powershell
docker-compose logs -f navi_admin_web
```

### Djangoコマンドの実行

コンテナ内でDjangoコマンドを実行する場合：

```powershell
docker-compose exec navi_admin_web python manage.py <command>
```

例：
- マイグレーションファイルの作成: `docker-compose exec navi_admin_web python manage.py makemigrations`
- シェルの起動: `docker-compose exec navi_admin_web python manage.py shell`
- 静的ファイルの収集: `docker-compose exec navi_admin_web python manage.py collectstatic`

### データベースへの接続

phpMyAdmin経由:
- URL: http://localhost:8013/
- ユーザー: `root`
- パスワード: `rootpassword`

またはMySQLクライアント:
```powershell
docker-compose exec navi_admin_db mysql -u navi_admin_user -ppassword db_local
```

## 環境変数

主要な環境変数は`docker-compose.yml`で設定されています：

### データベース (navi_admin_db)
- `MYSQL_ROOT_PASSWORD`: rootpassword
- `MYSQL_DATABASE`: db_local
- `MYSQL_USER`: navi_admin_user
- `MYSQL_PASSWORD`: password

### Django (navi_admin_web)
- `DJANGO_SETTINGS_MODULE`: terao_navi_web.settings
- `PYTHONUNBUFFERED`: 1

### MinIO (navi_admin_s3)
- `MINIO_ROOT_USER`: minioadmin
- `MINIO_ROOT_PASSWORD`: minioadmin

## データの永続化

以下のディレクトリにデータが永続化されます：

- `./local_data/mysql`: MySQLデータ
- `./local_data/minio`: MinIO（S3）データ

これらのディレクトリは`.gitignore`に含めることを推奨します。

## トラブルシューティング

### ポートの競合

もしポートが既に使用されている場合は、`docker-compose.yml`のポート番号を変更してください。

### データベース接続エラー

データベースの起動を待機してください。以下のコマンドでヘルスチェックを確認できます：

```powershell
docker-compose ps
```

### コンテナの再ビルド

キャッシュをクリアして再ビルドする場合：

```powershell
docker-compose build --no-cache
docker-compose up -d
```

## ライセンス

[ライセンス情報を記載]

## 連絡先

[連絡先情報を記載]
