from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ImageMetadata(BaseModel):
    """画像メタデータ（アップロード用）"""
    name: str = Field(..., description="画像名（必須）")
    description: Optional[str] = Field(None, description="画像の説明")
    tags: Optional[str] = Field(None, description="タグ（カンマ区切り）")


class ImageUploadResponse(BaseModel):
    """画像アップロードのレスポンス"""
    image_id: str = Field(..., description="画像ID")
    image_url: str = Field(..., description="S3画像URL")
    message: str = Field(default="画像を登録しました")


class ImageDetail(BaseModel):
    """画像詳細情報"""
    image_id: str
    image_url: str
    file_name: str
    file_size: int
    mime_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    name: str
    description: Optional[str] = None
    tags: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None


class SearchResponse(BaseModel):
    """文章検索のレスポンス"""
    results: List[ImageDetail] = Field(default_factory=list)
    total: int = Field(..., description="結果の総数")


class ImageListResponse(BaseModel):
    """画像一覧のレスポンス"""
    images: List[ImageDetail] = Field(default_factory=list)
    total: int = Field(..., description="総画像数")
    page: int = Field(..., description="現在のページ")
    limit: int = Field(..., description="1ページあたりの件数")


class HealthResponse(BaseModel):
    """ヘルスチェックレスポンス"""
    status: str = "healthy"
    version: str = "0.1.0"


class ErrorResponse(BaseModel):
    """エラーレスポンス"""
    error: dict = Field(..., description="エラー詳細")
