FROM python:3.11-slim

WORKDIR /app

# システムパッケージの更新と必要なライブラリをインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# uvを公式スクリプトでインストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# タイムアウトを延長
ENV UV_HTTP_TIMEOUT=300

# 依存関係ファイルをコピー
COPY pyproject.toml ./

# 依存関係をインストール
RUN uv sync --no-dev

# アプリケーションコードをコピー
COPY app ./app
COPY static ./static

# ポート8000を公開
EXPOSE 8000

# アプリケーションを起動
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
