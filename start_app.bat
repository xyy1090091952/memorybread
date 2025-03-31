@echo off

REM 获取脚本所在目录的绝对路径
for /f "delims=" %%i in ("%~dp0") do set SCRIPT_DIR=%%~fi
cd /d "%SCRIPT_DIR%" || (
    echo Error: Cannot change to script directory %SCRIPT_DIR%
    exit /b 1
)

REM 确保在正确的目录下运行
if not exist "save_words_server.py" (
    echo Error: Must run this script in directory containing save_words_server.py
    exit /b 1
)

REM 检查并释放7023端口
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":7023"') do (
    echo Port 7023 is occupied, releasing...
    taskkill /pid %%a /f
    timeout /t 1 >nul
)

REM 检查服务是否已运行
tasklist /fi "imagename eq python.exe" /fi "windowtitle eq save_words_server.py" | findstr /i "python.exe" >nul
if errorlevel 1 (
    REM 如果服务未运行，则启动
    start "" /b python save_words_server.py
    echo Service started
) else (
    echo Service is already running
)

timeout /t 2 >nul
REM 清除浏览器缓存并打开网页
start "" "http://localhost:7023/"

REM 添加交互式菜单
:menu
set /p user_input=Type 'stop' and press Enter to shutdown server:
if "%user_input%"=="stop" (
    echo Shutting down server...
    taskkill /fi "windowtitle eq save_words_server.py" /f
    
    REM 检查端口是否已释放
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":7023"') do (
        echo Warning: Port 7023 still occupied, forcing release...
        taskkill /pid %%a /f
        timeout /t 1 >nul
    )
    
    REM 验证进程是否已终止
    tasklist /fi "imagename eq python.exe" /fi "windowtitle eq save_words_server.py" | findstr /i "python.exe" >nul
    if not errorlevel 1 (
        echo Error: Failed to terminate server process
        exit /b 1
    )
    
    echo Server completely shut down
    exit /b 0
)
goto menu