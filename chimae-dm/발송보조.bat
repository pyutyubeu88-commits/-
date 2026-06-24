@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 치매간병보험 DM 발송 보조
echo ============================================
echo   치매간병보험 DM 발송 보조
echo ============================================
echo.
echo 최신 버전 확인 중...
git pull origin claude/harness-construction-chat-B5OUJ 2>nul
if errorlevel 1 git pull 2>nul
echo.
echo 프로그램 실행 중...
python sender_app.py
if errorlevel 1 (
    echo.
    echo [오류] 실행 실패. Python 이 설치되어 있는지 확인하세요.
    echo        https://www.python.org/downloads 에서 설치 후 다시 시도.
    pause
)
