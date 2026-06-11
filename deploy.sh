#!/bin/bash

# 訂餐系統部署腳本
set -e

echo "🚀 開始部署訂餐系統..."

# 檢查 Docker 是否安裝
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安裝，請先安裝 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安裝，請先安裝 Docker Compose"
    exit 1
fi

# 檢查 .env 檔案
if [ ! -f .env ]; then
    echo "⚙️  複製環境變數範本..."
    cp .env.example .env
    echo "✅ 已建立 .env 檔案，請編輯並填入 LINE Channel 設定"
    echo ""
    echo "需要設定的項目："
    echo "  - LINE_CHANNEL_ACCESS_TOKEN"
    echo "  - LINE_CHANNEL_SECRET"
    echo "  - DB_PASSWORD (可保持預設)"
    echo ""
    read -p "是否現在編輯 .env? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        nano .env
    fi
fi

# 建立必要目錄
echo "📁 建立必要目錄..."
mkdir -p uploads frontend/web/dist

# 啟動服務
echo "🐳 啟動 Docker 容器..."
docker-compose up -d

# 等待服務啟動
echo "⏳ 等待服務啟動..."
sleep 10

# 檢查服務狀態
echo ""
echo "📊 服務狀態："
docker-compose ps

# 拉取 LLM 模型
echo ""
echo "🤖 檢查 Ollama 模型..."
docker exec meal-ordering-ollama ollama list || true

echo ""
echo "❓ 是否要拉取 Llama3 模型？(約 4.7GB)"
read -p "[y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "⬇️  拉取 Llama3 模型..."
    docker exec -d meal-ordering-ollama ollama pull llama3
    echo "✅ 模型拉取已啟動（背景執行，約需 5-10 分鐘）"
    echo "可用以下指令查看進度："
    echo "  docker logs -f meal-ordering-ollama"
fi

echo ""
echo "✅ 部署完成！"
echo ""
echo "📱 系統連結："
echo "  • 管理後台：http://localhost"
echo "  • API 文件：http://localhost/docs"
echo "  • API 服務：http://localhost:8000"
echo ""
echo "📋 下一步："
echo "  1. 設定 LINE Channel Webhook"
echo "  2. 新增餐廳資料"
echo "  3. 匯入員工名單"
echo "  4. 設定今日訂餐規則"
echo ""
echo "📖 詳細說明請參閱 README.md"
