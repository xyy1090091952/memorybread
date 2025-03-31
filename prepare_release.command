#!/bin/bash

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# 创建临时目录
TEMP_DIR="memorybread_temp"
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

# 复制必要文件
echo "正在准备发布包..."
cp -r index.html "$TEMP_DIR/"
cp -r save_words_server.py "$TEMP_DIR/"
cp -r start_app.command "$TEMP_DIR/"
cp -r README.md "$TEMP_DIR/"
cp -r database "$TEMP_DIR/"
cp -r images "$TEMP_DIR/"

# 设置权限
chmod +x "$TEMP_DIR/start_app.command"

# 创建发布包
echo "正在创建发布包..."
zip -r "memorybread_mac.zip" "$TEMP_DIR"

# 清理临时文件
rm -rf "$TEMP_DIR"

echo "发布包已创建：memorybread_mac.zip"
echo "请检查发布包内容是否完整" 