@echo off
chcp 65001 >nul
title 네이버 블로그 자동화 - 최초 설치
echo ============================================
echo   최초 1회 설치를 시작합니다 (몇 분 걸립니다)
echo ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [오류] 이 PC에 Python이 설치되어 있지 않습니다.
    echo.
    echo 1. https://www.python.org/downloads/ 접속
    echo 2. [Download Python] 노란 버튼 클릭해서 설치
    echo 3. 설치 첫 화면에서 [Add Python to PATH] 체크박스 꼭 체크!
    echo 4. 설치가 끝나면 이 파일(install.bat)을 다시 더블클릭
    echo.
    pause
    exit /b 1
)

echo [1/2] 필요한 프로그램 설치 중...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo [2/2] 자동 발행용 브라우저 설치 중...
python -m playwright install chromium

echo.
echo ============================================
echo   설치 완료!
echo   이제 start.bat 파일을 더블클릭하면 실행됩니다.
echo ============================================
pause
