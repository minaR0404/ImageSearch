from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Query
from typing import Optional

from app.models.schemas import ImageUploadResponse, ImageListResponse, ImageDetail
from app.services.image_service import image_service
from app.services.s3_service import s3_service
from app.services.db_service import db_service
from app.config import settings

router = APIRouter(prefix="/api", tags=["images"])


@router.post("/images", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(..., description="アップロードする画像ファイル"),
    name: str = Form(..., description="画像名（必須）"),
    description: Optional[str] = Form(None, description="画像説明"),
    tags: Optional[str] = Form(None, description="タグ（カンマ区切り）"),
):
    """
    画像をアップロードして登録

    - 画像ファイルをバリデーション
    - S3にアップロード
    - メタデータをSQLiteに保存
    """
    try:
        # ファイルを読み込み
        image_bytes = await file.read()
        filename = file.filename or "image.jpg"
        content_type = file.content_type or "image/jpeg"

        # 画像のバリデーション
        image_service.validate_image(image_bytes, filename, content_type)

        # 画像のサイズを取得
        width, height = image_service.get_image_dimensions(image_bytes)

        # S3にアップロード
        s3_key, image_url = s3_service.upload_image(
            image_bytes,
            filename,
            content_type
        )

        # データベースに登録
        image_id = db_service.create_image(
            s3_key=s3_key,
            s3_bucket=settings.S3_BUCKET_NAME,
            file_name=filename,
            file_size=len(image_bytes),
            mime_type=content_type,
            name=name,
            width=width,
            height=height,
            description=description,
            tags=tags
        )

        return ImageUploadResponse(
            image_id=image_id,
            image_url=image_url,
            message="画像が正常に登録されました"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"画像アップロードに失敗しました: {str(e)}")


@router.get("/images", response_model=ImageListResponse)
async def list_images(
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(10, ge=1, le=100, description="1ページあたりの件数"),
    tag: Optional[str] = Query(None, description="タグフィルター")
):
    """
    画像一覧を取得

    - ページネーション対応
    - タグフィルター対応
    """
    try:
        # 画像一覧を取得
        images_data = db_service.list_images(page=page, limit=limit, tag_filter=tag)
        total = db_service.count_images(tag_filter=tag)

        # ImageDetailに変換
        images = []
        for img_data in images_data:
            # S3のURLを生成
            image_url = s3_service.get_presigned_url(img_data['s3_key'])

            images.append(ImageDetail(
                image_id=img_data['image_id'],
                image_url=image_url,
                file_name=img_data['file_name'],
                file_size=img_data['file_size'],
                mime_type=img_data['mime_type'],
                width=img_data.get('width'),
                height=img_data.get('height'),
                name=img_data['name'],
                description=img_data.get('description'),
                tags=img_data.get('tags'),
                created_at=img_data['created_at'],
                updated_at=img_data.get('updated_at')
            ))

        return ImageListResponse(
            images=images,
            total=total,
            page=page,
            limit=limit
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"画像一覧の取得に失敗しました: {str(e)}")


@router.delete("/images/{image_id}")
async def delete_image(image_id: str):
    """
    画像を削除

    - データベースから削除
    - S3から削除
    """
    try:
        # 画像情報を取得
        image_data = db_service.get_image(image_id)
        if not image_data:
            raise HTTPException(status_code=404, detail="画像が見つかりません")

        # S3から削除
        s3_service.delete_image(image_data['s3_key'])

        # データベースから削除
        db_service.delete_image(image_id)

        return {"message": "画像を削除しました", "image_id": image_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"画像の削除に失敗しました: {str(e)}")
