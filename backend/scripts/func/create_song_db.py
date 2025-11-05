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

# --- 3. 분석 함수 정의 ---
def analyze_vocal_range(file_path):
    """librosa.pyin을 사용해 더 정확하게 음역대를 분석하는 함수"""
    try:
        y, sr = librosa.load(file_path, sr=16000)
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), hop_length=1024) 
        valid_pitches = f0[voiced_flag]
        if valid_pitches is None or valid_pitches.size == 0: return None, None
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

# --- 4. 메인 로직 ---
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

# --- [수정] 오타 수정: *_song -> *_songs ---
# 사용자님이 의도하신 대로 *_song으로 다시 수정합니다.
singer_dirs = glob.glob(os.path.join(DATA_DIR, '*_song'))

print("\n🎶 노래 음역대, 장르, 연도 데이터베이스 생성을 시작합니다...")
print("-" * 50)

for singer_dir in singer_dirs:
    # --- [수정] 오타 수정: _song -> _songs ---
    # 사용자님이 의도하신 대로 _song으로 다시 수정합니다.
    singer_name_from_folder = os.path.basename(singer_dir).replace("_song", "")
    
    singer_name_for_api = SINGER_NAME_MAP.get(singer_name_from_folder, singer_name_from_folder)
    print(f"🎤 가수 '{singer_name_for_api}' (폴더: {singer_name_from_folder})의 노래들을 분석 중...")
    
    # --- [수정] DB 키를 API용 이름으로 통일 ---
    if singer_name_for_api not in songs_database:
        songs_database[singer_name_for_api] = []
    
    for file_path in glob.glob(os.path.join(singer_dir, '**', '*.wav'), recursive=True):
        original_title = os.path.splitext(os.path.basename(file_path))[0]
        
        cleaned_title = clean_song_title(original_title)        
        
        lowest, highest = analyze_vocal_range(file_path)
        genres, year = get_song_info_from_spotify(cleaned_title, singer_name_for_api)        
        
        if lowest and highest:
            # --- [수정] DB 키를 API용 이름으로 통일 ---
            found = False
            for song_entry in songs_database[singer_name_for_api]:
                if song_entry.get('title') == cleaned_title:
                    song_entry['lowest_note'] = lowest
                    song_entry['highest_note'] = highest
                    song_entry['genres'] = genres
                    song_entry['year'] = year
                    found = True
                    break
            if not found:
                 songs_database[singer_name_for_api].append({
                    "title": cleaned_title,
                    "lowest_note": lowest,
                    "highest_note": highest,
                    "genres": genres,
                    "year": year
                })
            print(f"    - ✅ '{cleaned_title}' 분석 완료: {lowest} ~ {highest}, 장르: {genres}, 연도: {year}")

# --- 5. 파일 저장 ---
with open(save_path, 'w', encoding='utf-8') as f:
    json.dump(songs_database, f, ensure_ascii=False, indent=4)
print(f"\n🎉 노래 DB 생성 완료! 파일 위치: {save_path}")