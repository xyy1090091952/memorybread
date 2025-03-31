@echo off
cd /d "%~dp0"

echo MemoryBread v0.1.6
echo ======================

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found, downloading installer...
    :: Download Python installer
    powershell -Command "& {Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe' -OutFile 'python-installer.exe'}"
    
    :: Install Python
    echo Installing Python...
    python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python-installer.exe
    
    :: Refresh environment variables
    call RefreshEnv.cmd
)

:: Install required Python packages
echo Checking and installing required packages...
python -m pip install --upgrade pip
python -m pip install watchdog

:: Ensure required directories exist
if not exist database mkdir database
if not exist images mkdir images

:: Start server and open browser
start http://localhost:7023
python save_words_server.py

pause 