import os
import glob
import librosa
import numpy as np
import json

# --- 경로 설정 ---
# 이 스크립트 파일의 위치를 기준으로 경로를 잡습니다.
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPTS_DIR)
DATA_DIR = os.path.join(BACKEND_DIR, '../data')
# -----------------

def analyze_vocal_range(file_path):
    """오디오 파일에서 음역대를 분석하는 함수"""
    try:
        y, sr = librosa.load(file_path, sr=16000)
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        
        valid_pitches = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                valid_pitches.append(pitch)

        if not valid_pitches: return None, None

        min_freq = np.percentile(valid_pitches, 5)
        max_freq = np.percentile(valid_pitches, 95)
        
        lowest_note = librosa.hz_to_note(min_freq)
        highest_note = librosa.hz_to_note(max_freq)
        
        return lowest_note, highest_note
    except Exception as e:
        print(f"'{os.path.basename(file_path)}' 분석 중 오류: {e}")
        return None, None

# --- 메인 로직 ---
songs_database = {}
# 기존 DB가 존재하면 읽어와 유지
save_path = os.path.join(DATA_DIR, "songs_db.json")
if os.path.exists(save_path):
    try:
        with open(save_path, 'r', encoding='utf-8') as f:
            existing = json.load(f)
            if isinstance(existing, dict):
                songs_database = existing
    except Exception as e:
        print(f"기존 DB 로드 실패, 새로 생성합니다: {e}")
singer_dirs = glob.glob(os.path.join(DATA_DIR, '*_song'))

print("노래 음역대 데이터베이스 생성을 시작합니다...")

for singer_dir in singer_dirs:
    singer_name = os.path.basename(singer_dir).replace("_song", "")
    print(f"--> '{singer_name}'의 노래들을 분석 중...")
    
    if singer_name not in songs_database or not isinstance(songs_database.get(singer_name), list):
        songs_database[singer_name] = []
    
    for file_path in glob.glob(os.path.join(singer_dir, '**', '*.wav'), recursive=True):
        song_title = os.path.splitext(os.path.basename(file_path))[0]
        lowest, highest = analyze_vocal_range(file_path)

        if lowest and highest:
            # 중복 제목 방지: 같은 제목이 있으면 갱신, 없으면 추가
            existing_list = songs_database[singer_name]
            found = False
            for item in existing_list:
                if isinstance(item, dict) and item.get("title") == song_title:
                    item["lowest_note"] = lowest
                    item["highest_note"] = highest
                    found = True
                    break
            if not found:
                existing_list.append({
                    "title": song_title,
                    "lowest_note": lowest,
                    "highest_note": highest
                })
            print(f"    - '{song_title}' 분석 완료: {lowest} ~ {highest}")
# --- 파일 저장 ---
with open(save_path, 'w', encoding='utf-8') as f:
    json.dump(songs_database, f, ensure_ascii=False, indent=4)

print(f"\n노래 DB 생성 완료! 파일 위치: {save_path}")