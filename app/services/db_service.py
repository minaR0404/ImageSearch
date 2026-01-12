"""
SQLiteデータベースサービス

画像メタデータの保存・取得・検索を担当
FTS5を使った全文検索機能を提供
"""

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from app.config import settings


class DatabaseService:
    """SQLiteデータベース操作クラス"""

    def __init__(self, db_path: str = "data/images.db"):
        self.db_path = db_path
        self._init_database()

    @contextmanager
    def _get_connection(self):
        """データベース接続のコンテキストマネージャー"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 辞書形式でアクセス可能に
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_database(self):
        """データベースとテーブルを初期化"""
        # データベースディレクトリを作成
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # メインテーブル作成
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS images (
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
                )
            """)

            # インデックス作成
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_created_at ON images(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_name ON images(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_tags ON images(tags)")

            # FTS5全文検索テーブル作成
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS images_fts USING fts5(
                    image_id UNINDEXED,
                    name,
                    description,
                    tags,
                    content='images',
                    content_rowid='rowid'
                )
            """)

            # トリガー作成（FTS5テーブルを自動更新）
            # INSERT トリガー
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS images_ai AFTER INSERT ON images BEGIN
                    INSERT INTO images_fts(rowid, image_id, name, description, tags)
                    VALUES (new.rowid, new.image_id, new.name, new.description, new.tags);
                END
            """)

            # DELETE トリガー
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS images_ad AFTER DELETE ON images BEGIN
                    INSERT INTO images_fts(images_fts, rowid, image_id, name, description, tags)
                    VALUES('delete', old.rowid, old.image_id, old.name, old.description, old.tags);
                END
            """)

            # UPDATE トリガー
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS images_au AFTER UPDATE ON images BEGIN
                    INSERT INTO images_fts(images_fts, rowid, image_id, name, description, tags)
                    VALUES('delete', old.rowid, old.image_id, old.name, old.description, old.tags);
                    INSERT INTO images_fts(rowid, image_id, name, description, tags)
                    VALUES (new.rowid, new.image_id, new.name, new.description, new.tags);
                END
            """)

    def create_image(
        self,
        s3_key: str,
        s3_bucket: str,
        file_name: str,
        file_size: int,
        mime_type: str,
        name: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        description: Optional[str] = None,
        tags: Optional[str] = None
    ) -> str:
        """画像メタデータを登録

        Args:
            s3_key: S3オブジェクトキー
            s3_bucket: S3バケット名
            file_name: ファイル名
            file_size: ファイルサイズ（バイト）
            mime_type: MIMEタイプ
            name: 画像名
            width: 画像幅（ピクセル）
            height: 画像高さ（ピクセル）
            description: 画像の説明
            tags: タグ（カンマ区切り）

        Returns:
            生成された画像ID
        """
        image_id = str(uuid.uuid4())

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO images (
                    image_id, s3_key, s3_bucket, file_name, file_size, mime_type,
                    width, height, name, description, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                image_id, s3_key, s3_bucket, file_name, file_size, mime_type,
                width, height, name, description, tags
            ))

        return image_id

    def get_image(self, image_id: str) -> Optional[Dict[str, Any]]:
        """画像IDで画像メタデータを取得

        Args:
            image_id: 画像ID

        Returns:
            画像メタデータ（存在しない場合はNone）
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM images WHERE image_id = ?", (image_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def search_images(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """全文検索で画像を検索

        Args:
            query: 検索クエリ
            limit: 取得件数

        Returns:
            検索結果のリスト
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # FTS5全文検索を実行
            cursor.execute("""
                SELECT images.*
                FROM images
                JOIN images_fts ON images.rowid = images_fts.rowid
                WHERE images_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (query, limit))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def list_images(
        self,
        page: int = 1,
        limit: int = 10,
        tag_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """画像一覧を取得

        Args:
            page: ページ番号（1始まり）
            limit: 1ページあたりの件数
            tag_filter: タグフィルター（部分一致）

        Returns:
            画像メタデータのリスト
        """
        offset = (page - 1) * limit

        with self._get_connection() as conn:
            cursor = conn.cursor()

            if tag_filter:
                cursor.execute("""
                    SELECT * FROM images
                    WHERE tags LIKE ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (f"%{tag_filter}%", limit, offset))
            else:
                cursor.execute("""
                    SELECT * FROM images
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def delete_image(self, image_id: str) -> bool:
        """画像メタデータを削除

        Args:
            image_id: 画像ID

        Returns:
            削除成功したかどうか
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM images WHERE image_id = ?", (image_id,))
            return cursor.rowcount > 0

    def count_images(self, tag_filter: Optional[str] = None) -> int:
        """画像の総数を取得

        Args:
            tag_filter: タグフィルター（部分一致）

        Returns:
            画像の総数
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if tag_filter:
                cursor.execute(
                    "SELECT COUNT(*) as count FROM images WHERE tags LIKE ?",
                    (f"%{tag_filter}%",)
                )
            else:
                cursor.execute("SELECT COUNT(*) as count FROM images")

            row = cursor.fetchone()
            return row['count'] if row else 0


# グローバルインスタンス
db_service = DatabaseService()
