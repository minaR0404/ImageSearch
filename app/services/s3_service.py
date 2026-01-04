import boto3
from botocore.exceptions import ClientError
from uuid import UUID
from app.config import settings


class S3Service:
    """AWS S3操作サービス"""

    def __init__(self):
        """S3クライアントを初期化"""
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        self.bucket_name = settings.S3_BUCKET_NAME

    def upload_image(
        self, image_bytes: bytes, image_id: UUID, content_type: str
    ) -> str:
        """
        画像をS3にアップロード

        Args:
            image_bytes: 画像データ（バイト形式）
            image_id: 画像のユニークID
            content_type: 画像のMIMEタイプ（例: image/jpeg）

        Returns:
            S3上の画像URL

        Raises:
            Exception: アップロードに失敗した場合
        """
        try:
            # S3キーを生成（画像IDをファイル名として使用）
            file_extension = content_type.split("/")[-1]
            s3_key = f"images/{image_id}.{file_extension}"

            # S3にアップロード
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=image_bytes,
                ContentType=content_type,
            )

            # 画像URLを生成
            image_url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"

            return image_url

        except ClientError as e:
            raise Exception(f"S3アップロードに失敗しました: {str(e)}")

    def delete_image(self, image_id: UUID, file_extension: str) -> None:
        """
        S3から画像を削除

        Args:
            image_id: 画像のユニークID
            file_extension: ファイル拡張子（例: jpg）

        Raises:
            Exception: 削除に失敗した場合
        """
        try:
            s3_key = f"images/{image_id}.{file_extension}"

            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)

        except ClientError as e:
            raise Exception(f"S3削除に失敗しました: {str(e)}")

    def get_presigned_url(self, image_id: UUID, file_extension: str, expiration: int = 3600) -> str:
        """
        署名付きURLを生成（一時的なアクセス用）

        Args:
            image_id: 画像のユニークID
            file_extension: ファイル拡張子
            expiration: URL有効期限（秒）

        Returns:
            署名付きURL

        Raises:
            Exception: URL生成に失敗した場合
        """
        try:
            s3_key = f"images/{image_id}.{file_extension}"

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
