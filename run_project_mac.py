import os
import subprocess
import platform

# 현재 운영체제 확인
CURRENT_OS = platform.system()

project_root = os.getcwd()
backend_path = os.path.join(project_root, "backend")
frontend_path = os.path.join(project_root, "frontend")

print("📁 프로젝트 루트:", project_root)
print("✅ main.py 존재:", os.path.exists(os.path.join(backend_path, "main.py")))

if CURRENT_OS == "Windows":
    print("💻 Windows 환경에서 실행합니다.")
    venv_activate = os.path.join(backend_path, "venv", "Scripts", "activate.bat")
    
    # 백엔드 실행 (Windows)
    subprocess.Popen(
        f'start cmd /k "cd /d {backend_path} && call {venv_activate} && OMP_NUM_THREADS=1 python main.py"',
        shell=True
    )
    # 프론트엔드 실행 (Windows)
    subprocess.Popen(
        f'start cmd /k "cd /d {frontend_path} && flutter run -d chrome"',
        shell=True
    )

elif CURRENT_OS == "Darwin": # "Darwin"은 macOS를 의미합니다.
    print("🍎 macOS 환경에서 실행합니다.")
    venv_activate = os.path.join(backend_path, "venv", "bin", "activate")
    
    # 2. AppleScript에서 따옴표가 깨지지 않도록 경로를 백슬래시(\)로 이스케이프 처리합니다.
    backend_command = f'cd \\"{backend_path}\\" && . \\"{venv_activate}\\" && OMP_NUM_THREADS=1 python3 main.py'
    subprocess.Popen(
        ['osascript', '-e', f'tell app "Terminal" to do script "{backend_command}"'],
    )
    
    frontend_command = f'cd \\"{frontend_path}\\" && flutter run -d chrome'
    subprocess.Popen(
        ['osascript', '-e', f'tell app "Terminal" to do script "{frontend_command}"'],
    )
else:
    print(f"❌ 지원되지 않는 운영체제입니다: {CURRENT_OS}")

input("\n✅ 실행 완료! (새로운 터미널 창에서 서버와 앱이 실행됩니다)\n✅ 이 창을 닫으려면 Enter를 누르세요...")