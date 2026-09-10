@echo off
title Naver Blog Automation - Update

echo 프로그램을 최신 버전으로 업데이트합니다...
echo 주의: 프로그램이 켜져 있으면 먼저 검은 창을 닫아 주세요.
echo.
pause

curl -L -o _update.zip https://github.com/eduwiki2015/first/archive/refs/heads/claude/epic-pascal-vnkffh.zip
if errorlevel 1 goto FAIL

tar -xf _update.zip
if errorlevel 1 goto FAIL

xcopy /E /Y first-claude-epic-pascal-vnkffh\* . >nul
rmdir /S /Q first-claude-epic-pascal-vnkffh
del _update.zip

echo.
echo ==========================================
echo   업데이트 완료. start.bat 으로 실행하세요.
echo ==========================================
pause
exit /b 0

:FAIL
echo.
echo [오류] 업데이트 파일 다운로드에 실패했습니다. 인터넷 연결을 확인해 주세요.
pause
exit /b 1
