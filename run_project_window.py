import os
import subprocess


project_root = os.getcwd()
backend_path = os.path.join(project_root, "backend")
frontend_path = os.path.join(project_root, "frontend")
venv_activate = os.path.join(backend_path, "venv", "Scripts", "activate.bat")

print("📁 프로젝트 루트:", project_root)
print("📁 백엔드 경로:", backend_path)
print("📁 프론트엔드 경로:", frontend_path)
print("📁 가상환경 activate.bat 경로:", venv_activate)

print("✅ main.py 존재:", os.path.exists(os.path.join(backend_path, "main.py")))
print("✅ activate.bat 존재:", os.path.exists(venv_activate))

project_root = os.getcwd()
backend_path = os.path.join(project_root, "backend")
frontend_path = os.path.join(project_root, "frontend")
venv_activate = os.path.join(backend_path, "venv", "Scripts", "activate.bat")

# 백엔드 실행
subprocess.Popen(
    f'start cmd /k "cd /d {backend_path} && call {venv_activate} && python main.py"',
    shell=True
)

# 프론트엔드 실행
subprocess.Popen(
    f'start cmd /k "cd /d {frontend_path} && flutter run"',
    shell=True
)

# 콘솔 유지
input("\n✅ 실행 완료! 콘솔을 닫으려면 Enter를 누르세요...")
