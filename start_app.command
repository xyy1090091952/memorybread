#!/bin/bash
# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# 确保在双击执行时也能正确设置工作目录
cd "$SCRIPT_DIR" || {
    echo "错误：无法切换到脚本所在目录 $SCRIPT_DIR"
    exit 1
}

# 确保在正确的目录下运行
if [ ! -f "save_words_server.py" ]; then
    echo "错误：必须在包含save_words_server.py的目录中运行此脚本"
    exit 1
fi

# 检查并释放7023端口
if lsof -i :7023 > /dev/null; then
    echo "发现7023端口被占用，正在释放..."
    kill -9 $(lsof -t -i :7023)
    sleep 1
fi

# 检查并安装watchdog模块
if ! python3 -c "import watchdog" > /dev/null 2>&1; then
    echo "警告: watchdog未安装，文件变更监听功能将不可用"
    echo "尝试自动安装watchdog模块..."
    if pip3 install watchdog > /dev/null 2>&1; then
        echo "watchdog模块安装成功，文件变更监听功能已启用"
    else
        echo "自动安装watchdog模块失败，服务器将以降级模式运行"
    fi
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
# 清除浏览器缓存
osascript -e 'tell application "Google Chrome" to activate'
osascript -e 'tell application "Google Chrome" to tell application "System Events" to keystroke "e" using {command down, shift down}'
open http://localhost:7023/

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