# Terao Nav Admin

寺尾ナビゲーション管理システムのバックエンド（管理システム）です。

## 概要

Djangoで構築された管理システムで、企業・ユーザー・アプリケーション・マニュアル管理機能を提供します。

## 技術スタック

- バックエンド: Django 4.2.27
- データベース: MySQL 8.0
- ストレージ: MinIO（S3互換）
- コンテナ: Docker / Docker Compose
- 言語: Python 3.12

## 必要な環境

- Docker Desktop（Windows/Mac）または Docker Engine（Linux）
- Docker Compose

## プロジェクト構成

```
terao_navi_web/
├── applications/                     # アプリケーション管理モジュール
├── companies/                        # 企業管理モジュール
├── manuals/                          # マニュアル管理モジュール
├── tags/                             # タグ管理モジュール
├── users/                            # ユーザー管理モジュール
├── terao_navi_web/                   # プロジェクト設定
├── templates/                        # HTMLテンプレート
├── docs/                             # 画面操作ドキュメント
├── docker/                           # Dockerファイル
├── local_setting/                    # ローカル開発用設定
├── local_data/                       # ローカルデータ保存用
├── docker-compose-only-admin.yml     # 管理システム単体起動用設定
├── docker-compose-connect-other.yml  # 外部API連携用設定
├── manage.py                         # Django管理コマンド
└── requirements.txt                  # Python依存パッケージ
```

## セットアップ

### リポジトリのクローン

```bash
git clone <repository-url>
cd terao_navi_web
```

## 起動オプション（前提）

本プロジェクトは、用途に応じて2つの起動方法（オプションA / B）を選べます。

- オプションA: 管理システム単体で起動します（DB / S3 / Web / phpMyAdmin をこのComposeで起動）。
- オプションB: 外部APIサーバー（terao_navi_api）のネットワークに接続して起動します（外部API側のDB/S3を利用）。※ 外部APIサーバーが事前に起動している必要があります。

## オプションA: 管理システム単体で起動（推奨）

### 起動

```powershell
docker compose -f docker-compose-only-admin.yml up
```

起動するサービス:
- navi-admin-db（MySQL）: ポート `33307`
- navi-admin-web（Django）: ポート `8004`
- navi-admin-s3（MinIO）: ポート `9000`（API）, `9001`（コンソール）
- phpmyadmin: ポート `8013`

### データベースのマイグレーション

初回起動時、またはモデル変更後に実行します。

マイグレーションファイル作成:
```powershell
docker compose -f docker-compose-only-admin.yml exec navi-admin-web python manage.py makemigrations
```

マイグレーション実行:
```powershell
docker compose -f docker-compose-only-admin.yml exec navi-admin-web python manage.py migrate
```

### スーパーユーザー作成

```powershell
docker compose -f docker-compose-only-admin.yml exec navi-admin-web python manage.py createsuperuser
```

### アクセス先

- Django管理画面: http://localhost:8004/admin/
- Djangoアプリケーション: http://localhost:8004/
- MinIOコンソール: http://localhost:9001/（ユーザー: `minioadmin`, パスワード: `minioadmin`）
- phpMyAdmin: http://localhost:8013/（ユーザー: `root`, パスワード: `rootpassword`）

### 開発時によく使うコマンド

停止:
```powershell
docker compose -f docker-compose-only-admin.yml stop
```

起動（再起動）:
```powershell
docker compose -f docker-compose-only-admin.yml start
```

完全削除:
```powershell
docker compose -f docker-compose-only-admin.yml down
```

データも削除する場合:
```powershell
docker compose -f docker-compose-only-admin.yml down -v
```

ログ（全サービス）:
```powershell
docker compose -f docker-compose-only-admin.yml logs -f
```

ログ（navi-admin-web）:
```powershell
docker compose -f docker-compose-only-admin.yml logs -f navi-admin-web
```

Djangoコマンド:
```powershell
docker compose -f docker-compose-only-admin.yml exec navi-admin-web python manage.py <command>
```

例:
```powershell
docker compose -f docker-compose-only-admin.yml exec navi-admin-web python manage.py makemigrations
docker compose -f docker-compose-only-admin.yml exec navi-admin-web python manage.py shell
docker compose -f docker-compose-only-admin.yml exec navi-admin-web python manage.py collectstatic
```

データベース接続:

phpMyAdmin:
- URL: http://localhost:8013/
- ユーザー: `root`
- パスワード: `rootpassword`

MySQLクライアント:
```powershell
docker compose -f docker-compose-only-admin.yml exec navi-admin-db mysql -u navi_admin_user -ppassword db_local
```

### 環境変数（docker-compose-only-admin.yml）

データベース（navi-admin-db）:

- `MYSQL_ROOT_PASSWORD`: rootpassword
- `MYSQL_DATABASE`: db_local
- `MYSQL_USER`: navi_admin_user
- `MYSQL_PASSWORD`: password

Django（navi-admin-web）:

- `DJANGO_SETTINGS_MODULE`: terao_navi_web.settings
- `PYTHONUNBUFFERED`: 1
- `DB_HOST`: navi-admin-db
- `AWS_S3_ENDPOINT_URL`: http://navi-admin-s3:9000
- `AWS_ACCESS_KEY_ID`: minioadmin
- `AWS_SECRET_ACCESS_KEY`: minioadmin

MinIO（navi-admin-s3）:

- `MINIO_ROOT_USER`: minioadmin
- `MINIO_ROOT_PASSWORD`: minioadmin

### データの永続化

以下のディレクトリにデータが永続化されます。

- `./local_data/mysql`: MySQLデータ
- `./local_data/minio`: MinIO（S3）データ

これらのディレクトリは `.gitignore` に含めることを推奨します。

### トラブルシューティング

ポートの競合:

ポートが既に使用されている場合は、`docker-compose-only-admin.yml` のポート番号を変更してください。

データベース接続エラー:

データベースの起動を待機してください。以下のコマンドでヘルスチェックを確認できます。

```powershell
docker compose -f docker-compose-only-admin.yml ps
```

コンテナの再ビルド:

キャッシュをクリアして再ビルドする場合:

```powershell
docker compose -f docker-compose-only-admin.yml build --no-cache
docker compose -f docker-compose-only-admin.yml up -d
```

## オプションB: 外部API環境に接続して起動

### 起動

既存の外部APIサーバー（terao_navi_api）のネットワークに接続して起動します。
※ 事前に外部APIサーバーが起動している必要があります。

```powershell
docker compose -f docker-compose-connect-other.yml up
```

起動するサービス:
- navi_admin_web（Django）: ポート `8004`
- 外部ネットワーク `terao_navi_api_navi-api-network` に接続

### データベースのマイグレーション

別プロジェクトでマイグレーション済み。

### スーパーユーザー作成

```powershell
docker compose -f docker-compose-connect-other.yml exec navi_admin_web python manage.py createsuperuser
```

### アクセス先

- Django管理画面: http://localhost:8004/admin/
- Djangoアプリケーション: http://localhost:8004/
- ※ MinIO と DB は外部APIサーバーのものを使用

### 開発時によく使うコマンド

停止:
```powershell
docker compose -f docker-compose-connect-other.yml stop
```

起動（再起動）:
```powershell
docker compose -f docker-compose-connect-other.yml start
```

完全削除:
```powershell
docker compose -f docker-compose-connect-other.yml down
```

データも削除する場合:
```powershell
docker compose -f docker-compose-connect-other.yml down -v
```

ログ（全サービス）:
```powershell
docker compose -f docker-compose-connect-other.yml logs -f
```

ログ（navi_admin_web）:
```powershell
docker compose -f docker-compose-connect-other.yml logs -f navi_admin_web
```

Djangoコマンド:
```powershell
docker compose -f docker-compose-connect-other.yml exec navi_admin_web python manage.py <command>
```

例:
```powershell
docker compose -f docker-compose-connect-other.yml exec navi_admin_web python manage.py makemigrations
docker compose -f docker-compose-connect-other.yml exec navi_admin_web python manage.py shell
docker compose -f docker-compose-connect-other.yml exec navi_admin_web python manage.py collectstatic
```

データベース接続:

外部APIサーバーのデータベースを使用します。

### 環境変数（docker-compose-connect-other.yml）

Django（navi_admin_web）:

- `DJANGO_SETTINGS_MODULE`: terao_navi_web.settings
- `PYTHONUNBUFFERED`: 1
- `AWS_S3_ENDPOINT_URL`: http://navi-api-s3:9000（外部APIサーバー）
- `AWS_ACCESS_KEY_ID`: dummy
- `AWS_SECRET_ACCESS_KEY`: dummy123

### データの永続化

データは外部APIサーバーで管理されます。

### トラブルシューティング

ポートの競合:

ポートが既に使用されている場合は、`docker-compose-connect-other.yml` のポート番号を変更してください。

データベース接続エラー:

データベースの起動を待機してください。以下のコマンドでヘルスチェックを確認できます。

```powershell
docker compose -f docker-compose-connect-other.yml ps
```

コンテナの再ビルド:

キャッシュをクリアして再ビルドする場合:

```powershell
docker compose -f docker-compose-connect-other.yml build --no-cache
docker compose -f docker-compose-connect-other.yml up -d
```

