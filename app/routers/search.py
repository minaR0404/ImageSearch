from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.models.schemas import SearchResponse, ImageDetail
from app.services.db_service import db_service
from app.services.s3_service import s3_service

router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search", response_model=SearchResponse)
async def search_images(
    query: str = Query(..., min_length=1, description="検索キーワード"),
    limit: int = Query(10, ge=1, le=100, description="返す結果の最大数"),
):
    """
    文章検索で画像を検索

    - SQLite FTS5を使った全文検索
    - 名前、説明、タグから検索
    - 関連度順に結果を返す
    """
    try:
        # 全文検索を実行
        search_results = db_service.search_images(query=query, limit=limit)

        # ImageDetailに変換
        results = []
        for img_data in search_results:
            # S3のURLを生成
            image_url = s3_service.get_presigned_url(img_data['s3_key'])

            results.append(ImageDetail(
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

        return SearchResponse(results=results, total=len(results))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"検索に失敗しました: {str(e)}")
