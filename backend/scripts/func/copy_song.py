import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp
import os
import sys
import re
import glob
import unicodedata
import json
# 경로 설정
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(SCRIPTS_DIR) == 'func':
    SCRIPTS_DIR = os.path.dirname(SCRIPTS_DIR)
BACKEND_DIR = os.path.dirname(SCRIPTS_DIR)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(BACKEND_DIR)

try:
    from app.utils import clean_song_title
except ImportError:
    print("⚠️ app.utils.clean_song_title을 찾을 수 없습니다.")
    clean_song_title = None

# ==========================================
# 1. 설정
# ==========================================
CLIENT_ID = "a2c4860d3fd5488588e05b1e90f76b78"
CLIENT_SECRET = "1d8ac11f5f594384a31779cfe17a2941"

# 검색 대신 '아티스트 ID'를 직접 사용합니다. (100% 정확함)
# 아이유(IU)의 Spotify ID: 3HqSLMAZ3g3d5poNaI7GOU
TARGET_ARTIST_ID = "3uCDicSmenMBtsKb5A51dd"
TARGET_ARTIST_NAME = "전상근"  # 출력용 이름    


def _safe_name(name: str) -> str:
    """파일/폴더에 안전하게 사용할 수 있도록 이름을 정제"""
    name = unicodedata.normalize("NFKD", name).strip()
    name = re.sub(r"[<>:\"/\\|?*]", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


# 아티스트명을 기준으로 폴더를 고정
SAFE_ARTIST_NAME = _safe_name(TARGET_ARTIST_NAME)
# BASE_DIR는 backend 디렉터리이므로 중복 없이 data/original 아래로 저장
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, "data", "original", SAFE_ARTIST_NAME)

# ==========================================
# 2. Spotify API: ID로 탑 10곡 정보 가져오기
# ==========================================
def get_spotify_top_tracks_by_id(artist_id, artist_name):
    # 인증 설정
    client_credentials_manager = SpotifyClientCredentials(
        client_id=CLIENT_ID, 
        client_secret=CLIENT_SECRET
    )
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    print(f"🔍 '{artist_name}' (ID: {artist_id})의 정보를 가져오는 중...")

    try:
        # 검색(search) 단계 없이 바로 탑 트랙을 요청합니다.
        top_tracks = sp.artist_top_tracks(artist_id, country='KR')
        
        track_list = []
        print(f"\n🎵 {artist_name}의 Top 10 트랙:")
        
        if not top_tracks['tracks']:
            print("❌ 곡 정보를 가져올 수 없습니다. 국가 설정(KR)을 확인하거나 아티스트 ID를 확인하세요.")
            return []

        for idx, track in enumerate(top_tracks['tracks']):
            # 검색어 생성: 가수 - 노래제목 (Official Audio)
            query = f"{track['artists'][0]['name']} - {track['name']} official audio"
            track_list.append(query)
            print(f"{idx+1}. {track['name']}")
        
        return track_list

    except Exception as e:
        print(f"❌ Spotify API 오류 발생: {e}")
        return []

# ==========================================
# 3. yt-dlp: 유튜브 검색 및 MP3 다운로드
# ==========================================
def download_tracks_from_youtube(search_queries):
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        # 다운로드 파일을 지정한 가수 폴더에 저장
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
        'quiet': True,
        'default_search': 'ytsearch1', # 검색 결과 1순위 자동 선택
        'noplaylist': True,
    }

    print("\n🚀 다운로드를 시작합니다...\n")
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for query in search_queries:
            try:
                print(f"📥 다운로드 중: {query} ...")
                ydl.download([query])
                print("   -> 완료!")
            except Exception as e:
                print(f"   -> ❌ 실패: {e}")

# ==========================================
# 4. 파일명 정제 함수
# ==========================================
def clean_downloaded_filenames():
    """다운로드된 파일들의 이름을 정제합니다."""
    if not os.path.exists(DOWNLOAD_FOLDER):
        return
    
    print("\n🧹 다운로드된 파일명 정제 중...")
    
    audio_files = glob.glob(os.path.join(DOWNLOAD_FOLDER, "*.mp3")) + \
                  glob.glob(os.path.join(DOWNLOAD_FOLDER, "*.wav")) + \
                  glob.glob(os.path.join(DOWNLOAD_FOLDER, "*.m4a"))
    
    renamed_count = 0
    for old_path in audio_files:
        filename = os.path.basename(old_path)
        name, ext = os.path.splitext(filename)
        
        # 파일명 정제 (가수명을 고정해 포함)
        if clean_song_title:
            cleaned_title = clean_song_title(name)
        else:
            cleaned_title = re.sub(r'\[.*?\]|\(.*?\)', '', name)
            cleaned_title = re.sub(r'\s+', ' ', cleaned_title).strip()
        
        # "가수명 - 제목" 형태로 통일
        new_title = f"{SAFE_ARTIST_NAME} - {cleaned_title}"
        new_filename = new_title + ext
        new_path = os.path.join(DOWNLOAD_FOLDER, new_filename)
        
        if filename != new_filename:
            try:
                # 중복 파일명 처리
                if os.path.exists(new_path):
                    base, ext2 = os.path.splitext(new_filename)
                    counter = 1
                    while os.path.exists(new_path):
                        new_filename = f"{base}_{counter}{ext2}"
                        new_path = os.path.join(DOWNLOAD_FOLDER, new_filename)
                        counter += 1
                
                os.rename(old_path, new_path)
                print(f"  ✅ {filename} -> {new_filename}")
                renamed_count += 1
            except Exception as e:
                print(f"  ❌ {filename} 이름 변경 실패: {e}")
    
    if renamed_count > 0:
        print(f"✅ {renamed_count}개 파일명 정제 완료!")
    else:
        print("ℹ️ 정제할 파일이 없습니다.")

# ==========================================
# 5. 메인 실행 함수
# ==========================================
if __name__ == "__main__":
    # 1. Spotify ID로 곡 목록 가져오기
    top_songs = get_spotify_top_tracks_by_id(TARGET_ARTIST_ID, TARGET_ARTIST_NAME)
    
    if top_songs:
        # 2. 유튜브에서 검색해서 다운로드하기
        download_tracks_from_youtube(top_songs)
        
        # 3. 다운로드된 파일명 정제
        clean_downloaded_filenames()
        
        print(f"\n✨ 모든 작업이 완료되었습니다! '{DOWNLOAD_FOLDER}' 폴더를 확인하세요.")