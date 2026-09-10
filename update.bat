@echo off
title Naver Blog Automation - Update
echo 프로그램을 최신 버전으로 업데이트합니다...
echo 주의: 프로그램이 켜져 있으면 먼저 검은 창을 닫아 주세요.
echo.
pause

set "URL=https://codeload.github.com/eduwiki2015/first/zip/refs/heads/claude/epic-pascal-vnkffh"

echo 최신 파일을 내려받는 중...
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; try { Invoke-WebRequest -Uri $env:URL -OutFile '_update.zip' -UseBasicParsing } catch { exit 1 }"
if errorlevel 1 goto FAIL
if not exist "_update.zip" goto FAIL

echo 압축을 푸는 중...
if exist "_update_tmp" rmdir /S /Q "_update_tmp"
powershell -NoProfile -Command "try { Expand-Archive -Path '_update.zip' -DestinationPath '_update_tmp' -Force } catch { exit 1 }"
if errorlevel 1 goto FAIL

echo 파일을 교체하는 중...
for /d %%D in ("_update_tmp\*") do xcopy /E /Y /Q "%%D\*" "." >nul

rmdir /S /Q "_update_tmp"
del "_update.zip"

echo.
echo ==========================================
echo   업데이트 완료! 이제 start.bat 을 더블클릭하세요.
echo ==========================================
pause
exit /b 0

:FAIL
echo.
echo [오류] 업데이트에 실패했습니다. 인터넷 연결을 확인하거나,
echo 아래 주소를 브라우저에 붙여넣어 직접 내려받아 주세요:
echo https://github.com/eduwiki2015/first/archive/refs/heads/claude/epic-pascal-vnkffh.zip
echo.
pause
exit /b 1
