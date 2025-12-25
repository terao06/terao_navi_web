import boto3
import secrets
import hashlib
from datetime import datetime
from django.conf import settings


def get_dynamodb_client():
    """DynamoDBクライアントを取得"""
    return boto3.client(
        'dynamodb',
        endpoint_url=settings.DYNAMODB_ENDPOINT_URL,
        region_name=settings.DYNAMODB_REGION_NAME,
        aws_access_key_id=settings.DYNAMODB_ACCESS_KEY_ID,
        aws_secret_access_key=settings.DYNAMODB_SECRET_ACCESS_KEY
    )


def generate_client_credentials():
    """
    クライアントIDとシークレットを生成
    
    Returns:
        tuple: (client_id, client_secret, secret_hash)
    """
    # クライアントIDを生成（32文字のランダムな16進数文字列）
    client_id = secrets.token_hex(16)
    
    # クライアントシークレットを生成（64文字のランダムな16進数文字列）
    client_secret = secrets.token_hex(32)
    
    # シークレットのハッシュ値を生成（SHA-256）
    secret_hash = hashlib.sha256(client_secret.encode()).hexdigest()
    
    return client_id, client_secret, secret_hash


def create_auth_client(company_id, client_id, secret_hash):
    """
    DynamoDBのauth_clientsテーブルにクライアント情報を登録
    
    Args:
        company_id: 会社ID
        client_id: クライアントID
        secret_hash: シークレットのハッシュ値
        
    Returns:
        bool: 登録成功時True
    """
    try:
        dynamodb = get_dynamodb_client()
        table_name = f"{settings.DYNAMODB_TABLE_PREFIX}auth_clients"
        
        # 現在時刻をISO 8601形式で取得
        created_at = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # DynamoDBに登録
        dynamodb.put_item(
            TableName=table_name,
            Item={
                'client_id': {'S': client_id},
                'company_id': {'N': str(company_id)},
                'secret_hash': {'S': secret_hash},
                'is_active': {'N': '1'},
                'created_at': {'S': created_at}
            }
        )
        
        return True
    except Exception as e:
        print(f"Error creating auth client: {e}")
        return False


def verify_client_credentials(client_id, client_secret):
    """
    クライアント認証情報を検証
    
    Args:
        client_id: クライアントID
        client_secret: クライアントシークレット
        
    Returns:
        dict or None: 認証成功時にクライアント情報を返す、失敗時None
    """
    try:
        dynamodb = get_dynamodb_client()
        table_name = f"{settings.DYNAMODB_TABLE_PREFIX}auth_clients"
        
        # クライアント情報を取得
        response = dynamodb.get_item(
            TableName=table_name,
            Key={'client_id': {'S': client_id}}
        )
        
        if 'Item' not in response:
            return None
        
        item = response['Item']
        
        # アクティブチェック
        if item.get('is_active', {}).get('N') != '1':
            return None
        
        # シークレットハッシュを検証
        secret_hash = hashlib.sha256(client_secret.encode()).hexdigest()
        stored_hash = item.get('secret_hash', {}).get('S')
        
        if secret_hash != stored_hash:
            return None
        
        # クライアント情報を返す
        return {
            'client_id': item['client_id']['S'],
            'company_id': int(item['company_id']['N']),
            'is_active': int(item['is_active']['N']),
            'created_at': item['created_at']['S']
        }
    except Exception as e:
        print(f"Error verifying client credentials: {e}")
        return None


def get_client_by_company_id(company_id):
    """
    会社IDからクライアント情報を取得
    
    Args:
        company_id: 会社ID
        
    Returns:
        list: クライアント情報のリスト
    """
    try:
        dynamodb = get_dynamodb_client()
        table_name = f"{settings.DYNAMODB_TABLE_PREFIX}auth_clients"
        
        response = dynamodb.query(
            TableName=table_name,
            IndexName='idx_company_id',
            KeyConditionExpression='company_id = :company_id',
            ExpressionAttributeValues={
                ':company_id': {'N': str(company_id)}
            }
        )
        
        clients = []
        for item in response.get('Items', []):
            clients.append({
                'client_id': item['client_id']['S'],
                'company_id': int(item['company_id']['N']),
                'is_active': int(item['is_active']['N']),
                'created_at': item['created_at']['S']
            })
        
        return clients
    except Exception as e:
        print(f"Error getting clients by company_id: {e}")
        return []


def deactivate_client(client_id):
    """
    クライアントを無効化
    
    Args:
        client_id: クライアントID
        
    Returns:
        bool: 無効化成功時True
    """
    try:
        dynamodb = get_dynamodb_client()
        table_name = f"{settings.DYNAMODB_TABLE_PREFIX}auth_clients"
        
        dynamodb.update_item(
            TableName=table_name,
            Key={'client_id': {'S': client_id}},
            UpdateExpression='SET is_active = :inactive',
            ExpressionAttributeValues={
                ':inactive': {'N': '0'}
            }
        )
        
        return True
    except Exception as e:
        print(f"Error deactivating client: {e}")
        return False


def delete_auth_clients_by_company_id(company_id):
    """
    指定した会社IDに紐づくクライアントをDynamoDBから削除
    
    Args:
        company_id: 会社ID
        
    Returns:
        bool: 全削除が成功した場合True（1件も存在しない場合もTrue）
    """
    try:
        dynamodb = get_dynamodb_client()
        table_name = f"{settings.DYNAMODB_TABLE_PREFIX}auth_clients"

        deleted_count = 0

        # 1) GSIでのQuery（型: Number）を試す
        try:
            last_evaluated_key = None
            while True:
                params = {
                    'TableName': table_name,
                    'IndexName': 'idx_company_id',
                    'KeyConditionExpression': 'company_id = :company_id',
                    'ExpressionAttributeValues': {
                        ':company_id': {'N': str(company_id)}
                    }
                }
                if last_evaluated_key:
                    params['ExclusiveStartKey'] = last_evaluated_key

                response = dynamodb.query(**params)
                items = response.get('Items', [])
                for item in items:
                    client_id = item['client_id']['S']
                    dynamodb.delete_item(
                        TableName=table_name,
                        Key={'client_id': {'S': client_id}}
                    )
                    deleted_count += 1

                last_evaluated_key = response.get('LastEvaluatedKey')
                if not last_evaluated_key:
                    break
        except Exception as e:
            # GSIが存在しない、型不一致などの場合はスキャンにフォールバック
            print(f"Fallback to scan (query failed): {e}")

        # 2) GSIで削除できなかった場合、Scanでの削除（型: Number）
        if deleted_count == 0:
            last_evaluated_key = None
            while True:
                params = {
                    'TableName': table_name,
                    'FilterExpression': 'company_id = :company_id',
                    'ExpressionAttributeValues': {
                        ':company_id': {'N': str(company_id)}
                    }
                }
                if last_evaluated_key:
                    params['ExclusiveStartKey'] = last_evaluated_key

                response = dynamodb.scan(**params)
                items = response.get('Items', [])
                for item in items:
                    client_id = item['client_id']['S']
                    dynamodb.delete_item(
                        TableName=table_name,
                        Key={'client_id': {'S': client_id}}
                    )
                    deleted_count += 1

                last_evaluated_key = response.get('LastEvaluatedKey')
                if not last_evaluated_key:
                    break

        # 3) さらに型が文字列の場合のフォールバック（過去データの型ぶれ対応）
        if deleted_count == 0:
            last_evaluated_key = None
            while True:
                params = {
                    'TableName': table_name,
                    'FilterExpression': 'company_id = :company_id',
                    'ExpressionAttributeValues': {
                        ':company_id': {'S': str(company_id)}
                    }
                }
                if last_evaluated_key:
                    params['ExclusiveStartKey'] = last_evaluated_key

                response = dynamodb.scan(**params)
                items = response.get('Items', [])
                for item in items:
                    client_id = item['client_id']['S']
                    dynamodb.delete_item(
                        TableName=table_name,
                        Key={'client_id': {'S': client_id}}
                    )
                    deleted_count += 1

                last_evaluated_key = response.get('LastEvaluatedKey')
                if not last_evaluated_key:
                    break

        # 対象がなくても削除成功として扱う
        return True
    except Exception as e:
        print(f"Error deleting auth clients by company_id({company_id}): {e}")
        return False
