import io
import numpy as np
import torch
import torchvision.transforms as transforms
from PIL import Image
from torchvision.models import resnet50, ResNet50_Weights


class ImageProcessor:
    """ResNet50を使用した画像特徴抽出サービス"""

    def __init__(self):
        """事前学習済みResNet50モデルを初期化"""
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # 事前学習済みResNet50をロード
        weights = ResNet50_Weights.DEFAULT
        self.model = resnet50(weights=weights)

        # 最終分類層を削除して特徴ベクトルを取得
        self.model = torch.nn.Sequential(*list(self.model.children())[:-1])
        self.model.eval()
        self.model.to(self.device)

        # 画像前処理
        self.preprocess = weights.transforms()

    def extract_features(self, image_bytes: bytes) -> np.ndarray:
        """
        画像バイトデータから特徴ベクトルを抽出

        Args:
            image_bytes: 画像データ（バイト形式）

        Returns:
            特徴ベクトル（numpy配列、shape: 2048,）

        Raises:
            ValueError: 画像処理に失敗した場合
        """
        try:
            # バイトデータから画像を読み込み
            image = Image.open(io.BytesIO(image_bytes))

            # 必要に応じてRGBに変換
            if image.mode != "RGB":
                image = image.convert("RGB")

            # 画像を前処理
            input_tensor = self.preprocess(image).unsqueeze(0).to(self.device)

            # 特徴抽出
            with torch.no_grad():
                features = self.model(input_tensor)

            # numpy配列に変換してフラット化
            feature_vector = features.cpu().numpy().flatten()

            # 単位長さに正規化
            feature_vector = feature_vector / np.linalg.norm(feature_vector)

            return feature_vector

        except Exception as e:
            raise ValueError(f"画像からの特徴抽出に失敗しました: {str(e)}")

    @staticmethod
    def validate_image(image_bytes: bytes, max_size: int) -> None:
        """
        画像ファイルを検証

        Args:
            image_bytes: 画像データ（バイト形式）
            max_size: 最大許容ファイルサイズ（バイト）

        Raises:
            ValueError: 画像が無効な場合
        """
        # ファイルサイズチェック
        if len(image_bytes) > max_size:
            raise ValueError(f"画像サイズが最大許容サイズ {max_size} バイトを超えています")

        try:
            # 画像を開いてみる
            image = Image.open(io.BytesIO(image_bytes))

            # 有効な画像形式か確認
            image.verify()

        except Exception as e:
            raise ValueError(f"無効な画像ファイルです: {str(e)}")


# グローバルインスタンス
image_processor = ImageProcessor()
