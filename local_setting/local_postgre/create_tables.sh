#!/bin/bash
set -e

# PostgreSQLに接続してpgvector拡張を有効化し、テーブルを作成する
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- pgvector拡張機能の有効化
    CREATE EXTENSION IF NOT EXISTS vector;

    -- manual_vectorsテーブルの作成（LangChainのPGVectorデフォルトスキーマに準拠させつつテーブル名を指定する場合）
    -- 注意: langchain-postgresライブラリは通常、自動でテーブルを作成・管理しますが、
    -- 手動で作成する場合は以下の構成が必要です。
    -- collectionテーブルとembeddingテーブルの2つが必要です。

    CREATE TABLE IF NOT EXISTS langchain_pg_collection (
        uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name VARCHAR,
        cmetadata JSONB
    );
EOSQL
