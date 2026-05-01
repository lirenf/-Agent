#!/usr/bin/env bash
# PaperMind 快速启动脚本
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$SCRIPT_DIR/.."

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║     PaperMind — 论文深度分析 Agent      ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# 检查 API Key
if [ -z "$ANTHROPIC_API_KEY" ]; then
  if [ -f "$ROOT/.env" ]; then
    export $(grep -v '^#' "$ROOT/.env" | xargs)
  fi
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "❌ 未设置 ANTHROPIC_API_KEY"
  echo ""
  echo "请在项目根目录创建 .env 文件:"
  echo "  cp .env.example .env"
  echo "  # 编辑 .env 填入你的 API Key"
  echo ""
  exit 1
fi

# 安装依赖
cd "$ROOT/backend"
echo "📦 安装 Python 依赖..."
pip install -r requirements.txt -q

echo ""
echo "🚀 启动服务: http://localhost:8000"
echo "   按 Ctrl+C 停止"
echo ""

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
