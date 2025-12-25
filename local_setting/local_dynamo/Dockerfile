# ./local-setting/local-dynamo/Dockerfile
FROM amazon/dynamodb-local:latest

LABEL maintainer="you@example.com" \
      org.opencontainers.image.title="navi_dynamodb" \
      org.opencontainers.image.description="DynamoDB Local for navi local dev"

# デフォルトの作業ディレクトリは /home/dynamodblocal
WORKDIR /home/dynamodblocal

# 永続化用ディレクトリ
RUN mkdir -p /home/dynamodblocal/data

# デフォルトの公開ポート
EXPOSE 8000

# データ永続化（任意）
VOLUME ["/home/dynamodblocal/data"]

# 既定は共有DB + 永続化パス
# ※ Compose の services.teraid-dynamodb.command で
#    ["-jar","DynamoDBLocal.jar","-inMemory","-sharedDb"] のように上書き可能
CMD ["-jar", "DynamoDBLocal.jar", "-sharedDb", "-dbPath", "/home/dynamodblocal/data"]
