# ImageSearch

画像検索システム - ベクトル類似度による画像検索

## 概要

ユーザーが画像をアップロードすると、データベースに登録された画像から類似画像を検索できるシステムです。
ResNet50を使用した特徴ベクトル抽出とコサイン類似度による検索を実装しています。

## 技術スタック

- **バックエンド**: FastAPI (Python 3.11+)
- **画像処理**: PyTorch + torchvision (ResNet50)
- **ストレージ**: AWS S3
- **フロントエンド**: HTML/CSS/JavaScript (バニラJS)
- **コンテナ**: Docker
- **パッケージ管理**: uv

## セットアップ

### 1. リポジトリをクローン

```bash
git clone <repository-url>
cd ImageSearch
```

### 2. 環境変数を設定

`.env.example`をコピーして`.env`を作成し、AWS認証情報を設定します。

```bash
cp .env.example .env
```

`.env`ファイルを編集:

```env
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=ap-northeast-1
S3_BUCKET_NAME=your-bucket-name
```

### 3. 依存関係をインストール

#### uvを使用する場合（推奨）

```bash
# uvをインストール（未インストールの場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 依存関係をインストール
uv pip install -r pyproject.toml
```

#### pipを使用する場合

```bash
pip install -e .
```

### 4. アプリケーションを起動

```bash
uvicorn app.main:app --reload
```

ブラウザで http://localhost:8000 にアクセスします。

## Docker

### Dockerでビルド・起動

```bash
# イメージをビルド
docker build -t image-search .

# コンテナを起動
docker run -p 8000:8000 --env-file .env image-search
```

ブラウザで http://localhost:8000 にアクセスします。

## 使い方

### 画像を登録

1. 「画像を登録」タブを選択
2. 画像をドラッグ&ドロップまたはクリックして選択
3. 名前・説明・タグ（任意）を入力
4. 「登録する」ボタンをクリック

### 画像を検索

1. 「画像を検索」タブを選択
2. 検索したい画像をドラッグ&ドロップまたはクリックして選択
3. 「検索する」ボタンをクリック
4. 類似画像が類似度スコア付きで表示されます

## API ドキュメント

FastAPIの自動生成ドキュメントが利用可能です:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要エンドポイント

#### `POST /api/images`
画像をアップロードして登録

#### `POST /api/search`
類似画像を検索

#### `GET /health`
ヘルスチェック

## プロジェクト構造

```
ImageSearch/
├── app/
│   ├── main.py                 # FastAPIアプリケーション
│   ├── config.py               # 設定管理
│   ├── models/
│   │   └── schemas.py          # Pydanticモデル
│   ├── routers/
│   │   ├── images.py           # 画像登録API
│   │   └── search.py           # 画像検索API
│   └── services/
│       ├── image_processor.py  # 画像処理・ベクトル化
│       ├── s3_service.py       # S3操作
│       └── vector_store.py     # ベクトル検索
├── static/
│   ├── index.html
│   ├── css/
│   └── js/
├── Dockerfile
├── pyproject.toml
└── README.md
```

## 開発

### テストの実行

```bash
# すべてのテストを実行
pytest

# カバレッジ付きで実行
pytest --cov=app --cov-report=html
```

## ライセンス

MIT License

## 今後の予定

- Phase 2: RDS PostgreSQL + pgvectorの統合
- Phase 3: API認証、ページネーション
- Phase 4: 本番環境対応、CI/CD
