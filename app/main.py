from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.routers import images, search
from app.models.schemas import HealthResponse
from app.config import settings

# FastAPIアプリケーションを作成
app = FastAPI(
    title="Image Search System",
    description="画像検索システム - ベクトル類似度による画像検索",
    version="0.1.0",
    debug=settings.DEBUG,
)

# CORS設定（開発環境用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では制限すべき
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターを登録
app.include_router(images.router)
app.include_router(search.router)

# 静的ファイル配信
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=FileResponse)
async def root():
    """ルートパスでindex.htmlを返す"""
    return FileResponse("static/index.html")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """ヘルスチェックエンドポイント"""
    return HealthResponse(status="healthy", version="0.1.0")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
