import os
import glob
import sys

# --- 경로 문제 해결을 위한 코드 ---
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPTS_DIR)
sys.path.append(BACKEND_DIR)
# --------------------------------

try:
    from app.utils import clean_song_title
except ImportError:
    print("오류: app/utils.py 파일 또는 clean_song_title 함수를 찾을 수 없습니다.")
    exit()

# --- 경로 설정 ---
DATA_DIR = os.path.join(BACKEND_DIR, 'data')
# -----------------

print(f"'{DATA_DIR}' 폴더 내의 모든 음원 파일 이름 정리를 시작합니다...")
print("-" * 50)

singer_dirs = glob.glob(os.path.join(DATA_DIR, '*_song'))
total_renamed_count = 0

for singer_dir in singer_dirs:
    singer_name = os.path.basename(singer_dir).replace("_song", "")
    print(f"🎤 '{singer_name}' 폴더를 처리 중...")

    audio_files = glob.glob(os.path.join(singer_dir, '**', '*.wav'), recursive=True) + \
                  glob.glob(os.path.join(singer_dir, '**', '*.mp3'), recursive=True) + \
                  glob.glob(os.path.join(singer_dir, '**', '*.m4a'), recursive=True)

    if not audio_files:
        print("  -> 처리할 음원 파일이 없습니다.")
        continue

    for old_file_path in audio_files:
        file_dir = os.path.dirname(old_file_path)
        original_filename = os.path.basename(old_file_path)
        original_title, extension = os.path.splitext(original_filename)
        
        # --- 수정된 부분: singer_name 인자 제거 ---
        new_title = clean_song_title(original_title)
        
        new_filename = new_title + extension
        new_file_path = os.path.join(file_dir, new_filename)

        if original_filename != new_filename:
            try:
                os.rename(old_file_path, new_file_path)
                print(f"  - 변경: '{original_filename}' -> '{new_filename}'")
                total_renamed_count += 1
            except Exception as e:
                print(f"  - ⚠️ 오류: '{original_filename}' 이름 변경 실패: {e}")
        else:
            print(f"  - 유지: '{original_filename}' (변경 필요 없음)")

print("-" * 50)
print(f"총 {total_renamed_count}개의 파일 이름이 변경되었습니다.")