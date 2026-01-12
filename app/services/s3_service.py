import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from typing import Tuple
from app.config import settings


class S3Service:
    """AWS S3操作サービス"""

    def __init__(self):
        """S3クライアントを初期化"""
        self.s3_client = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
        )
        self.bucket_name = settings.S3_BUCKET_NAME

    def upload_image(
        self, image_bytes: bytes, filename: str, content_type: str
    ) -> Tuple[str, str]:
        """
        画像をS3にアップロード

        Args:
            image_bytes: 画像データ（バイト形式）
            filename: 元のファイル名
            content_type: 画像のMIMEタイプ（例: image/jpeg）

        Returns:
            (S3キー, 画像URL) のタプル

        Raises:
            Exception: アップロードに失敗した場合
        """
        try:
            # S3キーを生成（タイムスタンプ + ファイル名）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            s3_key = f"images/{timestamp}_{filename}"

            # S3にアップロード
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=image_bytes,
                ContentType=content_type,
            )

            # 画像URLを生成（署名付きURL）
            image_url = self.get_presigned_url(s3_key)

            return s3_key, image_url

        except ClientError as e:
            raise Exception(f"S3アップロードに失敗しました: {str(e)}")

    def delete_image(self, s3_key: str) -> None:
        """
        S3から画像を削除

        Args:
            s3_key: S3オブジェクトキー

        Raises:
            Exception: 削除に失敗した場合
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)

        except ClientError as e:
            raise Exception(f"S3削除に失敗しました: {str(e)}")

    def get_presigned_url(self, s3_key: str, expiration: int = 3600) -> str:
        """
        署名付きURLを生成（一時的なアクセス用）

        Args:
            s3_key: S3オブジェクトキー
            expiration: URL有効期限（秒）

        Returns:
            署名付きURL

        Raises:
            Exception: URL生成に失敗した場合
        """
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": s3_key},
                ExpiresIn=expiration,
            )

            return url

        except ClientError as e:
            raise Exception(f"署名付きURL生成に失敗しました: {str(e)}")


# グローバルインスタンス
s3_service = S3Service()
