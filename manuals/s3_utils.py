import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from django.conf import settings


def get_s3_client():
    """S3クライアントを取得"""
    # boto3のセッションを作成
    session = boto3.session.Session()
    
    return session.client(
        's3',
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        config=Config(signature_version='s3v4'),
        region_name=settings.AWS_S3_REGION_NAME,
        use_ssl=settings.AWS_S3_USE_SSL,
    )


def ensure_bucket_exists():
    """バケットが存在しない場合は作成"""
    s3_client = get_s3_client()
    try:
        s3_client.head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
    except ClientError:
        # バケットが存在しない場合は作成
        try:
            s3_client.create_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
        except ClientError as e:
            print(f"Error creating bucket: {e}")
            raise


def upload_file_to_s3(file, company_id, application_id, filename):
    """
    ファイルをS3にアップロード
    
    Args:
        file: アップロードするファイルオブジェクト
        company_id: 会社ID（後方互換性のため残すが使用しない）
        application_id: アプリケーションID
        filename: ファイル名
    
    Returns:
        str: S3内のファイルパス
    """
    ensure_bucket_exists()
    
    # S3内のパスを生成: application_id/filename (バケット名がmanualsなので、パスにmanualsは不要)
    s3_key = f"{application_id}/{filename}"
    
    s3_client = get_s3_client()
    try:
        s3_client.upload_fileobj(
            file,
            settings.AWS_STORAGE_BUCKET_NAME,
            s3_key,
            ExtraArgs={'ContentType': 'application/pdf'}
        )
        return s3_key
    except ClientError as e:
        print(f"Error uploading file: {e}")
        raise


def download_file_from_s3(s3_key):
    """
    S3からファイルをダウンロード
    
    Args:
        s3_key: S3内のファイルパス
    
    Returns:
        bytes: ファイルの内容
    """
    s3_client = get_s3_client()
    try:
        response = s3_client.get_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=s3_key
        )
        return response['Body'].read()
    except ClientError as e:
        print(f"Error downloading file: {e}")
        raise


def delete_file_from_s3(s3_key):
    """
    S3からファイルを削除
    
    Args:
        s3_key: S3内のファイルパス
    """
    s3_client = get_s3_client()
    try:
        s3_client.delete_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=s3_key
        )
    except ClientError as e:
        print(f"Error deleting file: {e}")
        raise


def get_file_url(s3_key, expiration=3600):
    """
    S3ファイルの署名付きURLを生成
    
    Args:
        s3_key: S3内のファイルパス
        expiration: URL有効期限（秒）
    
    Returns:
        str: 署名付きURL
    """
    s3_client = get_s3_client()
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': s3_key
            },
            ExpiresIn=expiration
        )
        return url
    except ClientError as e:
        print(f"Error generating presigned URL: {e}")
        raise
