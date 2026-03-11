@echo off
chcp 65001 >nul 2>nul

echo ======================================
echo.
echo   부루마블 보드게임 설치 확인
echo.
echo ======================================
echo.

echo [1/3] Python 설치 확인 중...
python --version >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo   [오류] Python이 설치되어 있지 않습니다.
    echo.
    echo   설치 방법:
    echo     1. https://www.python.org/downloads/ 접속
    echo     2. Download Python 클릭하여 설치
    echo     3. 설치 시 Add Python to PATH 반드시 체크
    echo     4. 설치 후 이 파일을 다시 실행하세요
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^^^>^^^&1') do set PYVER=%%i
echo   확인됨: %PYVER%
echo.

echo [2/3] Tkinter 확인 중...
python -c "import tkinter" >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo   [오류] Tkinter가 설치되어 있지 않습니다.
    echo   Python 재설치 시 tcl/tk and IDLE 옵션을 체크하세요.
    echo.
    pause
    exit /b 1
)
echo   확인됨: Tkinter 정상
echo.

echo [3/3] 문제 파일 확인 중...
if exist "questions.txt" (
    echo   확인됨: questions.txt 존재
) else (
    echo   [주의] questions.txt 파일이 없습니다.
    echo   게임 설정에서 문제 파일을 직접 지정하거나
    echo   이 폴더에 questions.txt 파일을 만드세요.
)
echo.

echo ======================================
echo.
echo   설치 확인 완료!
echo.
echo   실행 방법: run.bat 더블클릭
echo   또는: python main.py
echo.
echo ======================================
echo.
pause
