from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Optional
from uuid import uuid4

from app.models.schemas import ImageUploadResponse, ImageMetadata
from app.services.image_processor import image_processor
from app.services.s3_service import s3_service
from app.services.vector_store import vector_store
from app.config import settings

router = APIRouter(prefix="/api", tags=["images"])


@router.post("/images", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(..., description="アップロードする画像ファイル"),
    name: Optional[str] = Form(None, description="画像名"),
    description: Optional[str] = Form(None, description="画像説明"),
    tags: Optional[str] = Form(None, description="タグ（カンマ区切り）"),
):
    """
    画像をアップロードして登録

    - 画像をS3にアップロード
    - 特徴ベクトルを抽出
    - ベクトルストアに登録
    """
    try:
        # ファイルを読み込み
        image_bytes = await file.read()

        # 画像のバリデーション
        image_processor.validate_image(image_bytes, settings.MAX_IMAGE_SIZE)

        # ユニークIDを生成
        image_id = uuid4()

        # 特徴ベクトルを抽出
        feature_vector = image_processor.extract_features(image_bytes)

        # S3にアップロード
        content_type = file.content_type or "image/jpeg"
        image_url = s3_service.upload_image(image_bytes, image_id, content_type)

        # メタデータを作成
        tag_list = [tag.strip() for tag in tags.split(",")] if tags else []
        metadata = ImageMetadata(name=name, description=description, tags=tag_list)

        # ベクトルストアに登録
        vector_store.add_vector(image_id, feature_vector, metadata, image_url)

        return ImageUploadResponse(
            image_id=image_id,
            image_url=image_url,
            message="画像が正常にアップロードされました",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"画像アップロードに失敗しました: {str(e)}")
