#!/bin/bash
# 启动Web界面服务

set -e

# 获取脚本所在目录的父目录（项目根目录）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🚀 启动地址公寓识别工具Web界面..."
echo "项目目录: $PROJECT_ROOT"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到python3命令"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
if [ -f "requirements.txt" ]; then
    python3 -m pip install -r requirements.txt
else
    echo "⚠️  警告: 未找到requirements.txt文件"
fi

# 设置环境变量
export FLASK_APP=ui/app.py
export FLASK_ENV=development

# 启动Flask应用
echo "🌐 启动Web服务器..."
echo "访问地址: http://localhost:5000"
echo "按 Ctrl+C 停止服务"
echo ""

python3 ui/app.py