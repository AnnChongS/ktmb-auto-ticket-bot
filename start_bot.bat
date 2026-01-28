@echo off
:: 设置字符集为UTF-8，防止中文乱码和闪退
chcp 65001 >nul
title KTMB Web UI - Auto Launcher
color 0b

echo ===================================================
echo     KTMB Web UI - One-Click Launcher
echo ===================================================
echo.

:: 1. Check Python
echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    color 0c
    echo [ERROR] Python is not installed or not in PATH!
    echo 请先安装 Python 并勾选 "Add Python to PATH".
    pause
    exit /b
)
echo Python is OK.
echo.

:: 2. Auto-create requirements.txt
echo [2/5] Checking requirements.txt...
if not exist requirements.txt (
    echo Auto-creating requirements.txt...
    echo requests> requirements.txt
    echo playwright>> requirements.txt
    echo flask>> requirements.txt
)
echo requirements.txt is OK.
echo.

:: 3. Check and Create VENV
set VENV_DIR=venv
echo [3/5] Checking virtual environment (venv)...
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Creating venv... This might take a minute...
    python -m venv %VENV_DIR%
    if errorlevel 1 (
        color 0c
        echo [ERROR] Failed to create venv!
        pause
        exit /b
    )
)
echo Venv is OK.
echo.

:: 4. Install dependencies
echo [4/5] Installing dependencies (Please wait)...
"%VENV_DIR%\Scripts\python.exe" -m pip install -r requirements.txt
echo Checking Playwright browsers...
"%VENV_DIR%\Scripts\python.exe" -m playwright install chromium
echo Dependencies are OK.
echo.

:: 5. Start Chrome
echo [5/5] Starting Chrome (Port 9222)...
start chrome --remote-debugging-port=9222 --user-data-dir="C:\ChromeDebug"
echo.

:: 6. Start Web Server
echo Starting Flask Backend Server...
timeout /t 2 /nobreak >nul

:: 正确的启动虚拟环境并运行 app.py 的语法
start "KTMB_Backend" cmd /k "%VENV_DIR%\Scripts\activate.bat && python app.py"

echo Opening Web UI...
timeout /t 3 /nobreak >nul
start http://127.0.0.1:5000

echo.
echo ===================================================
echo All Started! Please do not close the backend window.
echo 启动完毕！请不要关闭名为 KTMB_Backend 的黑色终端窗口！
echo ===================================================
echo.
pause