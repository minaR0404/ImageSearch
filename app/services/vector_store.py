from typing import List, Dict, Tuple
from uuid import UUID
import numpy as np
from app.models.schemas import ImageMetadata


class InMemoryVectorStore:
    """インメモリベクトルストア（Phase 1用）"""

    def __init__(self):
        """ベクトルストアを初期化"""
        # 画像ID -> 特徴ベクトルのマッピング
        self.vectors: Dict[UUID, np.ndarray] = {}

        # 画像ID -> メタデータのマッピング
        self.metadata: Dict[UUID, ImageMetadata] = {}

        # 画像ID -> S3 URLのマッピング
        self.urls: Dict[UUID, str] = {}

    def add_vector(
        self, image_id: UUID, vector: np.ndarray, metadata: ImageMetadata, image_url: str
    ) -> None:
        """
        ベクトルとメタデータを追加

        Args:
            image_id: 画像のユニークID
            vector: 特徴ベクトル
            metadata: 画像のメタデータ
            image_url: S3上の画像URL
        """
        self.vectors[image_id] = vector
        self.metadata[image_id] = metadata
        self.urls[image_id] = image_url

    def search(
        self, query_vector: np.ndarray, top_k: int = 10
    ) -> List[Tuple[UUID, float]]:
        """
        コサイン類似度で類似ベクトルを検索

        Args:
            query_vector: 検索クエリのベクトル
            top_k: 返す結果の数

        Returns:
            (image_id, similarity_score)のリスト（類似度降順）
        """
        if not self.vectors:
            return []

        # 全ベクトルとの類似度を計算
        similarities = []
        for image_id, stored_vector in self.vectors.items():
            # コサイン類似度を計算
            similarity = self._cosine_similarity(query_vector, stored_vector)
            similarities.append((image_id, float(similarity)))

        # 類似度で降順ソート
        similarities.sort(key=lambda x: x[1], reverse=True)

        # 上位k件を返す
        return similarities[:top_k]

    def get_metadata(self, image_id: UUID) -> ImageMetadata:
        """
        画像IDからメタデータを取得

        Args:
            image_id: 画像のユニークID

        Returns:
            画像のメタデータ

        Raises:
            KeyError: 画像IDが存在しない場合
        """
        return self.metadata[image_id]

    def get_url(self, image_id: UUID) -> str:
        """
        画像IDからS3 URLを取得

        Args:
            image_id: 画像のユニークID

        Returns:
            S3上の画像URL

        Raises:
            KeyError: 画像IDが存在しない場合
        """
        return self.urls[image_id]

    def delete_vector(self, image_id: UUID) -> None:
        """
        ベクトルとメタデータを削除

        Args:
            image_id: 画像のユニークID
        """
        self.vectors.pop(image_id, None)
        self.metadata.pop(image_id, None)
        self.urls.pop(image_id, None)

    def count(self) -> int:
        """
        登録されているベクトルの数を返す

        Returns:
            ベクトル数
        """
        return len(self.vectors)

    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        2つのベクトルのコサイン類似度を計算

        Args:
            vec1: ベクトル1
            vec2: ベクトル2

        Returns:
            コサイン類似度（-1 ~ 1）
        """
        # ベクトルが正規化されている前提でドット積を計算
        return np.dot(vec1, vec2)


# グローバルインスタンス
vector_store = InMemoryVectorStore()
