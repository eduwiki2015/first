@echo off
title Naver Blog Automation

rem Streamlit 최초 실행 시 이메일 질문이 나오지 않도록 설정
if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit"
if not exist "%USERPROFILE%\.streamlit\credentials.toml" (
    echo [general]> "%USERPROFILE%\.streamlit\credentials.toml"
    echo email = "">> "%USERPROFILE%\.streamlit\credentials.toml"
)

echo 프로그램을 시작합니다. 잠시 후 브라우저가 자동으로 열립니다...
echo 이 검은 창은 끄지 마세요. 프로그램을 종료하려면 이 창을 닫으면 됩니다.
echo.
python -m streamlit run app.py
pause
