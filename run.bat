@echo off
chcp 65001 >nul 2>nul
cd /d "%~dp0"
echo.
echo 게임을 실행합니다...
echo.
python main.py
echo.
echo === 프로그램 종료 (에러코드: %errorlevel%) ===
echo.
if exist error_log.txt (
    echo === 에러 로그 ===
    type error_log.txt
    echo.
)
pause
