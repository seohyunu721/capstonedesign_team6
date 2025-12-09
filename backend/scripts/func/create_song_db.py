import os
import glob
import librosa
import numpy as np
import json
import joblib
import musicbrainzngs
import requests
import spotipy
import sys
from spotipy.oauth2 import SpotifyClientCredentials

# --- 1. 경로 설정 ---
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(SCRIPTS_DIR) == 'func':
    SCRIPTS_DIR = os.path.dirname(SCRIPTS_DIR) 
BACKEND_DIR = os.path.dirname(SCRIPTS_DIR)
sys.path.append(BACKEND_DIR)

DATA_DIR = os.path.join(BACKEND_DIR, 'data')
MODELS_DIR = os.path.join(BACKEND_DIR, 'models')

# utils.py에서 제목 정제 함수 불러오기
try:
    from app.utils import clean_song_title
except ImportError:
    print("오류: 'backend/app/utils.py'에서 'clean_song_title' 함수를 찾을 수 없습니다.")
    exit()

# --- 2. 스포티파이 API 설정 ---
CLIENT_ID = "a2c4860d3fd5488588e05b1e90f76b78"
CLIENT_SECRET = "1d8ac11f5f594384a31779cfe17a2941"
try:
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET))
    print("✅ 스포티파이 API 인증 성공!")
except Exception as e:
    print(f"⚠️ 스포티파이 인증 실패: {e}.")
    sp = None

# --- 3. Librosa 장르 분류 모델 로드 (2순위 예비용) ---
try:
    GENRE_MODEL = joblib.load(os.path.join(MODELS_DIR, "genre_classifier.pkl"))
    GENRE_LABELS = ['blues', 'classical', 'country', 'disco', 'hiphop', 'jazz', 'metal', 'pop', 'reggae', 'rock']
    print("✅ Librosa 장르 분류 모델 로딩 완료!")
except Exception as e:
    print(f"⚠️ Librosa 장르 분류 모델 로드 실패: {e}")
    GENRE_MODEL = None

# --- 4. 분석 함수 정의 ---
def analyze_vocal_range(file_path):
    """librosa.pyin을 사용해 더 정확하게 음역대를 분석하는 함수"""
    try:
        y, sr = librosa.load(file_path, sr=16000)

        # 노이즈 줄이는 코드 (짧은 무음 구간 제거)
        y, _ = librosa.effects.trim(y, top_db=30)

        rms = np.sqrt(np.mean(y**2))
        
        if len(y) < sr * 0.5:
            print(f"[경고] {file_path} 길이가 너무 짧음")
            return None, None
        
       
        if rms < 0.005:
            print(f"[경고] {file_path} 음량이 너무 작습니다 (rms={rms:.4f})")
            return None, None

        
        
        # 1. pYIN 알고리즘으로 기본 주파수(F0) 추정
        # fmin/fmax로 사람 목소리의 합리적인 범위만 탐색하도록 제한
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y,
            sr=sr,
            fmin=librosa.note_to_hz('A1'),  # 55Hz
            fmax=librosa.note_to_hz('C8'), 
            # fmin=librosa.note_to_hz('C2'), # 최저음 (약 65Hz)
            # fmax=librosa.note_to_hz('C7'),
            frame_length=2048,
            hop_length=1024  # 최고음 (약 2093Hz)
        )
        
        # 2. '노래가 불린 구간(voiced)'의 유효한 음높이 값만 추출
        valid_pitches = f0[voiced_flag]

        if valid_pitches is None or valid_pitches.size == 0:
            return None, None
            
        # 3. NaN 값 제거 (pYIN 결과에 포함될 수 있음)
        valid_pitches = valid_pitches[~np.isnan(valid_pitches)]
        if valid_pitches.size == 0: return None, None
        min_freq, max_freq = np.percentile(valid_pitches, 5), np.percentile(valid_pitches, 95)
        return librosa.hz_to_note(min_freq), librosa.hz_to_note(max_freq)
    except Exception as e:
        print(f"'{os.path.basename(file_path)}' 음역대 분석 중 오류: {e}")
        return None, None
    


def get_song_info_from_spotify(song_title, singer_name):
    """스포티파이 API로 장르와 발매 연도를 가져옵니다."""
    if not sp: return [], None
    try:
        search_query = f'track:{song_title} artist:{singer_name}'
        results = sp.search(q=search_query, type='track', limit=1)
        if not results['tracks']['items']:
            print(f"    - ⚠️ 스포티파이 검색 실패: '{singer_name} - {song_title}'")
            return ["정보 없음"], None
        track = results['tracks']['items'][0]
        artist_id = track['artists'][0]['id']
        album_id = track['album']['id']
        artist_info = sp.artist(artist_id)
        genres = artist_info['genres'] if artist_info['genres'] else ["정보 없음"]
        album_info = sp.album(album_id)
        release_date_str = album_info.get('release_date')
        release_year = None
        if release_date_str:
            try:
                year_part = release_date_str[:4]
                if year_part.isdigit():
                    release_year = int(year_part)
            except Exception as year_e:
                print(f"    - ⚠️ 연도 변환 중 오류: {release_date_str} ({year_e})")
        return genres, release_year
    except Exception as e:
        print(f"    - ⚠️ 스포티파이 API 요청 오류: {e}")
        return [], None

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

def get_genre_with_librosa(audio_file_path):
    """Librosa 자체 모델로 장르를 예측하는 함수"""
    if not GENRE_MODEL:
        return ["정보 없음"]
    try:
        features = extract_librosa_features(audio_file_path).reshape(1, -1)
        prediction_index = GENRE_MODEL.predict(features)[0]
        genre = GENRE_LABELS[prediction_index]
        return [genre]
    except Exception as e:
        print(f"    - ⚠️ Librosa 분석 오류: {e}")
        return ["분석 실패"]

# --- 5. 메인 로직 ---
songs_database = {}
save_path = os.path.join(DATA_DIR, "songs_db.json")
if os.path.exists(save_path):
    try:
        with open(save_path, 'r', encoding='utf-8') as f:
            songs_database = json.load(f)
        print("✅ 기존 songs_db.json 파일을 불러왔습니다. 데이터를 업데이트합니다.")
    except Exception as e:
        print(f"⚠️ 기존 DB 로드 실패, 새로 생성합니다: {e}")

SINGER_NAME_MAP = {
    "sungsikyung": "성시경",
    "kwill": "케이윌",
    "limchangjung": "임창정",
    "iu": "아이유",
    "younha": "윤하",
    "LEE HI ": "이하이",
    "폴킴 (Paul Kim) ": "폴킴",
    "HuhGak": "허각"
}

# 의도하신 대로 *_song으로 유지
singer_dirs = glob.glob(os.path.join(DATA_DIR, '*_songs'))

print("\n🎶 노래 음역대, 장르, 연도 데이터베이스 생성을 시작합니다...")
print("-" * 50)

for singer_dir in singer_dirs:
    singer_name_from_folder = os.path.basename(singer_dir).replace("_songs", "")
    
    # API 검색용 이름 (e.g., "성시경")을 가져옴
    singer_name_for_api = SINGER_NAME_MAP.get(singer_name_from_folder, singer_name_from_folder)
    print(f"🎤 가수 '{singer_name_for_api}' (폴더: {singer_name_from_folder})의 노래들을 분석 중...")
    
    # DB의 key는 API 검색용 이름(최종 이름)으로 통일
    if singer_name_for_api not in songs_database:
        songs_database[singer_name_for_api] = []
    
    # 이미 처리된 곡 목록 캐싱: 연도가 있으면 스킵, 연도 없으면 재시도
    existing_map = {
        entry.get("title"): entry
        for entry in songs_database[singer_name_for_api]
    }
    
    for file_path in glob.glob(os.path.join(singer_dir, '**', '*.wav'), recursive=True):
        original_title = os.path.splitext(os.path.basename(file_path))[0]
        
        # --- [수정] clean_song_title 함수 호출 방식 수정 (인자 1개 전달) ---
        cleaned_title = clean_song_title(original_title) 
        
        # 이미 DB에 있고, 연도가 채워져 있으면 건너뜀
        if cleaned_title in existing_map:
            existing_entry = existing_map[cleaned_title]
            if existing_entry.get("year") not in (None, "정보 없음"):
                print(f"   ⏭️  스킵 (이미 있음, 연도 존재): {cleaned_title}")
                continue
        
        lowest, highest = analyze_vocal_range(file_path)
        
        # 두 가지 장르 분석 모두 호출
        genres_api, year = get_song_info_from_spotify(cleaned_title, singer_name_for_api)
        genres_model = get_genre_with_librosa(file_path)
        
        if lowest and highest:
            # DB에 저장할 최종 항목
            new_entry = {
                "title": cleaned_title,
                "lowest_note": lowest,
                "highest_note": highest,
                "genres_api": genres_api,
                "genres_model": genres_model,
                "year": year
            }

            # DB 업데이트 로직 (API용 이름 기준)
            found = False
            for song_entry in songs_database[singer_name_for_api]:
                if song_entry.get('title') == cleaned_title:
                    song_entry.update(new_entry) # 정보 업데이트
                    found = True
                    break
            if not found:
                 songs_database[singer_name_for_api].append(new_entry) # 새로 추가
                 
            print(f"    - ✅ '{cleaned_title}' 분석 완료: {lowest} ~ {highest}, API 장르: {genres_api}, 모델 장르: {genres_model}, 연도: {year}")

# --- 6. 파일 저장 ---
with open(save_path, 'w', encoding='utf-8') as f:
    json.dump(songs_database, f, ensure_ascii=False, indent=4)
print(f"\n🎉 노래 DB 생성 완료! 파일 위치: {save_path}")
