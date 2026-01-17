"""
データベースサービス

画像メタデータの保存・取得・検索を担当
PostgreSQLまたはSQLiteに対応
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from app.config import settings


class DatabaseService:
    """データベース操作クラス（PostgreSQL/SQLite対応）"""

    def __init__(self):
        self.db_url = settings.DATABASE_URL
        self.is_postgres = self.db_url.startswith("postgresql://")

        if self.is_postgres:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            self.psycopg2 = psycopg2
            self.RealDictCursor = RealDictCursor
        else:
            import sqlite3
            self.sqlite3 = sqlite3

        self._init_database()

    @contextmanager
    def _get_connection(self):
        """データベース接続のコンテキストマネージャー"""
        if self.is_postgres:
            # PostgreSQL接続
            conn = self.psycopg2.connect(self.db_url)
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
        else:
            # SQLite接続
            db_path = self.db_url.replace("sqlite:///", "")
            conn = self.sqlite3.connect(db_path)
            conn.row_factory = self.sqlite3.Row
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
        if not self.is_postgres:
            # SQLiteの場合、ディレクトリ作成
            from pathlib import Path
            db_path = self.db_url.replace("sqlite:///", "")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            if self.is_postgres:
                # PostgreSQL用テーブル作成
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

                # PostgreSQL用インデックス作成
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_created_at ON images(created_at)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_name ON images(name)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_tags ON images(tags)")

                # PostgreSQL用全文検索インデックス
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_images_search
                    ON images USING gin(
                        to_tsvector('english',
                            coalesce(name, '') || ' ' ||
                            coalesce(description, '') || ' ' ||
                            coalesce(tags, '')
                        )
                    )
                """)
            else:
                # SQLite用テーブル作成
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
                cursor.execute("""
                    CREATE TRIGGER IF NOT EXISTS images_ai AFTER INSERT ON images BEGIN
                        INSERT INTO images_fts(rowid, image_id, name, description, tags)
                        VALUES (new.rowid, new.image_id, new.name, new.description, new.tags);
                    END
                """)

                cursor.execute("""
                    CREATE TRIGGER IF NOT EXISTS images_ad AFTER DELETE ON images BEGIN
                        INSERT INTO images_fts(images_fts, rowid, image_id, name, description, tags)
                        VALUES('delete', old.rowid, old.image_id, old.name, old.description, old.tags);
                    END
                """)

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
        """画像メタデータを登録"""
        image_id = str(uuid.uuid4())

        with self._get_connection() as conn:
            cursor = conn.cursor()

            if self.is_postgres:
                cursor.execute("""
                    INSERT INTO images (
                        image_id, s3_key, s3_bucket, file_name, file_size, mime_type,
                        width, height, name, description, tags
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    image_id, s3_key, s3_bucket, file_name, file_size, mime_type,
                    width, height, name, description, tags
                ))
            else:
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
        """画像IDで画像メタデータを取得"""
        with self._get_connection() as conn:
            if self.is_postgres:
                cursor = conn.cursor(cursor_factory=self.RealDictCursor)
                cursor.execute("SELECT * FROM images WHERE image_id = %s", (image_id,))
            else:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM images WHERE image_id = ?", (image_id,))

            row = cursor.fetchone()
            return dict(row) if row else None

    def search_images(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """全文検索で画像を検索"""
        with self._get_connection() as conn:
            if self.is_postgres:
                cursor = conn.cursor(cursor_factory=self.RealDictCursor)
                # PostgreSQL全文検索
                cursor.execute("""
                    SELECT *
                    FROM images
                    WHERE to_tsvector('english',
                        coalesce(name, '') || ' ' ||
                        coalesce(description, '') || ' ' ||
                        coalesce(tags, '')
                    ) @@ plainto_tsquery('english', %s)
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (query, limit))
            else:
                cursor = conn.cursor()
                # SQLite FTS5全文検索
                search_terms = query.strip().split()
                fts_query = " OR ".join([f"{term}*" for term in search_terms if term])

                cursor.execute("""
                    SELECT images.*
                    FROM images
                    JOIN images_fts ON images.rowid = images_fts.rowid
                    WHERE images_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """, (fts_query, limit))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def list_images(
        self,
        page: int = 1,
        limit: int = 10,
        tag_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """画像一覧を取得"""
        offset = (page - 1) * limit

        with self._get_connection() as conn:
            if self.is_postgres:
                cursor = conn.cursor(cursor_factory=self.RealDictCursor)
                if tag_filter:
                    cursor.execute("""
                        SELECT * FROM images
                        WHERE tags LIKE %s
                        ORDER BY created_at DESC
                        LIMIT %s OFFSET %s
                    """, (f"%{tag_filter}%", limit, offset))
                else:
                    cursor.execute("""
                        SELECT * FROM images
                        ORDER BY created_at DESC
                        LIMIT %s OFFSET %s
                    """, (limit, offset))
            else:
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
        """画像メタデータを削除"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if self.is_postgres:
                cursor.execute("DELETE FROM images WHERE image_id = %s", (image_id,))
            else:
                cursor.execute("DELETE FROM images WHERE image_id = ?", (image_id,))
            return cursor.rowcount > 0

    def count_images(self, tag_filter: Optional[str] = None) -> int:
        """画像の総数を取得"""
        with self._get_connection() as conn:
            if self.is_postgres:
                cursor = conn.cursor(cursor_factory=self.RealDictCursor)
                if tag_filter:
                    cursor.execute(
                        "SELECT COUNT(*) as count FROM images WHERE tags LIKE %s",
                        (f"%{tag_filter}%",)
                    )
                else:
                    cursor.execute("SELECT COUNT(*) as count FROM images")
            else:
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
