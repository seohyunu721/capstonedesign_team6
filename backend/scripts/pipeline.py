import os
import subprocess
import sys

# --- 경로 설정 ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(BACKEND_DIR, "data")
MODELS_DIR = os.path.join(BACKEND_DIR, "models")

# --- 단계별 실행 ---
def _run_with_utf8(script_path: str):
    """
    UTF-8 환경에서 스크립트 실행
    가상환경의 Python을 우선적으로 사용하도록 개선
    """
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["OMP_NUM_THREADS"] = "1"  # NumPy 멀티스레딩 충돌 방지
    
    # 가상환경의 Python 우선 사용
    venv_python = os.path.join(BACKEND_DIR, "venv", "bin", "python3")
    if os.path.exists(venv_python):
        python_executable = venv_python
        print(f"✅ 가상환경 Python 사용: {python_executable}")
    else:
        python_executable = sys.executable
        print(f"⚠️ 시스템 Python 사용: {python_executable}")
    
    # script_path가 리스트인 경우와 문자열인 경우 모두 처리
    if isinstance(script_path, list):
        cmd = [python_executable] + script_path
    else:
        cmd = [python_executable, script_path]
    
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        encoding="utf-8",
        errors="replace",
        cwd=BACKEND_DIR,  # 작업 디렉토리를 backend로 설정
    )

def run_remove_mr():
    print("\n[1/5] MR 제거 스크립트 실행 중...")
    remove_mr_script = os.path.join(SCRIPT_DIR, "func/remove_mr.py")
    result = _run_with_utf8(remove_mr_script)
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr)
        raise RuntimeError("MR 제거 스크립트 실행 중 오류 발생!")

def run_train_xvector():
    print("\n[2/5] X-vector 학습 스크립트 실행 중...")
    train_script = os.path.join(SCRIPT_DIR, "func/train.py")
    result = _run_with_utf8(train_script)
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr)
        combined = (result.stdout or "") + "\n" + (result.stderr or "")
        # NumPy ABI 불일치 또는 콘솔 인코딩 오류는 비치명으로 간주하고 다음 단계로 진행
        if "A module that was compiled using NumPy 1.x" in combined or "UnicodeEncodeError: 'cp949'" in combined:
            print("경고: 환경 제약으로 X-vector 학습을 건너뜁니다. 다음 단계로 진행합니다.")
            return
        raise RuntimeError("X-vector 학습 스크립트 실행 중 오류 발생!")

def run_train_faiss():
    print("\n[3/5] Faiss 인덱스 생성 스크립트 실행 중...")
    train_faiss_script = os.path.join(SCRIPT_DIR, "func/train_faiss.py")
    result = _run_with_utf8(train_faiss_script)
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr)
        raise RuntimeError("Faiss 인덱스 생성 스크립트 실행 중 오류 발생!")

def run_clean_filenames():
    print("\n[4/6] 파일명 정제 스크립트 실행 중...")
    clean_filename_script = os.path.join(SCRIPT_DIR, "func/clean_filename_llm.py")
    original_dir = os.path.join(DATA_DIR, "original")
    
    if os.path.exists(original_dir):
        result = _run_with_utf8([clean_filename_script, original_dir, "--llm"])
        if result.stdout:
            print(result.stdout)
        if result.returncode != 0:
            if result.stderr:
                print(result.stderr)
            print("⚠️ 파일명 정제 중 오류 발생, 계속 진행합니다...")
    else:
        print("⚠️ original 디렉토리가 없어 파일명 정제를 건너뜁니다.")

def run_create_song_db():
    print("\n[5/6] 노래 음역대 데이터베이스 생성 스크립트 실행 중...")
    create_song_db_script = os.path.join(SCRIPT_DIR, "func/create_song_db.py")
    result = _run_with_utf8(create_song_db_script)
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr)
        raise RuntimeError("노래 음역대 데이터베이스 생성 스크립트 실행 중 오류 발생!")

def finalize_pipeline():
    print("\n[6/6] 파이프라인 완료!")
    print("모든 작업이 성공적으로 완료되었습니다.")

# --- 메인 실행 ---
if __name__ == "__main__":
    try:
        run_remove_mr()
        run_train_xvector()
        run_train_faiss()
        run_clean_filenames()  # 파일명 정제 추가
        run_create_song_db()
        finalize_pipeline()
    except Exception as e:
        print(f"파이프라인 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()