@echo off
chcp 65001 >nul
title 네이버 블로그 자동화
echo 프로그램을 시작합니다. 잠시 후 브라우저가 자동으로 열립니다...
echo (이 검은 창은 끄지 마세요. 프로그램을 종료하려면 이 창을 닫으면 됩니다.)
echo.
python -m streamlit run app.py
pause
