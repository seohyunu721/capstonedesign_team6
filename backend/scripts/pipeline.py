import os
import subprocess

# --- 경로 설정 ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(BACKEND_DIR, "data")
MODELS_DIR = os.path.join(BACKEND_DIR, "models")

# --- 단계별 실행 ---
def run_remove_mr():
    print("\n[1/5] MR 제거 스크립트 실행 중...")
    remove_mr_script = os.path.join(SCRIPT_DIR, "remove_mr.py")
    result = subprocess.run(["python3", remove_mr_script], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError("MR 제거 스크립트 실행 중 오류 발생!")

def run_train_xvector():
    print("\n[2/5] X-vector 학습 스크립트 실행 중...")
    train_script = os.path.join(SCRIPT_DIR, "train.py")
    result = subprocess.run(["python3", train_script], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError("X-vector 학습 스크립트 실행 중 오류 발생!")

def run_train_faiss():
    print("\n[3/5] Faiss 인덱스 생성 스크립트 실행 중...")
    train_faiss_script = os.path.join(SCRIPT_DIR, "train_faiss.py")
    result = subprocess.run(["python3", train_faiss_script], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError("Faiss 인덱스 생성 스크립트 실행 중 오류 발생!")

def run_create_song_db():
    print("\n[4/5] 노래 음역대 데이터베이스 생성 스크립트 실행 중...")
    create_song_db_script = os.path.join(SCRIPT_DIR, "create_song_db.py")
    result = subprocess.run(["python3", create_song_db_script], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError("노래 음역대 데이터베이스 생성 스크립트 실행 중 오류 발생!")

def finalize_pipeline():
    print("\n[5/5] 파이프라인 완료!")
    print("모든 작업이 성공적으로 완료되었습니다.")

# --- 메인 실행 ---
if __name__ == "__main__":
    try:
        run_remove_mr()
        run_train_xvector()
        run_train_faiss()
        run_create_song_db()
        finalize_pipeline()
    except Exception as e:
        print(f"파이프라인 실행 중 오류 발생: {e}")