#!/bin/bash
# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# 确保在双击执行时也能正确设置工作目录
cd "$SCRIPT_DIR" || {
    echo "错误：无法切换到脚本所在目录 $SCRIPT_DIR"
    exit 1
}

# 检查并设置必要的执行权限
echo "检查并设置必要的执行权限..."
chmod +x "$SCRIPT_DIR/start_app.command"
chmod +x "$SCRIPT_DIR/save_words_server.py"

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "正在安装Python..."
    # 使用系统自带的Python安装器
    /usr/bin/python3 -m ensurepip --upgrade
    echo "Python安装完成，请重新运行此脚本"
    exit 0
fi

# 检查Python版本
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if (( $(echo "$PYTHON_VERSION < 3.7" | bc -l) )); then
    echo "正在更新Python..."
    # 使用系统自带的Python安装器
    /usr/bin/python3 -m ensurepip --upgrade
    echo "Python更新完成，请重新运行此脚本"
    exit 0
fi

# 检查并创建必要的目录
if [ ! -d "database" ]; then
    echo "创建数据库目录..."
    mkdir -p database
fi

if [ ! -d "images" ]; then
    echo "创建图片目录..."
    mkdir -p images
fi

# 检查并安装必要的Python包
echo "检查并安装必要的Python包..."
REQUIRED_PACKAGES=("flask" "watchdog")
for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! python3 -c "import $package" > /dev/null 2>&1; then
        echo "正在安装 $package..."
        if ! pip3 install $package > /dev/null 2>&1; then
            echo "错误：无法安装 $package，请检查网络连接或手动安装"
            echo "您可以运行: pip3 install $package"
            exit 1
        fi
    fi
done

# 检查并释放7023端口
if lsof -i :7023 > /dev/null; then
    echo "发现7023端口被占用，正在释放..."
    kill -9 $(lsof -t -i :7023)
    sleep 1
fi

# 检查服务是否已运行
if ! pgrep -f "python3 save_words_server.py" > /dev/null; then
    # 如果服务未运行，则启动
    nohup bash -c "while true; do
        python3 save_words_server.py
        echo '服务器意外停止，将在5秒后重启...'
        sleep 5
    done" > /dev/null 2>&1 &
    echo "服务已启动"
else
    echo "服务已在运行中"
fi

sleep 2  # 等待服务器启动

# 尝试打开Chrome浏览器
if [ -d "/Applications/Google Chrome.app" ]; then
    echo "正在打开Chrome浏览器..."
    osascript -e 'tell application "Google Chrome" to activate'
    osascript -e 'tell application "Google Chrome" to tell application "System Events" to keystroke "e" using {command down, shift down}'
else
    echo "未检测到Chrome浏览器，将使用默认浏览器打开..."
fi

# 打开应用
open http://localhost:7023/

echo "应用已启动，请在浏览器中访问 http://localhost:7023/"
echo "如果浏览器没有自动打开，请手动访问上述地址"

# 添加交互式菜单
while true; do
    echo "输入'stop'并按回车键关闭服务器:"
    read user_input
    if [ "$user_input" = "stop" ]; then
        echo "正在关闭服务器..."
        pkill -f "python3 save_words_server.py"
        pkill -f "nohup bash -c while true"
        
        # 检查端口是否已释放
        if lsof -i :7023 > /dev/null; then
            echo "警告：7023端口仍被占用，正在强制释放..."
            kill -9 $(lsof -t -i :7023)
            sleep 1
        fi
        
        # 验证进程是否已终止
        if pgrep -f "python3 save_words_server.py" > /dev/null; then
            echo "错误：无法终止服务器进程"
            exit 1
        fi
        
        echo "服务器已完全关闭"
        exit 0
    fi
done