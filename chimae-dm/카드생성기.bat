@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 최신 버전 확인 중...
git pull >nul 2>&1
echo GUI 실행 중...
python card_app.py
if errorlevel 1 (
    echo.
    echo Python 실행에 실패했습니다. Python이 설치되어 있는지 확인하세요.
    pause
)
