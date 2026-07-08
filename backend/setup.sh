#!/bin/bash

# 赛事推演预测系统 - 初始化脚本
# 用于首次安装配置

set -e  # 遇到错误立即退出

echo "========================================"
echo "  赛事推演预测系统 - 环境初始化"
echo "========================================"
echo ""

# 1. 检查 pyenv
echo "1️⃣  检查 pyenv..."
if ! command -v pyenv &> /dev/null; then
    echo "❌ 未找到 pyenv"
    echo "💡 请先安装 pyenv: https://github.com/pyenv/pyenv"
    exit 1
fi
echo "✅ pyenv 已安装"
echo ""

# 2. 检查 Python 版本
echo "2️⃣  检查 Python 环境..."
PYTHON_VERSION=$(python --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
if [ -z "$PYTHON_VERSION" ]; then
    echo "❌ 未找到 Python 环境"
    echo "💡 请激活 pyenv 虚拟环境"
    echo "   例如: pyenv activate codes3.11.12"
    exit 1
fi
echo "✅ Python $PYTHON_VERSION"
echo ""

# 3. 安装依赖
echo "3️⃣  安装 Python 依赖..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ 依赖安装完成"
else
    echo "⚠️  未找到 requirements.txt"
fi
echo ""

# 4. 配置 .env 文件
echo "4️⃣  配置环境变量..."
if [ -f ".env" ]; then
    echo "⚠️  .env 文件已存在"
    read -p "是否覆盖？(y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "跳过 .env 配置"
    else
        cp .env.example .env
        echo "✅ 已复制 .env.example -> .env"
        echo "💡 请编辑 .env 文件配置数据库连接信息"
    fi
else
    cp .env.example .env
    echo "✅ 已创建 .env 文件"
    echo "💡 请编辑 .env 文件配置数据库连接信息"
fi
echo ""

# 5. 初始化数据库
echo "5️⃣  初始化数据库..."
read -p "是否初始化数据库表？(y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "init_db.py" ]; then
        python init_db.py
        echo "✅ 数据库初始化完成"
    else
        echo "⚠️  未找到 init_db.py"
    fi
else
    echo "跳过数据库初始化"
fi
echo ""

# 6. 完成
echo "========================================"
echo "✅ 初始化完成！"
echo "========================================"
echo ""
echo "📋 后续步骤:"
echo "   1. 编辑 .env 文件配置数据库"
echo "   2. 运行 ./start.sh 启动服务"
echo "   3. 访问 http://localhost:8000/api/v1/docs"
echo ""
echo "💡 提示:"
echo "   - 启动服务: ./start.sh"
echo "   - 触发爬虫: python trigger_crawler.py"
echo ""
