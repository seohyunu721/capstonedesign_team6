import os
import glob
import librosa
import numpy as np
import json
import joblib
import musicbrainzngs
import requests

# --- 1. 설정 ---
# MusicBrainz API 설정 (your-email@example.com 부분에 본인 이메일 입력)
musicbrainzngs.set_useragent("Vocalize-Capstone-App", "0.1", "dbqls3141@gmail.com")

# 경로 설정
# 현재 파일(create_song_db.py)이 있는 func 폴더
FUNC_DIR = os.path.dirname(os.path.abspath(__file__))
# func 폴더의 부모인 scripts 폴더
SCRIPTS_DIR = os.path.dirname(FUNC_DIR)
# scripts 폴더의 부모인 backend 폴더 (올바른 경로)
BACKEND_DIR = os.path.dirname(SCRIPTS_DIR) 

DATA_DIR = os.path.join(BACKEND_DIR, 'data')
MODELS_DIR = os.path.join(BACKEND_DIR, 'models')

# Librosa 기반의 미리 학습된 장르 분류 모델 로드
try:
    GENRE_MODEL = joblib.load(os.path.join(MODELS_DIR, "genre_classifier.pkl"))
    GENRE_LABELS = ['blues', 'classical', 'country', 'disco', 'hiphop', 'jazz', 'metal', 'pop', 'reggae', 'rock']
    print("✅ Librosa 장르 분류 모델 로딩 완료!")
except Exception as e:
    print(f"⚠️ Librosa 장르 분류 모델 로드 실패: {e}")
    GENRE_MODEL = None

# --- 2. 분석 함수 정의 ---
def analyze_vocal_range(file_path):
    """Librosa로 음역대 분석"""
    try:
        y, sr = librosa.load(file_path, sr=16000)
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        valid_pitches = [pitches[magnitudes[:, t].argmax(), t] for t in range(pitches.shape[1]) if pitches[magnitudes[:, t].argmax(), t] > 0]
        if not valid_pitches: return None, None
        min_freq, max_freq = np.percentile(valid_pitches, 5), np.percentile(valid_pitches, 95)
        return librosa.hz_to_note(min_freq), librosa.hz_to_note(max_freq)
    except Exception as e:
        print(f"    - ⚠️ 음역대 분석 오류: {os.path.basename(file_path)} ({e})")
        return None, None

def extract_librosa_features(file_path):
    """Librosa 장르 분류를 위한 특징 추출"""
    try:
        y, sr = librosa.load(file_path, mono=True, duration=30)
        mfccs = np.mean(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20).T, axis=0)
        chroma = np.mean(librosa.feature.chroma_stft(y=y, sr=sr).T, axis=0)
        contrast = np.mean(librosa.feature.spectral_contrast(y=y, sr=sr).T, axis=0)
        return np.hstack([mfccs, chroma, contrast])
    except Exception as e:
        print(f"    - ⚠️ Librosa 특징 추출 오류: {e}")
        return None

def get_genre_hybrid(artist_name, song_title, audio_file_path):
    """AcousticBrainz를 먼저 시도하고, 실패 또는 '정보 없음'일 경우 Librosa로 예측"""
    # 1순위: AcousticBrainz API
    try:
        search_result = musicbrainzngs.search_recordings(artist=artist_name, recording=song_title, limit=1)
        if search_result['recording-list']:
            recording_id = search_result['recording-list'][0]['id']
            ab_url = f"https://acousticbrainz.org/api/v1/{recording_id}/high-level"
            response = requests.get(ab_url, timeout=200) # 5초 타임아웃
            if response.status_code == 200:
                data = response.json()
                genre = data.get('genre_rosamerica', {}).get('value')
                if genre and genre != '정보 없음':
                    print(f"    - ✅ AcousticBrainz 성공: {genre}")
                    return [genre]
        print(f"    - ⚠️ AcousticBrainz 정보 없음. Librosa로 전환합니다.")
    except Exception as e:
        print(f"    - ⚠️ AcousticBrainz API 오류. Librosa로 전환합니다: {e}")

    # 2순위: Librosa 자체 모델
    if GENRE_MODEL:
        try:
            features = extract_librosa_features(audio_file_path)
            if features is not None:
                features = features.reshape(1, -1)
                prediction_index = GENRE_MODEL.predict(features)[0]
                genre = GENRE_LABELS[prediction_index]
                print(f"    - ✅ Librosa 성공: {genre}")
                return [genre]
        except Exception as e:
            print(f"    - ⚠️ Librosa 분석 오류: {e}")
    
    return ["정보 없음"]

# --- 3. 메인 로직 ---
songs_database = {}
save_path = os.path.join(DATA_DIR, "songs_db.json")
# ... (기존 DB 로드 로직은 동일)

singer_dirs = glob.glob(os.path.join(DATA_DIR, '*_song'))
print("\n🎶 노래 음역대 및 장르 데이터베이스 생성을 시작합니다...")
print("-" * 50)

for singer_dir in singer_dirs:
    singer_name = os.path.basename(singer_dir).replace("_song", "")
    print(f"🎤 가수 '{singer_name}'의 노래들을 분석 중...")
    
    if singer_name not in songs_database:
        songs_database[singer_name] = []
    
    for file_path in glob.glob(os.path.join(singer_dir, '**', '*.wav'), recursive=True):
        song_title = os.path.splitext(os.path.basename(file_path))[0].replace('_vocals', '')
        
        lowest, highest = analyze_vocal_range(file_path)
        genres = get_genre_hybrid(singer_name, song_title, file_path)
        
        if lowest and highest:
            # ... (기존 DB 업데이트 및 추가 로직은 동일)
            found = False
            for song_entry in songs_database[singer_name]:
                if song_entry.get('title') == song_title:
                    song_entry['lowest_note'] = lowest
                    song_entry['highest_note'] = highest
                    song_entry['genres'] = genres
                    found = True
                    break
            if not found:
                 songs_database[singer_name].append({
                    "title": song_title,
                    "lowest_note": lowest,
                    "highest_note": highest,
                    "genres": genres
                })
            print(f"    - '{song_title}' 분석 완료: {lowest} ~ {highest}, 장르: {genres}")

# --- 4. 파일 저장 ---
with open(save_path, 'w', encoding='utf-8') as f:
    json.dump(songs_database, f, ensure_ascii=False, indent=4)
print(f"\n🎉 노래 DB 생성 완료! 파일 위치: {save_path}")