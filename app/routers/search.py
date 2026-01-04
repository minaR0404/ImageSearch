from fastapi import APIRouter, File, UploadFile, HTTPException, Query

from app.models.schemas import SearchResponse, SearchResult
from app.services.image_processor import image_processor
from app.services.vector_store import vector_store
from app.config import settings

router = APIRouter(prefix="/api", tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search_similar_images(
    file: UploadFile = File(..., description="検索する画像ファイル"),
    limit: int = Query(
        default=settings.DEFAULT_SEARCH_LIMIT,
        ge=1,
        le=settings.MAX_SEARCH_LIMIT,
        description="返す結果の最大数",
    ),
):
    """
    類似画像を検索

    - アップロードされた画像から特徴ベクトルを抽出
    - ベクトルストアで類似画像を検索
    - 類似度順に結果を返す
    """
    try:
        # ファイルを読み込み
        image_bytes = await file.read()

        # 画像のバリデーション
        image_processor.validate_image(image_bytes, settings.MAX_IMAGE_SIZE)

        # 特徴ベクトルを抽出
        query_vector = image_processor.extract_features(image_bytes)

        # 類似ベクトルを検索
        similar_images = vector_store.search(query_vector, top_k=limit)

        # 検索結果を構築
        results = []
        for image_id, similarity_score in similar_images:
            metadata = vector_store.get_metadata(image_id)
            image_url = vector_store.get_url(image_id)

            results.append(
                SearchResult(
                    image_id=image_id,
                    image_url=image_url,
                    similarity_score=similarity_score,
                    metadata=metadata,
                )
            )

        return SearchResponse(results=results, total=len(results))

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"画像検索に失敗しました: {str(e)}")
