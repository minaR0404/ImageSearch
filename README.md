# ImageSearch

画像管理・文章検索システム

## 概要

ユーザーが画像をアップロードしてメタデータ（名前、説明、タグ）と共に保存し、文章検索によって関連画像を見つけられるシステムです。
SQLite FTS5を使った全文検索により、キーワードから素早く画像を検索できます。

## 技術スタック

- **バックエンド**: FastAPI (Python 3.11+)
- **画像処理**: Pillow（基本的な画像処理のみ）
- **データベース**: SQLite + FTS5（全文検索）
- **ストレージ**: AWS S3
- **フロントエンド**: HTML/CSS/JavaScript (バニラJS)
- **コンテナ**: Docker
- **パッケージ管理**: uv

## セットアップ

### 1. リポジトリをクローン

```bash
git clone https://github.com/minaR0404/ImageSearch.git
cd ImageSearch
```

### 2. 環境変数を設定

`.env.example`をコピーして`.env`を作成し、AWS認証情報を設定します。

```bash
cp .env.example .env
```

`.env`ファイルを編集:

```env
AWS_REGION=ap-northeast-1
S3_BUCKET_NAME=your-bucket-name
```

### 3. 依存関係をインストール

#### uvを使用する場合（推奨）

```bash
# uvをインストール（未インストールの場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 依存関係をインストール
uv sync
```

#### pipを使用する場合

```bash
pip install -e .
```

### 4. アプリケーションを起動

```bash
uv run uvicorn app.main:app --reload
```

ブラウザで http://localhost:8000 にアクセスします。

## Docker

### Dockerでビルド・起動

```bash
# イメージをビルド
docker build -t imagesearch:latest .

# コンテナを起動
docker run -p 8000:8000 --env-file .env imagesearch:latest
```

ブラウザで http://localhost:8000 にアクセスします。

## 使い方

### 画像を登録

1. 「画像を登録」タブを選択
2. 画像をドラッグ&ドロップまたはクリックして選択
3. 名前（必須）・説明・タグを入力
4. 「登録する」ボタンをクリック

### 画像を検索

1. 「画像を検索」タブを選択
2. 検索キーワードを入力（例: 「猫」「風景」「かわいい動物」）
3. 「検索する」ボタンをクリック
4. 一致する画像が表示されます

検索は**名前、説明、タグ**から全文検索されます。

## API ドキュメント

FastAPIの自動生成ドキュメントが利用可能です:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要エンドポイント

#### `POST /api/images`
画像をアップロードして登録

**リクエスト:**
- `file`: 画像ファイル（JPEG, PNG）
- `name`: 画像名（必須）
- `description`: 説明（任意）
- `tags`: タグ（カンマ区切り、任意）

#### `GET /api/search?query=キーワード`
キーワードで画像を検索

**パラメータ:**
- `query`: 検索キーワード（必須）
- `limit`: 取得件数（デフォルト: 10、最大: 100）

#### `GET /api/images`
画像一覧を取得

**パラメータ:**
- `page`: ページ番号（デフォルト: 1）
- `limit`: 1ページあたりの件数（デフォルト: 10）
- `tag`: タグフィルター（任意）

#### `DELETE /api/images/{image_id}`
画像を削除

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
│   │   └── search.py           # 文章検索API
│   └── services/
│       ├── db_service.py       # SQLite操作（FTS5検索）
│       ├── image_service.py    # 画像処理
│       └── s3_service.py       # S3操作
├── static/
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
├── data/
│   └── images.db               # SQLiteデータベース
├── Dockerfile
├── deploy-to-ecr.sh            # ECRデプロイスクリプト
├── pyproject.toml
├── SPECIFICATION.md            # 詳細仕様書
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

### ローカル開発

```bash
# 開発サーバー起動（ホットリロード有効）
uv run uvicorn app.main:app --reload

# 依存関係の追加
uv add package-name

# 依存関係の更新
uv sync
```

## 特徴

### 軽量・高速
- PyTorch不要で起動が高速
- Dockerイメージサイズ: 約500MB（従来の数GBから大幅削減）
- SQLite FTS5による高速全文検索

### シンプルな構成
- 外部DBサーバー不要（SQLite使用）
- セットアップが簡単
- メンテナンスが容易

## ライセンス

MIT License

## 今後の予定

- Phase 2: タグベースフィルタリング、ページネーション改善
- Phase 3: RDS PostgreSQLへの移行（本番運用時）
- Phase 4: ユーザー認証、マルチテナント対応
- Phase 5: より高度な検索（Elasticsearch統合）
