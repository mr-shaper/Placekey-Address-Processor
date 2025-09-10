#!/bin/bash
# 地址公寓识别工具 - 清理启动脚本

echo "🧹 正在清理临时文件和缓存..."

# 获取Python临时目录路径
TEMP_DIR=$(python3 -c "import tempfile; print(tempfile.gettempdir())")

echo "临时目录: $TEMP_DIR"

# 清理上传文件
echo "清理上传文件..."
rm -f "$TEMP_DIR"/upload_*.csv 2>/dev/null || true

# 清理处理后的文件
echo "清理处理文件..."
rm -f "$TEMP_DIR"/processed_*.csv 2>/dev/null || true

# 清理其他临时文件
echo "清理其他临时文件..."
rm -f "$TEMP_DIR"/temp_*.csv 2>/dev/null || true
rm -f "$TEMP_DIR"/cache_*.csv 2>/dev/null || true
rm -f "$TEMP_DIR"/*.tmp 2>/dev/null || true

echo "✅ 临时文件清理完成"
echo "🚀 启动Web应用..."

# 启动Flask应用
python3 ui/app.py