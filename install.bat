@echo off
title Naver Blog Automation - Install

python --version >nul 2>&1
if errorlevel 1 goto NOPYTHON

echo [1/2] 필요한 프로그램을 설치하는 중입니다. 몇 분 걸립니다...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo [2/2] 자동 발행용 브라우저를 설치하는 중입니다...
python -m playwright install chromium

echo.
echo ==========================================
echo   설치 완료. 이제 start.bat 을 더블클릭하세요.
echo ==================================================
pause
exit /b 0

:NOPYTHON
echo.
echo [오류] 이 PC에 Python 이 설치되어 있지 않습니다.
echo.
echo 1. 인터넷 주소창에 www.python.org/downloads 입력해서 접속
echo 2. Download Python 노란 버튼을 눌러 받은 파일 실행
echo 3. 설치 첫 화면 맨 아래 Add Python to PATH 체크박스를 꼭 체크
echo 4. 설치가 끝나면 install.bat 을 다시 더블클릭
echo.
pause
exit /b 1
