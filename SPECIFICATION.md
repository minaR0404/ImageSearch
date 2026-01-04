# 画像検索システム 仕様書

## 1. システム概要

### 1.1 目的
ユーザーが画像をアップロードすることで、データベースに登録された画像から類似画像を検索し、関連情報を返すシステムを構築する。

### 1.2 デプロイ環境
- AWS App Runner を使用したコンテナベースのデプロイ
- サーバーレスアーキテクチャで自動スケーリング対応

## 2. システム構成

### 2.1 技術スタック

#### バックエンド
- **言語**: Python 3.11+
- **フレームワーク**: FastAPI
- **画像処理**: OpenCV, Pillow
- **ベクトル化**:
  - オプション1: CLIP (OpenAI)
  - オプション2: ResNet50 (事前学習済みモデル)
- **データベース**:
  - メタデータ: Amazon RDS (PostgreSQL) または Amazon DynamoDB
  - ベクトルデータ: Amazon Aurora PostgreSQL (pgvector拡張) または Pinecone
- **ストレージ**: Amazon S3 (画像ファイル保存)

#### インフラ
- **コンテナ**: Docker
- **デプロイ**: AWS App Runner
- **CI/CD**: GitHub Actions
- **画像ストレージ**: Amazon S3
- **ネットワーク**: App Runner VPC Connector (RDS接続時)

### 2.2 アーキテクチャ図

```
[ユーザー]
    ↓ (画像アップロード)
[FastAPI Application on App Runner]
    ↓ ↓ ↓
    |  |  └→ [S3] 画像保存
    |  └→ [ベクトルDB] 類似検索
    └→ [RDS/DynamoDB] メタデータ取得
    ↓
[検索結果] → [ユーザー]
```

## 3. 機能要件

### 3.1 画像登録機能
- **エンドポイント**: `POST /api/images`
- **入力**:
  - 画像ファイル (JPEG, PNG形式、最大10MB)
  - メタデータ (名前、説明、タグなど)
- **処理フロー**:
  1. 画像をバリデーション
  2. S3にアップロード
  3. 画像を特徴ベクトルに変換
  4. ベクトルDBに保存
  5. メタデータをRDS/DynamoDBに保存
- **出力**: 登録された画像ID、URL

### 3.2 画像検索機能
- **エンドポイント**: `POST /api/search`
- **入力**:
  - 検索用画像ファイル
  - 検索件数 (デフォルト: 10件)
  - 類似度閾値 (オプション)
- **処理フロー**:
  1. 検索画像を特徴ベクトルに変換
  2. ベクトルDBで類似検索 (コサイン類似度)
  3. 類似画像のメタデータを取得
  4. 結果を類似度順にソート
- **出力**:
  ```json
  {
    "results": [
      {
        "image_id": "uuid",
        "image_url": "s3_url",
        "similarity_score": 0.95,
        "metadata": {
          "name": "画像名",
          "description": "説明",
          "tags": ["tag1", "tag2"],
          "created_at": "2025-01-01T00:00:00Z"
        }
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
  1. ベクトルDBから削除
  2. RDS/DynamoDBから削除
  3. S3から削除

### 3.5 ヘルスチェック
- **エンドポイント**: `GET /health`
- **出力**: システムステータス

## 4. 非機能要件

### 4.1 パフォーマンス
- 画像検索レスポンス時間: 2秒以内
- 画像登録処理時間: 5秒以内
- 同時接続数: 100リクエスト/秒に対応

### 4.2 セキュリティ
- HTTPS通信のみ許可
- APIキー認証またはJWT認証
- 画像ファイルのウイルススキャン (オプション)
- S3バケットのプライベート設定 + 署名付きURL

### 4.3 可用性
- App Runnerの自動スケーリング
- RDSのMulti-AZ構成 (本番環境)
- S3の99.999999999%の耐久性

### 4.4 監視・ログ
- CloudWatch Logs でアプリケーションログ収集
- CloudWatch Metrics で メトリクス監視
  - リクエスト数
  - レスポンスタイム
  - エラー率
- X-Ray でトレーシング (オプション)

## 5. データモデル

### 5.1 画像メタデータ (RDS/DynamoDB)

```sql
CREATE TABLE images (
    image_id UUID PRIMARY KEY,
    s3_key VARCHAR(512) NOT NULL,
    s3_bucket VARCHAR(255) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(50) NOT NULL,
    width INTEGER,
    height INTEGER,
    name VARCHAR(255),
    description TEXT,
    tags JSONB,
    vector_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_images_created_at ON images(created_at);
CREATE INDEX idx_images_tags ON images USING GIN(tags);
```

### 5.2 ベクトルデータ (pgvector使用時)

```sql
CREATE EXTENSION vector;

CREATE TABLE image_vectors (
    vector_id VARCHAR(255) PRIMARY KEY,
    image_id UUID REFERENCES images(image_id) ON DELETE CASCADE,
    embedding vector(512),  -- モデルに応じて次元数を調整
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_image_vectors_embedding ON image_vectors
USING ivfflat (embedding vector_cosine_ops);
```

## 6. App Runner 設定

### 6.1 Dockerファイル要件
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 依存関係インストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコピー
COPY . .

# ポート公開
EXPOSE 8000

# 起動コマンド
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 6.2 App Runner 構成
- **CPU**: 1 vCPU
- **メモリ**: 2 GB
- **ポート**: 8000
- **自動スケーリング**:
  - 最小インスタンス: 1
  - 最大インスタンス: 10
  - 同時実行数: 100
- **環境変数**:
  - `DATABASE_URL`: RDS接続文字列
  - `S3_BUCKET_NAME`: 画像保存用バケット名
  - `AWS_REGION`: リージョン
  - `VECTOR_DB_URL`: ベクトルDB接続情報
  - `API_KEY`: API認証キー

### 6.3 IAMロール権限
App Runnerインスタンスロールに以下の権限が必要:
- S3: `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject`
- RDS: VPC接続権限
- CloudWatch: ログ書き込み権限

## 7. API仕様

### 7.1 認証
すべてのエンドポイントで以下のヘッダーが必要:
```
X-API-Key: {api_key}
```

### 7.2 エラーレスポンス
```json
{
  "error": {
    "code": "INVALID_IMAGE",
    "message": "画像形式が不正です",
    "details": "Supported formats: JPEG, PNG"
  }
}
```

### 7.3 レート制限
- 1IPあたり 100リクエスト/分
- 超過時: HTTP 429 Too Many Requests

## 8. 開発フェーズ

### Phase 1: MVP (最小機能)
- [ ] FastAPI基本セットアップ
- [ ] 画像アップロード + S3保存
- [ ] 特徴ベクトル抽出 (ResNet50)
- [ ] インメモリベクトル検索
- [ ] Dockerfile作成
- [ ] App Runnerデプロイ

### Phase 2: データベース統合
- [ ] RDS PostgreSQL セットアップ
- [ ] pgvector拡張導入
- [ ] メタデータCRUD実装
- [ ] ベクトル永続化

### Phase 3: 機能拡張
- [ ] API認証実装
- [ ] タグベースフィルタリング
- [ ] ページネーション
- [ ] 画像削除機能

### Phase 4: 本番対応
- [ ] CloudWatch監視設定
- [ ] エラーハンドリング強化
- [ ] パフォーマンスチューニング
- [ ] セキュリティ監査
- [ ] CI/CDパイプライン

## 9. コスト見積もり (月額)

### 開発環境
- App Runner: ~$25 (1インスタンス、低トラフィック)
- S3: ~$1 (10GB保存)
- RDS db.t3.micro: ~$15
- **合計**: ~$41/月

### 本番環境 (想定: 1万リクエスト/日)
- App Runner: ~$50-100 (自動スケーリング)
- S3: ~$5 (50GB保存)
- RDS db.t3.small Multi-AZ: ~$60
- データ転送: ~$10
- **合計**: ~$125-175/月

## 10. セキュリティ考慮事項

- [ ] 画像ファイルサイズ制限
- [ ] ファイル形式バリデーション
- [ ] S3バケットポリシー設定
- [ ] VPC内でのRDS配置
- [ ] シークレット管理 (AWS Secrets Manager)
- [ ] CORS設定
- [ ] レート制限実装

## 11. 今後の拡張可能性

- フロントエンドUIの追加 (React/Vue.js)
- リアルタイム検索結果のストリーミング
- 画像の自動タグ付け (AI)
- ユーザー認証・マルチテナント対応
- 検索履歴・お気に入り機能
- 動画サムネイル検索対応
