"""
画像処理サービス

画像のバリデーション、リサイズ、基本情報の取得を担当
"""

from io import BytesIO
from PIL import Image
from typing import Tuple, Optional


class ImageService:
    """画像処理クラス"""

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_MIME_TYPES = {"image/jpeg", "image/png"}
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

    @staticmethod
    def validate_image(file_content: bytes, filename: str, mime_type: str) -> None:
        """画像ファイルをバリデーション

        Args:
            file_content: ファイル内容
            filename: ファイル名
            mime_type: MIMEタイプ

        Raises:
            ValueError: バリデーションエラー
        """
        # ファイルサイズチェック
        if len(file_content) > ImageService.MAX_FILE_SIZE:
            raise ValueError(f"ファイルサイズが大きすぎます（最大: 10MB）")

        # MIMEタイプチェック
        if mime_type not in ImageService.ALLOWED_MIME_TYPES:
            raise ValueError(f"サポートされていないファイル形式です。対応形式: JPEG, PNG")

        # 拡張子チェック
        file_ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if file_ext not in ImageService.ALLOWED_EXTENSIONS:
            raise ValueError(f"サポートされていないファイル拡張子です: {file_ext}")

        # 実際に画像として開けるかチェック
        try:
            image = Image.open(BytesIO(file_content))
            image.verify()
        except Exception as e:
            raise ValueError(f"無効な画像ファイルです: {str(e)}")

    @staticmethod
    def get_image_dimensions(file_content: bytes) -> Tuple[int, int]:
        """画像のサイズ（幅・高さ）を取得

        Args:
            file_content: ファイル内容

        Returns:
            (幅, 高さ) のタプル
        """
        try:
            image = Image.open(BytesIO(file_content))
            return image.size  # (width, height)
        except Exception:
            return (0, 0)

    @staticmethod
    def resize_image(
        file_content: bytes,
        max_width: int = 1920,
        max_height: int = 1920,
        quality: int = 85
    ) -> bytes:
        """画像をリサイズ（オプション機能）

        Args:
            file_content: ファイル内容
            max_width: 最大幅
            max_height: 最大高さ
            quality: JPEG品質（1-100）

        Returns:
            リサイズ後の画像データ
        """
        try:
            image = Image.open(BytesIO(file_content))

            # リサイズが必要かチェック
            if image.width <= max_width and image.height <= max_height:
                return file_content

            # アスペクト比を保ってリサイズ
            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            # バイト配列に変換
            output = BytesIO()
            image_format = image.format or "JPEG"
            image.save(output, format=image_format, quality=quality, optimize=True)
            return output.getvalue()

        except Exception:
            # リサイズ失敗時は元のファイルを返す
            return file_content


# グローバルインスタンス
image_service = ImageService()
