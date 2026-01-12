# 画像管理・文章検索システム 仕様書

## 1. システム概要

### 1.1 目的
ユーザーが画像をアップロードしてメタデータ（名前、説明、タグ）と共に保存し、文章検索によって関連画像を見つけられるシステムを構築する。

### 1.2 デプロイ環境
- AWS App Runner を使用したコンテナベースのデプロイ
- サーバーレスアーキテクチャで自動スケーリング対応

## 2. システム構成

### 2.1 技術スタック

#### バックエンド
- **言語**: Python 3.11+
- **フレームワーク**: FastAPI
- **画像処理**: Pillow (基本的な画像処理のみ)
- **文章検索**: SQLiteのFTS5（全文検索）
- **データベース**: SQLite（ローカルファイル、シンプル）
- **ストレージ**: Amazon S3 (画像ファイル保存)

#### フロントエンド (Phase 1: 簡易版)
- **HTML/CSS/JavaScript** (バニラJS、フレームワークなし)
- **静的ファイル配信**: FastAPIのStaticFilesミドルウェア
- **スタイリング**: シンプルなCSS
- **機能**:
  - ドラッグ&ドロップ画像アップロード
  - 画像プレビュー
  - テキスト検索フォーム
  - 検索結果のグリッド表示

#### インフラ
- **コンテナ**: Docker
- **デプロイ**: AWS App Runner
- **画像ストレージ**: Amazon S3

### 2.2 アーキテクチャ図

```
[ユーザー]
    ↓ (画像アップロード + メタデータ)
[FastAPI Application on App Runner]
    ↓ ↓
    |  └→ [S3] 画像保存
    └→ [SQLite] メタデータ保存・検索
    ↓
[検索結果] → [ユーザー]
```

## 3. 機能要件

### 3.1 画像登録機能
- **エンドポイント**: `POST /api/images`
- **入力**:
  - 画像ファイル (JPEG, PNG形式、最大10MB)
  - メタデータ:
    - `name` (必須): 画像の名前
    - `description` (任意): 画像の説明
    - `tags` (任意): カンマ区切りのタグ
- **処理フロー**:
  1. 画像をバリデーション
  2. S3にアップロード
  3. メタデータをSQLiteに保存
- **出力**: 登録された画像ID、URL

### 3.2 文章検索機能
- **エンドポイント**: `GET /api/search`
- **入力**:
  - `query`: 検索キーワード（名前、説明、タグから検索）
  - `limit` (オプション): 検索件数 (デフォルト: 10件)
- **処理フロー**:
  1. SQLiteでFTS5全文検索を実行
  2. 名前、説明、タグからマッチする画像を抽出
  3. 結果を関連度順にソート
- **出力**:
  ```json
  {
    "results": [
      {
        "image_id": "uuid",
        "image_url": "s3_url",
        "name": "画像名",
        "description": "説明",
        "tags": "tag1,tag2",
        "created_at": "2025-01-01T00:00:00Z"
      }
    ]
  }
  ```

### 3.3 画像一覧取得機能
- **エンドポイント**: `GET /api/images`
- **入力**:
  - ページネーション (page, limit)
  - フィルター (タグ、日付範囲)
- **出力**: 登録画像のリスト

### 3.4 画像削除機能
- **エンドポイント**: `DELETE /api/images/{image_id}`
- **処理フロー**:
  1. SQLiteから削除
  2. S3から削除

### 3.5 ヘルスチェック
- **エンドポイント**: `GET /health`
- **出力**: システムステータス

## 4. 非機能要件

### 4.1 パフォーマンス
- 文章検索レスポンス時間: 1秒以内
- 画像登録処理時間: 3秒以内
- 同時接続数: 50リクエスト/秒に対応

### 4.2 セキュリティ
- HTTPS通信のみ許可
- S3バケットのプライベート設定 + 署名付きURL

### 4.3 可用性
- App Runnerの自動スケーリング
- S3の99.999999999%の耐久性

### 4.4 監視・ログ
- CloudWatch Logs でアプリケーションログ収集
- CloudWatch Metrics でメトリクス監視
  - リクエスト数
  - レスポンスタイム
  - エラー率

## 5. データモデル

### 5.1 画像メタデータ (SQLite)

```sql
-- メインテーブル
CREATE TABLE images (
    image_id TEXT PRIMARY KEY,
    s3_key TEXT NOT NULL,
    s3_bucket TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type TEXT NOT NULL,
    width INTEGER,
    height INTEGER,
    name TEXT NOT NULL,
    description TEXT,
    tags TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_images_created_at ON images(created_at);
CREATE INDEX idx_images_name ON images(name);
CREATE INDEX idx_images_tags ON images(tags);

-- FTS5テーブル（全文検索用）
CREATE VIRTUAL TABLE images_fts USING fts5(
    image_id UNINDEXED,
    name,
    description,
    tags,
    content='images',
    content_rowid='rowid'
);

-- FTS5テーブルを自動更新するトリガー
CREATE TRIGGER images_ai AFTER INSERT ON images BEGIN
  INSERT INTO images_fts(rowid, image_id, name, description, tags)
  VALUES (new.rowid, new.image_id, new.name, new.description, new.tags);
END;

CREATE TRIGGER images_ad AFTER DELETE ON images BEGIN
  INSERT INTO images_fts(images_fts, rowid, image_id, name, description, tags)
  VALUES('delete', old.rowid, old.image_id, old.name, old.description, old.tags);
END;

CREATE TRIGGER images_au AFTER UPDATE ON images BEGIN
  INSERT INTO images_fts(images_fts, rowid, image_id, name, description, tags)
  VALUES('delete', old.rowid, old.image_id, old.name, old.description, old.tags);
  INSERT INTO images_fts(rowid, image_id, name, description, tags)
  VALUES (new.rowid, new.image_id, new.name, new.description, new.tags);
END;
```

## 6. App Runner 設定

### 6.1 Dockerファイル要件
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# システムパッケージのインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# uvインストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 依存関係インストール
COPY pyproject.toml ./
RUN uv sync --no-dev

# アプリケーションコピー
COPY app ./app
COPY static ./static

# データベースディレクトリ作成
RUN mkdir -p /app/data

# ポート公開
EXPOSE 8000

# 起動コマンド
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 6.2 App Runner 構成
- **CPU**: 0.25 vCPU
- **メモリ**: 0.5 GB
- **ポート**: 8000
- **自動スケーリング**:
  - 最小インスタンス: 1
  - 最大インスタンス: 5
  - 同時実行数: 50
- **環境変数**:
  - `S3_BUCKET_NAME`: 画像保存用バケット名
  - `AWS_REGION`: リージョン

### 6.3 IAMロール権限
App Runnerインスタンスロールに以下の権限が必要:
- S3: `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject`
- CloudWatch: ログ書き込み権限

## 7. フロントエンド仕様 (Phase 1)

### 7.1 ディレクトリ構成
```
/static
  ├── index.html       # メインページ
  ├── css
  │   └── style.css   # スタイルシート
  └── js
      └── app.js      # アプリケーションロジック
```

### 7.2 画面構成

#### メイン画面
```
+----------------------------------+
|   画像管理・検索システム          |
+----------------------------------+
| [画像を登録]  [画像を検索]        |
+----------------------------------+
|
| 【登録モード】
| +----------------------------+
| | 画像をドラッグ&ドロップ     |
| | またはクリックして選択      |
| +----------------------------+
| 名前: [___________________]
| 説明: [___________________]
| タグ: [___________________]
| [登録する]
|
| 【検索モード】
| 検索: [___________________] [検索]
|
| 【検索結果】
| +------+ +------+ +------+
| | 画像1| | 画像2| | 画像3|
| | 名前 | | 名前 | | 名前 |
| +------+ +------+ +------+
+----------------------------------+
```

### 7.3 主要機能

#### 画像登録
- ドラッグ&ドロップまたはファイル選択
- 画像プレビュー表示
- メタデータ入力フォーム（名前、説明、タグ）
- 登録完了メッセージ

#### 文章検索
- テキスト入力フォーム
- 検索中のローディング表示
- 結果をグリッド表示（画像+名前+説明）
- 画像クリックで詳細表示

## 8. API仕様

### 8.1 エラーレスポンス
```json
{
  "error": {
    "code": "INVALID_IMAGE",
    "message": "画像形式が不正です",
    "details": "Supported formats: JPEG, PNG"
  }
}
```

## 9. テスト仕様

### 9.1 テスト戦略

#### テストフレームワーク
- **pytest**: テスト実行
- **pytest-cov**: カバレッジ測定
- **httpx**: FastAPI TestClient用

#### ディレクトリ構成
```
/tests
  ├── __init__.py
  ├── conftest.py           # テスト共通設定
  ├── test_api.py           # API統合テスト
  └── test_search.py        # 文章検索テスト
```

### 9.2 基本テスト

```python
def test_health_check(client):
    """ヘルスチェックエンドポイント"""
    response = client.get("/health")
    assert response.status_code == 200

def test_upload_image(client, test_image):
    """画像アップロード"""
    response = client.post(
        "/api/images",
        files={"file": ("test.jpg", test_image, "image/jpeg")},
        data={"name": "テスト画像", "description": "説明", "tags": "tag1,tag2"}
    )
    assert response.status_code == 200
    assert "image_id" in response.json()

def test_search_images(client):
    """文章検索"""
    response = client.get("/api/search?query=テスト")
    assert response.status_code == 200
    assert "results" in response.json()
```

## 10. プロジェクト構成

### 10.1 ディレクトリ構造

```
ImageSearch/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPIアプリケーションエントリーポイント
│   ├── config.py               # 環境変数・設定管理
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydanticモデル
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── images.py           # 画像登録API
│   │   └── search.py           # 文章検索API
│   ├── services/
│   │   ├── __init__.py
│   │   ├── image_service.py    # 画像処理
│   │   ├── s3_service.py       # S3操作
│   │   └── db_service.py       # SQLite操作
│   └── utils/
│       ├── __init__.py
│       └── validators.py       # バリデーション関数
├── static/
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api.py
│   └── test_search.py
├── data/
│   └── images.db               # SQLiteデータベース
├── .env.example                # 環境変数テンプレート
├── .gitignore
├── Dockerfile
├── pyproject.toml
├── README.md
└── SPECIFICATION.md
```

### 10.2 主要ファイルの役割

- **app/main.py**: FastAPIアプリのエントリーポイント、ルーター登録
- **app/config.py**: 環境変数（AWS認証情報、S3バケット名など）
- **app/services/image_service.py**: 画像の基本処理（リサイズ、バリデーション）
- **app/services/db_service.py**: SQLite操作（CRUD、FTS5検索）
- **app/routers/**: APIエンドポイント定義
- **.env.example**: 必要な環境変数のサンプル

## 11. 開発フェーズ

### Phase 1: MVP (最小機能)
- [ ] FastAPI基本セットアップ（既存コードの整理）
- [ ] PyTorch/ResNet50関連のコード削除
- [ ] SQLiteデータベース構築（FTS5対応）
- [ ] 画像登録機能の簡素化（ベクトル化削除）
- [ ] 文章検索機能の実装（FTS5使用）
- [ ] 簡易Webフロントエンド更新
  - [ ] 画像アップロードUI（既存）
  - [ ] 文章検索UI（新規）
  - [ ] 検索結果表示UI（既存を流用）
- [ ] pyproject.toml更新（torch/torchvision削除）
- [ ] Dockerfile軽量化
- [ ] App Runnerデプロイ

### Phase 2: 機能拡張
- [ ] タグベースフィルタリング
- [ ] ページネーション
- [ ] 画像削除機能
- [ ] 基本テスト実装

### Phase 3: 本番対応
- [ ] CloudWatch監視設定
- [ ] エラーハンドリング強化
- [ ] セキュリティ監査

## 12. コスト見積もり (月額)

### 開発環境
- App Runner: ~$5-10 (0.25 vCPU、低トラフィック、軽量化により削減)
- S3: ~$1 (10GB保存)
- **合計**: ~$6-11/月

### 本番環境 (想定: 1万リクエスト/日)
- App Runner: ~$15-25 (軽量化により削減)
- S3: ~$5 (50GB保存)
- データ転送: ~$5
- **合計**: ~$25-35/月

## 13. セキュリティ考慮事項

- [ ] 画像ファイルサイズ制限
- [ ] ファイル形式バリデーション
- [ ] S3バケットポリシー設定
- [ ] CORS設定

## 14. 今後の拡張可能性

- フロントエンドUIの改善 (React/Vue.js)
- ユーザー認証・マルチテナント対応
- 検索履歴・お気に入り機能
- RDS PostgreSQLへの移行（本番運用時）
- より高度な検索（Elasticsearchなど）
