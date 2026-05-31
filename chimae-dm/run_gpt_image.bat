@echo off
chcp 65001 >nul
echo ============================================
echo  치매간병보험 카드 생성기 (gpt-image-2)
echo ============================================
echo.

set /p OPENAI_API_KEY=OpenAI API 키를 붙여넣고 Enter:

if "%OPENAI_API_KEY%"=="" (
    echo 키가 입력되지 않았습니다. 종료합니다.
    pause
    exit /b 1
)

echo.
echo 패키지 설치 중...
pip install openai pillow -q

echo.
echo 카드 생성 시작 (약 1~2분 소요)...
echo.
python gpt_image.py

echo.
echo 완료! out_gpt 폴더를 확인하세요.
explorer out_gpt
pause
