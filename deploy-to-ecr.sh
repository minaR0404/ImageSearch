#!/bin/bash

# ECRにDockerイメージをプッシュするスクリプト
# 使い方: ./deploy-to-ecr.sh

set -e  # エラーが発生したら即座に終了

# 設定
AWS_REGION="ap-northeast-1"
AWS_ACCOUNT_ID="714624883784"
REPOSITORY_NAME="imagesearch"
IMAGE_TAG="latest"

echo "========================================="
echo "ECRへのDockerイメージデプロイ"
echo "========================================="

# ステップ1: ECRにログイン
echo ""
echo "[1/6] ECRにログイン中..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# ステップ2: ECRリポジトリが存在するか確認（なければ作成）
echo ""
echo "[2/6] ECRリポジトリを確認中..."
if ! aws ecr describe-repositories --repository-names $REPOSITORY_NAME --region $AWS_REGION > /dev/null 2>&1; then
    echo "リポジトリが存在しないため、作成します..."
    aws ecr create-repository --repository-name $REPOSITORY_NAME --region $AWS_REGION
    echo "リポジトリを作成しました: $REPOSITORY_NAME"
else
    echo "リポジトリは既に存在します: $REPOSITORY_NAME"
fi

# ステップ3: Dockerイメージをビルドまたは既存イメージを使用
echo ""
echo "[3/6] Dockerイメージの確認..."
if docker images | grep -q "^$REPOSITORY_NAME.*$IMAGE_TAG"; then
    echo "既存のイメージが見つかりました: $REPOSITORY_NAME:$IMAGE_TAG"
    read -p "既存のイメージを使用しますか？ (y/n) [y]: " use_existing
    use_existing=${use_existing:-y}

    if [[ $use_existing == "y" || $use_existing == "Y" ]]; then
        echo "既存のイメージを使用します"
    else
        echo "イメージを再ビルドします..."
        echo "これには時間がかかる場合があります（PyTorchのダウンロードのため）..."
        docker build -t $REPOSITORY_NAME:$IMAGE_TAG .
    fi
else
    echo "イメージが見つかりません。ビルドします..."
    echo "これには時間がかかる場合があります（PyTorchのダウンロードのため）..."
    docker build -t $REPOSITORY_NAME:$IMAGE_TAG .
fi

# ステップ4: イメージにECR用のタグを付ける
echo ""
echo "[4/6] イメージにタグを付与中..."
docker tag $REPOSITORY_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPOSITORY_NAME:$IMAGE_TAG

# ステップ5: ECRにプッシュ
echo ""
echo "[5/6] ECRにプッシュ中..."
echo "これには時間がかかる場合があります（イメージサイズが大きいため）..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPOSITORY_NAME:$IMAGE_TAG

# ステップ6: 完了
echo ""
echo "[6/6] 完了！"
echo "========================================="
echo "デプロイ完了"
echo "========================================="
echo ""
echo "イメージURI:"
echo "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPOSITORY_NAME:$IMAGE_TAG"
echo ""
echo "このURIをApp Runnerで使用できます。"
