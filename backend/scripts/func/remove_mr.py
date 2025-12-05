import os
import subprocess
import glob
import shutil  # 파일/폴더 관리를 위한 라이브러리
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# 선택적 GPU 사용 감지
try:
    import torch
    HAS_TORCH = True
except Exception:
    HAS_TORCH = False

# --- 설정 ---
# 루트 경로
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# 원본 음원 파일이 있는 폴더 (MR 제거 대상)
INPUT_DIR = os.path.join(BASE_DIR, "data", "original")

# 최종 보컬 파일을 저장할 기본 폴더 (train.py가 읽는 위치: data/*_songs)
OUTPUT_BASE_DIR = os.path.join(BASE_DIR, "data")

# 성능 최적화 옵션
USE_GPU = True  # GPU 사용 여부 (CUDA가 있으면 자동 감지)
USE_FAST_MODEL = False  # True: 더 빠른 모델 사용 (품질 약간 낮음), False: 고품질 모델
MAX_WORKERS = 2  # 병렬 처리 개수 (CPU 코어 수에 맞게 조정, 너무 많으면 메모리 부족)


def pick_device():
    """사용 가능한 디바이스 결정"""
    if USE_GPU and HAS_TORCH and torch.cuda.is_available():
        return "cuda"
    return "cpu"
# ------------

def process_single_file(file_path):
    """단일 파일을 처리하는 함수 (병렬 처리용)"""
    try:
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        parent_dir = os.path.basename(os.path.dirname(file_path))
        if parent_dir and parent_dir != "original":
            singer_name_raw = parent_dir
        else:
            singer_name_raw = base_name.split('-')[0]
        singer_name = singer_name_raw + "_songs"
        singer_output_dir = os.path.join(OUTPUT_BASE_DIR, singer_name)
        os.makedirs(singer_output_dir, exist_ok=True)
        
        # 이미 처리된 파일인지 확인
        final_vocal_path = os.path.join(singer_output_dir, f"{base_name}_vocals.wav")
        if os.path.exists(final_vocal_path):
            print(f"⏭️  이미 처리됨: {os.path.basename(file_path)}")
            return True, base_name
        
        temp_output_dir = os.path.join(singer_output_dir, "temp_separated")
        
        # 모델 선택: 빠른 모델 vs 고품질 모델
        model_name = "htdemucs" if USE_FAST_MODEL else "htdemucs_ft"
        
        # 디바이스 결정
        device = pick_device()

        # 명령어 구성
        command = [
            sys.executable, "-m", "demucs",
            "-n", model_name,
            "--two-stems=vocals",
            "-o", temp_output_dir,
            file_path,
            "--device", device
        ]
        
        start_time = time.time()
        print(f"🔄 처리 시작: {os.path.basename(file_path)}")
        
        # Demucs 명령 실행 (CUDA 실패 시 CPU로 재시도)
        try:
            result = subprocess.run(
                command, 
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            if device == "cuda":
                print("⚠️ CUDA 실패, CPU로 재시도합니다...")
                command[-1] = "cpu"  # --device 값 교체
                result = subprocess.run(
                    command, 
                    check=True,
                    capture_output=True,
                    text=True
                )
            else:
                raise
        
        # 보컬 파일 경로 찾기
        vocal_file_path = os.path.join(temp_output_dir, model_name, base_name, "vocals.wav")
        
        if os.path.exists(vocal_file_path):
            # 최종 위치로 이동
            shutil.move(vocal_file_path, final_vocal_path)
            
            # 원본 파일 삭제
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # 임시 폴더 정리
            model_output_dir = os.path.join(temp_output_dir, model_name)
            if os.path.exists(model_output_dir):
                shutil.rmtree(model_output_dir)
            
            elapsed = time.time() - start_time
            print(f"✅ 완료 ({elapsed:.1f}초): {os.path.basename(file_path)}")
            return True, base_name
        else:
            print(f"❌ 보컬 파일을 찾을 수 없음: {base_name}")
            return False, base_name
            
    except subprocess.CalledProcessError as e:
        print(f"❌ 처리 실패: {os.path.basename(file_path)} - {e}")
        if e.stderr:
            print(f"   오류 메시지: {e.stderr[:200]}")
        return False, os.path.basename(file_path)
    except Exception as e:
        print(f"❌ 예기치 못한 오류: {os.path.basename(file_path)} - {e}")
        return False, os.path.basename(file_path)


# 결과 폴더가 없으면 생성
os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)

# 처리할 음원 파일 목록 가져오기 (하위 폴더까지 모두 검색)
audio_files = glob.glob(os.path.join(INPUT_DIR, '**', '*.wav'), recursive=True) + \
              glob.glob(os.path.join(INPUT_DIR, '**', '*.mp3'), recursive=True) + \
              glob.glob(os.path.join(INPUT_DIR, '**', '*.m4a'), recursive=True)

if not audio_files:
    print(f"'{INPUT_DIR}' 폴더에 처리할 음원 파일이 없습니다.")
    sys.exit(0)

# 이미 처리된 파일 필터링
files_to_process = []
for file_path in audio_files:
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    parent_dir = os.path.basename(os.path.dirname(file_path))
    if parent_dir and parent_dir != "original":
        singer_name_raw = parent_dir
    else:
        singer_name_raw = base_name.split('-')[0]
    singer_name = singer_name_raw + "_songs"
    singer_output_dir = os.path.join(OUTPUT_BASE_DIR, singer_name)
    final_vocal_path = os.path.join(singer_output_dir, f"{base_name}_vocals.wav")
    
    if not os.path.exists(final_vocal_path):
        files_to_process.append(file_path)

if not files_to_process:
    print("✅ 모든 파일이 이미 처리되었습니다!")
    sys.exit(0)

print(f"📊 총 {len(audio_files)}개 파일 중 {len(files_to_process)}개 처리 필요")
print(f"⚙️  설정: 모델={('빠른 모델' if USE_FAST_MODEL else '고품질 모델')}, GPU={USE_GPU}, 병렬={MAX_WORKERS}개")
print(f"🚀 MR 제거를 시작합니다...\n")

start_total = time.time()
success_count = 0
fail_count = 0

# 병렬 처리 또는 순차 처리
if MAX_WORKERS > 1 and len(files_to_process) > 1:
    # 병렬 처리
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_single_file, file_path): file_path 
                  for file_path in files_to_process}
        
        for future in as_completed(futures):
            success, name = future.result()
            if success:
                success_count += 1
            else:
                fail_count += 1
else:
    # 순차 처리
    for file_path in files_to_process:
        success, name = process_single_file(file_path)
        if success:
            success_count += 1
        else:
            fail_count += 1

total_time = time.time() - start_total

print(f"\n{'='*50}")
print(f"✅ 성공: {success_count}개")
print(f"❌ 실패: {fail_count}개")
print(f"⏱️  총 소요 시간: {total_time/60:.1f}분 ({total_time:.1f}초)")
if files_to_process:
    print(f"📈 평균 처리 시간: {total_time/len(files_to_process):.1f}초/파일")
print(f"{'='*50}")
print(f"결과물은 '{OUTPUT_BASE_DIR}' 폴더 안에 저장되었습니다.")