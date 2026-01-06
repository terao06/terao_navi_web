#!/usr/bin/env bash
set -euo pipefail

# ===== 設定（compose の environment から上書きされます）=====
ENDPOINT="${DDB_ENDPOINT:-http://navi-dynamodb:8000}"
REGION="${AWS_REGION:-ap-northeast-1}"
TABLE_PREFIX="${DDB_TABLE_PREFIX:-}"

# ===== テーブル名 =====
ASM_TABLE="${TABLE_PREFIX}agent_session_messages"
ASS_TABLE="${TABLE_PREFIX}agent_session_states"

echo "[init] endpoint=${ENDPOINT} region=${REGION} prefix=${TABLE_PREFIX}"

# ----- DynamoDB Local 起動待ち -----
echo "[init] waiting for DynamoDB..."
for i in {1..60}; do
  if aws dynamodb list-tables --endpoint-url "${ENDPOINT}" --region "${REGION}" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

# =========================
# auth_clients
# =========================
AUTH_TABLE="${TABLE_PREFIX}auth_clients"

if aws dynamodb describe-table \
    --table-name "${AUTH_TABLE}" \
    --endpoint-url "${ENDPOINT}" --region "${REGION}" >/dev/null 2>&1; then
  echo "[init] table exists: ${AUTH_TABLE}"
else
  echo "[init] creating table: ${AUTH_TABLE}"
  aws dynamodb create-table \
    --table-name "${AUTH_TABLE}" \
    --billing-mode PAY_PER_REQUEST \
    --attribute-definitions \
      AttributeName=client_id,AttributeType=S \
      AttributeName=company_id,AttributeType=N \
    --key-schema \
      AttributeName=client_id,KeyType=HASH \
    --global-secondary-indexes '[
      {
        "IndexName": "idx_company_id",
        "KeySchema": [{"AttributeName":"company_id","KeyType":"HASH"}],
        "Projection": {"ProjectionType":"ALL"}
      }
    ]' \
    --endpoint-url "${ENDPOINT}" --region "${REGION}"
  echo "[init] created: ${AUTH_TABLE}"
fi

echo "[init] done."
