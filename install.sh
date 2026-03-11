#!/bin/bash
# 부루마블 보드게임 - Linux/Mac 설치 스크립트

echo "======================================"
echo "  부루마블 보드게임 설치 스크립트"
echo "======================================"
echo ""

# Python3 확인
echo "[1/3] Python3 설치 확인 중..."
if command -v python3 &>/dev/null; then
    PYVER=$(python3 --version 2>&1)
    echo "  설치됨: $PYVER"
else
    echo ""
    echo "[오류] Python3이 설치되어 있지 않습니다."
    echo ""
    echo "설치 방법:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-tk"
    echo "  Fedora/RHEL:   sudo dnf install python3 python3-tkinter"
    echo "  macOS:         brew install python3 python-tk"
    echo ""
    echo "설치 후 이 스크립트를 다시 실행하세요."
    exit 1
fi
echo ""

# Tkinter 확인
echo "[2/3] Tkinter 확인 중..."
if python3 -c "import tkinter" &>/dev/null; then
    echo "  Tkinter 정상 확인"
else
    echo ""
    echo "[오류] Tkinter가 설치되어 있지 않습니다."
    echo ""
    echo "설치 방법:"
    echo "  Ubuntu/Debian: sudo apt install python3-tk"
    echo "  Fedora/RHEL:   sudo dnf install python3-tkinter"
    echo "  macOS:         brew install python-tk"
    echo ""
    exit 1
fi
echo ""

# 문제 파일 확인
echo "[3/3] 문제 파일 확인 중..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/questions.txt" ]; then
    echo "  questions.txt 파일 확인 완료"
else
    echo "  [주의] questions.txt 파일이 없습니다."
    echo "  게임 실행 후 설정에서 문제 파일을 지정하거나,"
    echo "  이 폴더에 questions.txt 파일을 만들어주세요."
fi
echo ""

echo "======================================"
echo "  설치 확인 완료!"
echo "======================================"
echo ""
echo "게임 실행 방법:"
echo "  방법 1: ./run.sh"
echo "  방법 2: python3 main.py"
echo ""
