#!/bin/bash

# 赛事推演预测系统 - 后端启动脚本
# 前置要求:
# 1. pyenv 虚拟环境已创建并激活
# 2. .env 文件已配置
# 3. 数据库表已初始化

set -e  # 遇到错误立即退出

echo "========================================"
echo "  赛事推演预测系统 - 后端启动"
echo "========================================"
echo ""

# 检查 Python 环境
if ! command -v python &> /dev/null; then
    echo "❌ 错误: 未找到 Python 环境"
    echo "💡 请先激活 pyenv 虚拟环境"
    exit 1
fi

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "❌ 错误: 未找到 .env 文件"
    echo "💡 请先创建 .env 文件并配置数据库连接"
    echo "   可以复制: cp .env.example .env"
    exit 1
fi

# 检查依赖
if ! python -c "import fastapi" &> /dev/null; then
    echo "⚠️  警告: 依赖未安装，正在安装..."
    pip install -r requirements.txt
fi

# 检查是否已有服务在运行
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  警告: 端口 8000 已被占用"
    echo "💡 可能已有服务在运行，或使用其他端口"
    read -p "是否强制停止并重启？(y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "停止旧服务..."
        lsof -Pi :8000 -sTCP:LISTEN -t | xargs kill -9 2>/dev/null || true
        sleep 1
    else
        exit 1
    fi
fi

# 显示配置信息
echo "📋 配置信息:"
echo "   Python: $(python --version 2>&1 | head -n1)"
echo "   工作目录: $(pwd)"
echo ""

# 启动服务
echo "🚀 启动服务..."
echo "   API 文档: http://localhost:8000/api/v1/docs"
echo "   健康检查: http://localhost:8000/api/v1/matches"
echo ""
echo "按 Ctrl+C 停止服务"
echo "========================================"
echo ""

# 启动 FastAPI 服务
python -m app.main
