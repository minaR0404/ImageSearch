FROM python:3.11-slim

WORKDIR /app

# システムパッケージの更新と必要なライブラリをインストール
RUN apt-get update && apt-get install -y \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# uvを公式スクリプトでインストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 依存関係ファイルをコピー
COPY pyproject.toml ./

# 依存関係をインストール
RUN uv pip install --system --no-cache -r pyproject.toml

# アプリケーションコードをコピー
COPY app ./app
COPY static ./static

# ポート8000を公開
EXPOSE 8000

# アプリケーションを起動
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
