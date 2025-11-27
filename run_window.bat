@echo off
setlocal

REM 프로젝트 루트로 이동 (이 파일이 있는 위치 기준)
cd /d %~dp0

echo [1/5] 가상환경 생성 중...
if not exist backend\venv (
    python -m venv backend\venv
)

echo [2/5] 가상환경 활성화 및 라이브러리 설치...
call backend\venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r backend\requirements.txt

echo [3/5] 백엔드 실행 중...
start cmd /k "cd /d backend && call venv\Scripts\activate.bat && python main.py"

echo [4/5] 프론트엔드 실행 중...
start cmd /k "cd /d frontend && flutter pub get && flutter run"

echo [5/5] 모든 작업이 실행되었습니다!
pause
