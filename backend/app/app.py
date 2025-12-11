import os
import shutil
import glob
import numpy as np
import joblib
import torch
import torchaudio
import faiss
import librosa
import json
import time  
import asyncio
# 추가 본 ###################
import soundfile as sf
from pydub import AudioSegment
#########################
from fastapi import FastAPI, UploadFile, File, HTTPException,Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
import httpx
import base64
from speechbrain.inference import EncoderClassifier
from torchaudio.transforms import Resample
import matplotlib
# macOS에서 GUI 백엔드가 쓰여서 발생하는 에러 방지: 반드시 pyplot 이전에 backend 설정
matplotlib.use("Agg")   # non-GUI backend (파일로 저장 전용)
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from fastapi.staticfiles import StaticFiles # <-- 추가
import yt_dlp

# --- 1. FastAPI 앱 및 모델 로딩 ---
app = FastAPI()

# [추가] 정적 파일 경로 설정
# 'backend/static/graphs' 폴더에 저장된 파일을 'http://서버주소/static/graphs/파일이름'으로 접근 가능하게 함
APP_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(APP_DIR)
MODELS_DIR = os.path.join(BACKEND_DIR, 'models')
DATA_DIR = os.path.join(BACKEND_DIR, 'data')

# --- 안전한 정적 파일 경로 재설정 (절대경로) ---
STATIC_DIR = os.path.join(BACKEND_DIR, "static")
GRAPHS_DIR = os.path.join(STATIC_DIR, "graphs")
os.makedirs(GRAPHS_DIR, exist_ok=True)
# mount StaticFiles with absolute path (덮어쓰기 허용)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
USER_TO_GTZAN_MAP = {
    "발라드": ["pop", "classical", "jazz", "blues", "k-ballad"], 
    "댄스": ["disco", "pop", "hiphop", "k-pop", "dance-pop"], 
    "R&B": ["hiphop", "jazz", "pop", "r&b", "soul"],
    "록": ["rock", "metal", "k-rock"],
    "랩/힙합": ["hiphop", "rap", "k-rap"],
    "팝": ["pop", "disco", "k-pop"]
}

# 모델 로드 [spkrec-ecapa-voxceleb] ECAPA 사용
model = EncoderClassifier.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    run_opts={"device":"cuda" if torch.cuda.is_available() else "cpu"}
# 저장 dir 지울 가능성 있음
)

try:
    print("모델/데이터 로딩을 시작합니다...")
    classifier = EncoderClassifier.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",
        run_opts={"device":"cuda" if torch.cuda.is_available() else "cpu"}
    )    
        
    singer_index = faiss.read_index(os.path.join(MODELS_DIR, "singers.index"))
    singer_id_map = joblib.load(os.path.join(MODELS_DIR, "singer_id_map.pkl"))
    
    with open(os.path.join(DATA_DIR, "songs_db.json"), 'r', encoding='utf-8') as f:
        songs_db = json.load(f)
        
    with open(os.path.join(DATA_DIR, "singer_info.json"), 'r', encoding='utf-8') as f:
        singer_info = json.load(f)
    
    print("모든 모델 및 데이터 로딩 완료!")
except Exception as e:
    print(f"모델/데이터 로딩 중 오류 발생: {e}")
    classifier, singer_index, singer_id_map, songs_db = None, None, None, None

# --- 2. 핵심 분석 함수들 ---
from pydub import AudioSegment

def convert_to_wav(aac_path, wav_file_path):
    audio = AudioSegment.from_file(aac_path, format="aac")
    audio = audio.set_frame_rate(16000).set_channels(1)
    audio.export(wav_file_path, format="wav")
    return wav_file_path




# 녹음 파일 안전하게 로딩되게 
def safe_load_audio(file_path, target_sr=16000, mono=True):
    try:
        # librosa가 wav 헤더 깨진 것도 자동 복원
        y, sr = librosa.load(file_path, sr=target_sr) # mono=True
        # 무음 방지용 아주 작은 노이즈 추가
        if np.max(np.abs(y)) < 1e-5:
            y = y + np.random.randn(len(y)) * 1e-5
        return y, target_sr
    except Exception as e:
        print(f"[Audio Load Error] {e}")
        data, sr = sf.read(file_path)
        return data.astype(np.float32), sr



def extract_xvector(file_path):
    signal, sr = sf.read(file_path)
    # 최소 길이 체크
    if len(signal) < sr * 0.5:  # 0.5초 미만
        raise ValueError("Audio too short for x-vector extraction")
    return classifier.encode_file(file_path)


def get_xvector(file_path, model):
    TARGET_SR = 16000
    MIN_LENGTH_SEC = 0.5
    try:
        signal, fs = torchaudio.load(file_path)
        if signal.shape[0] > 1:
            signal = torch.mean(signal, dim=0, keepdim=True)
        if fs != TARGET_SR:
            resampler = Resample(orig_freq=fs, new_freq=TARGET_SR)
            signal = resampler(signal)

        min_length_samples = int(MIN_LENGTH_SEC * TARGET_SR)
        if signal.shape[1] < min_length_samples:
            pad = min_length_samples - signal.shape[1]
            signal = torch.nn.functional.pad(signal, (0, pad))
        
        with torch.no_grad():
            embedding = model.encode_batch(signal)
        return embedding.squeeze().cpu().numpy()
    except Exception as e:
        print(f"x-vector 추출 중 오류: {e}")
        return None
    
def format_axis(x, pos):
    return librosa.midi_to_note(int(x))

def analyze_vocal_range(file_path, graph_save_path=None):
    
    # -----------------------
    # 1. 정밀 분석 파라미터 설정
    # -----------------------
    SR = 22050           
    HOP_LENGTH = 256     
    FRAME_LENGTH = 2048  
    CONF_THRESH = 0.6    
    RMS_THRESH = 0.05    
    
    try:
        # 2. 오디오 로드
        y, sr = librosa.load(file_path, sr=SR)
        
        # 3. pYIN 알고리즘 실행
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y, 
            fmin=librosa.note_to_hz('C2'), 
            fmax=librosa.note_to_hz('C7'), 
            sr=sr, 
            hop_length=HOP_LENGTH,
            frame_length=FRAME_LENGTH,
            fill_na=np.nan
        )
        
        # 4. 에너지(RMS) 기반 잡음 제거
        rms = librosa.feature.rms(y=y, frame_length=FRAME_LENGTH, hop_length=HOP_LENGTH)[0]
        
        # 마스크를 사용해 유효한 시간과 주파수 데이터만 추출 (그래프용)
        times = librosa.times_like(f0, sr=sr, hop_length=HOP_LENGTH)

        # voiced_probs 및 rms 길이 보정(안전성)
        voiced_probs = np.asarray(voiced_probs)
        if voiced_probs.shape != f0.shape:
            voiced_probs = librosa.util.fix_length(voiced_probs, size=len(f0), fill_value=0.0)

        rms = librosa.util.fix_length(rms, size=len(f0)) 

        valid_mask = (voiced_probs > CONF_THRESH) & (rms > RMS_THRESH)

        # 추가 필터: f0가 유한값인 프레임만 사용
        finite_mask = np.isfinite(f0)
        final_mask = valid_mask & finite_mask

        valid_times = times[final_mask]     # 유효한 시간축
        valid_pitches = f0[final_mask]      # 유효한 주파수(Hz)

        # 유효한 음이 없으면 종료
        if valid_pitches.size == 0 or valid_times.size == 0:
            print("❌ 유효한 피치 프레임이 없습니다.")
            return None, None

        # Hz -> MIDI 변환
        valid_midi = librosa.hz_to_midi(valid_pitches)

        # 안전성: 배열 길이 재확인 (plot 오류 방지)
        if valid_times.shape[0] != valid_midi.shape[0]:
            minlen = min(valid_times.shape[0], valid_midi.shape[0])
            valid_times = valid_times[:minlen]
            valid_midi = valid_midi[:minlen]

        # -----------------------
        # 수정: NaN/inf 제거 및 안전한 percentile 계산
        # -----------------------
        # NaN 또는 inf 값 제거
        valid_midi = valid_midi[np.isfinite(valid_midi)]
        if valid_midi.size == 0:
            print("❌ 유효한 MIDI 데이터가 없습니다 (모든 값이 NaN/inf).")
            return None, None

        try:
            # NaN 안전 계산
            min_midi = float(np.nanpercentile(valid_midi, 1))
            max_midi = float(np.nanpercentile(valid_midi, 99))
        except Exception as e:
            print(f"❌ percentile 계산 중 오류: {e}")
            return None, None

        # 계산 결과가 유한수인지 확인
        if not (np.isfinite(min_midi) and np.isfinite(max_midi)):
            print("❌ 계산된 min/max MIDI 값이 유한수가 아닙니다.")
            return None, None
        # -----------------------
        
        # 7. 결과 반환값 계산
        lowest_note = librosa.midi_to_note(int(round(min_midi)))
        highest_note = librosa.midi_to_note(int(round(max_midi)))
        
        print(f"   -> [음역대 분석 완료] {lowest_note} ~ {highest_note}")

        # --- [추가] 그래프 생성 및 저장 로직 ---
        if graph_save_path:
            plt.figure(figsize=(12, 6)) # 그래프 크기 설정
            
            # 메인 산점도 그리기 (파란색 점)
            plt.scatter(valid_times, valid_midi, s=10, c='dodgerblue', alpha=0.6, label='Detected Pitch', edgecolors='none')
            
            # 최저/최고음 가이드라인 (초록/빨강 점선)
            plt.axhline(min_midi, color='green', linestyle='--', linewidth=2, label=f"Min: {lowest_note}")
            plt.axhline(max_midi, color='red', linestyle='--', linewidth=2, label=f"Max: {highest_note}")
            
            # Y축 설정 (MIDI 숫자 -> 음계 이름으로 변환)
            y_min = int(min_midi) - 3
            y_max = int(max_midi) + 3
            plt.ylim(y_min, y_max)
            # 모든 반음 단위로 눈금 표시
            plt.yticks(range(y_min, y_max + 1)) 
            plt.gca().yaxis.set_major_formatter(FuncFormatter(format_axis))
            
            # 그래프 스타일 꾸미기
            plt.grid(True, which='both', linestyle='-', alpha=0.3)
            plt.xlabel("Time (seconds)")
            plt.ylabel("Musical Note")
            plt.title(f"Vocal Pitch Analysis: {lowest_note} ~ {highest_note}")
            plt.legend(loc='upper right')
            plt.tight_layout()
            
            # 이미지 파일로 저장
            plt.savefig(graph_save_path)
            plt.close() # 메모리 해제 (중요)
            print(f"   -> [그래프 저장 완료] {graph_save_path}")
        # -----------------------------------
        
        return lowest_note, highest_note
        
    except Exception as e:
        print(f"❌ 음역대 분석 중 오류 발생: {e}")
        return None, None

def is_in_range(song_low, song_high, user_low, user_high, tolerance=2):
    """
    음역대 비교 (tolerance: 반음 단위 허용 오차, 기본값 2)
    사용자의 음역대가 노래 음역대보다 조금 좁아도 통과시킴
    """
    try:
        if not all([song_low, song_high, user_low, user_high]):
            return False
            
        song_low_midi = librosa.note_to_midi(song_low)
        song_high_midi = librosa.note_to_midi(song_high)
        user_low_midi = librosa.note_to_midi(user_low)
        user_high_midi = librosa.note_to_midi(user_high)
        
        # [수정] 사용자의 최저음이 노래보다 2키 높아도 OK (user_low - 2 <= song_low)
        #        사용자의 최고음이 노래보다 2키 낮아도 OK (user_high + 2 >= song_high)
        return (user_low_midi - tolerance) <= song_low_midi and \
               (user_high_midi + tolerance) >= song_high_midi
               
    except Exception:
        return False

def search_faiss_with_timing(index, query, k):
    """Faiss 검색을 실행하고 내부 실행 시간을 출력하는 함수"""
    search_start_time = time.time()
    scores, ids = index.search(query, k)
    search_end_time = time.time()
    # 밀리초(ms) 단위로 실제 검색 시간 출력
    print(f"--- [내부 측정] faiss.search 실제 실행 시간: {(search_end_time - search_start_time) * 1000:.4f} ms ---")
    return scores, ids


# --- Spotify API 설정 (환경 변수 또는 직접 설정) ---
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "a2c4860d3fd5488588e05b1e90f76b78")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "1d8ac11f5f594384a31779cfe17a2941")

# Spotify 토큰 캐싱
_spotify_token_cache = {"token": None, "expires_at": None}

async def _get_spotify_token():
    """Spotify Access Token 발급 (캐싱 포함)"""
    import time
    current_time = time.time()
    
    # 캐시된 토큰이 아직 유효하면 반환
    if _spotify_token_cache["token"] and _spotify_token_cache["expires_at"]:
        if current_time < _spotify_token_cache["expires_at"]:
            return _spotify_token_cache["token"]
    
    try:
        # Basic Auth 생성
        credentials = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://accounts.spotify.com/api/token",
                headers={
                    "Authorization": f"Basic {encoded_credentials}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data="grant_type=client_credentials",
                timeout=10.0,
            )
            
            if response.status_code != 200:
                print(f"❌ [Spotify] 토큰 발급 실패: {response.status_code}")
                raise HTTPException(status_code=500, detail="Spotify 토큰 발급 실패")
            
            data = response.json()
            token = data["access_token"]
            expires_in = data.get("expires_in", 3600)
            
            # 토큰 캐싱 (만료 5분 전에 갱신)
            _spotify_token_cache["token"] = token
            _spotify_token_cache["expires_at"] = current_time + expires_in - 300
            
            return token
    except Exception as e:
        print(f"❌ [Spotify] 토큰 발급 오류: {e}")
        raise HTTPException(status_code=500, detail=f"Spotify 토큰 발급 오류: {str(e)}")

def search_youtube_video(singer, song_title):
    """YouTube에서 노래를 검색하여 비디오 ID를 반환하는 함수"""
    try:
        search_query = f"{singer} {song_title} audio"
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',  # 플레이리스트 내에서만 flat 모드
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # ytsearch1: 검색 결과 중 첫 번째 항목만 가져옴
            search_url = f"ytsearch1:{search_query}"
            info = ydl.extract_info(search_url, download=False)
            
            if info and 'entries' in info and len(info['entries']) > 0:
                video = info['entries'][0]
                video_id = video.get('id')
                video_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else None
                video_title = video.get('title', '')
                return {
                    'video_id': video_id,
                    'video_url': video_url,
                    'title': video_title
                }
        
        return None
    except Exception as e:
        print(f"YouTube 검색 오류 ({singer} - {song_title}): {e}")
        return None
    
# --- 3. API 엔드포인트 ---
@app.get("/")
def read_root():
    return {"message": "AI 음성 분석 및 노래 추천 API"}

@app.get("/artist-image/{artist_name}")
async def get_artist_image(artist_name: str):
    """가수 이름으로 Spotify에서 이미지 URL 가져오기"""
    if not artist_name or artist_name == "N/A":
        raise HTTPException(status_code=400, detail="유효하지 않은 가수 이름")
    
    try:
        access_token = await _get_spotify_token()
        
        # URL 인코딩
        import urllib.parse
        encoded_name = urllib.parse.quote(artist_name)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.spotify.com/v1/search?q={encoded_name}&type=artist&limit=1",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10.0,
            )
            
            if response.status_code != 200:
                print(f"❌ [Spotify] 검색 실패: {response.status_code}")
                return {"image_url": None}
            
            data = response.json()
            items = data.get("artists", {}).get("items", [])
            
            if not items:
                print(f"⚠️ [Spotify] 가수를 찾을 수 없음: {artist_name}")
                return {"image_url": None}
            
            images = items[0].get("images", [])
            if not images:
                print(f"⚠️ [Spotify] 이미지가 없음: {artist_name}")
                return {"image_url": None}
            
            # 가장 큰 이미지 반환
            image_url = images[0].get("url")
            return {"image_url": image_url}
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [Spotify] 이미지 가져오기 오류: {e}")
        return {"image_url": None}

@app.post("/analyze")
async def analyze(
    request: Request,
    voice_file: UploadFile = File(...),
    gender: str = Form("none"),
    genre: str = Form("none"),
    start_year: int = Form(1980),
    end_year: int = Form(2025)
):
    print(f"\n========== [분석 시작] ==========")
    print(f"📥 사용자 입력 정보: 성별={gender}, 장르={genre}, 년도={start_year}~{end_year}")
    
    start_time = time.time()
    # [수정 1] singer_info도 확인 목록에 추가
    if not all([classifier, singer_index, singer_id_map, songs_db, singer_info]):
        raise HTTPException(status_code=500, detail="서버 모델/데이터가 준비되지 않았습니다.")

    temp_file_path = f"temp_{voice_file.filename}"
    wav_file_path = temp_file_path.rsplit('.',1)[0] + ".wav"
    analysis_path = temp_file_path

    try:
        # --- 파일 저장 및 변환 (기존과 동일) ---
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(voice_file.file, buffer)

        ext = temp_file_path.rsplit('.', 1)[-1].lower()
        if ext in ["m4a", "aac", "mp4"]:
            try:
                audio = AudioSegment.from_file(temp_file_path, format=ext)
                audio = audio.set_frame_rate(16000).set_channels(1)
                audio.export(wav_file_path, format="wav")
                analysis_path = wav_file_path
            except Exception as e:
                 print(f"오디오 변환 실패: {e}")
                 # 변환 실패 시 원본 사용 시도 (선택 사항)
        else:
            analysis_path = temp_file_path

        # [추가] 그래프 이미지 저장 경로 생성 (유니크한 파일명 사용)
        timestamp = int(time.time())
        graph_filename = f"graph_{timestamp}.png"
        # 실제 저장될 물리적 경로 (backend/static/graphs/...)
        graph_save_path = os.path.join("static", "graphs", graph_filename)
    
        # --- 비동기 분석 실행 (기존과 동일) ---
        loop = asyncio.get_running_loop()
        xvector_task = loop.run_in_executor(None, get_xvector, analysis_path, classifier)
        vocal_range_task = loop.run_in_executor(
            None, 
            analyze_vocal_range, 
            analysis_path, 
            graph_save_path # <-- 여기에 추가! (함수가 이 인자를 받도록 수정되어 있어야 함)
        )
        
        user_xvector, (user_lowest_note, user_highest_note) = await asyncio.gather(
            xvector_task,
            vocal_range_task
        )
        
        t_after_analysis = time.time()
        print(f"[Time Check] x-vector 및 음역대 동시 분석 시간: {t_after_analysis - start_time:.4f} 초")

        if user_xvector is None:
            raise HTTPException(status_code=400, detail="음성 파일을 분석할 수 없습니다.")

        # --- Faiss 검색 ---
        user_xvector_normalized = user_xvector.astype('float32').reshape(1, -1)
        faiss.normalize_L2(user_xvector_normalized)

        # [수정] 검색 후보군(k)을 늘려 필터링의 정확도를 높입니다.
        TOP_K_FOR_DISPLAY = 5
        SEARCH_POOL_K = 50 # 5명에서 50명으로 늘려 필터링할 데이터 확보

        scores, ids = singer_index.search(user_xvector_normalized, SEARCH_POOL_K)
        
        # 전체 검색 결과 풀 생성
        all_search_results = []
        for i in range(SEARCH_POOL_K):
            singer_id = ids[0][i]
            if singer_id != -1:
                all_search_results.append({
                    "singer": singer_id_map[singer_id],
                    "similarity": float(scores[0][i]) * 100
                })

        # 프론트엔드에 표시할 Top-K 결과 (필터링과 무관하게 상위 5개)
        raw_top_k = all_search_results[:TOP_K_FOR_DISPLAY]

        # --- 필터링 로직 ---
        
        # 1. 성별 필터링
        if gender == 'none':
            # 성별 필터가 없으면 전체 검색 풀을 후보로 사용
            artists_to_check = all_search_results
        else:
            # 성별 필터가 있으면, 전체 검색 풀 내에서 해당 성별의 가수만 필터링
            artists_to_check = [
                res for res in all_search_results
                if singer_info.get(res['singer']) == gender
            ]
        
        # 최종 추천 대상 가수 목록 (이름만 추출)
        # artists_to_check가 비어있으면 filtered_artists도 비어있게 됨
        filtered_artists = [res['singer'] for res in artists_to_check]

        # [수정] best_match_singer를 먼저 정의
        best_match_singer = filtered_artists[0] if filtered_artists else "N/A"

        # 2. 최종 노래 추천 (장르, 년도, 음역대 필터링)
        recommended_songs = []
        matched_singer_full_songs = []
        top_singers_full_songs = []
        
        target_gtzan_genres = USER_TO_GTZAN_MAP.get(genre, []) # 상단에 정의된 MAP 사용

        # 필터링된 가수 목록을 순회하며 조건에 맞는 노래 찾기
        if best_match_singer != "N/A":
            for artist_name in filtered_artists:
                singer_song_list = songs_db.get(artist_name, [])
                
                current_singer_recs = []
                for song in singer_song_list:
                    song_year = song.get('year')
                    # API 장르와 모델 예측 장르 모두 확인
                    song_genres = song.get('genres_api', []) + song.get('genres_model', [])

                    # A. 년도 필터
                    if song_year and not (start_year <= song_year <= end_year):
                        continue
                    # B. 장르 필터 (교집합 확인)
                    if genre != 'none' and not any(g in target_gtzan_genres for g in song_genres):
                        continue
                    # C. 음역대 필터
                    if is_in_range(song['lowest_note'], song['highest_note'], user_lowest_note, user_highest_note):
                        current_singer_recs.append(song)
                
                if current_singer_recs:
                    top_singers_full_songs.append({
                        "singer": artist_name,
                        "songs": current_singer_recs
                    })
                    if artist_name == best_match_singer:
                        matched_singer_full_songs = current_singer_recs
        
        recommended_songs = [song['title'] for song in matched_singer_full_songs]

        # --- Top3 노래 및 유튜브 검색 ---
        top3_songs_with_youtube = []
        songs_to_search = []
        
        # Case A: 음역대 기반 추천곡이 있는 경우 (최대 3개)
        if recommended_songs:
            songs_to_search = [(best_match_singer, song_title) for song_title in recommended_songs[:3]]
        # Case B: 음역대 추천곡이 없으면, 매칭된 가수의 DB 상위 3곡
        elif best_match_singer != "N/A" and best_match_singer in songs_db:
            songs_to_search = [(best_match_singer, song['title']) for song in songs_db[best_match_singer][:3]]

        # Case C: 위에서도 부족하면, 유사도 Top K 가수들의 대표곡으로 채움
        if not songs_to_search and best_match_singer != "N/A":
            seen_singers = {best_match_singer}
            for result in raw_top_k:
                singer_name = result['singer']
                if singer_name in seen_singers:
                    continue
                seen_singers.add(singer_name)
                if singer_name in songs_db and songs_db[singer_name]:
                    songs_to_search.append((singer_name, songs_db[singer_name][0]['title']))
                if len(songs_to_search) >= 3:
                    break

        # Case D: DB에 노래 정보가 아예 없으면 가수 이름으로 검색어 생성
        if not songs_to_search and best_match_singer != "N/A":
            for result in raw_top_k[:3]:
                singer_name = result['singer']
                songs_to_search.append((singer_name, f"{singer_name} 노래"))
        
        # 2. 비동기로 유튜브 검색 실행 (병렬 처리로 속도 최적화)
        if songs_to_search:
            loop = asyncio.get_running_loop()
            youtube_search_tasks = []
            
            for singer, song_title in songs_to_search:
                task = loop.run_in_executor(None, search_youtube_video, singer, song_title)
                youtube_search_tasks.append((singer, song_title, task))
            
            for singer, song_title, task in youtube_search_tasks:
                youtube_info = await task
                if youtube_info:
                    top3_songs_with_youtube.append({
                        'title': song_title,
                        'singer': singer,
                        'youtube_video_id': youtube_info.get('video_id'),
                        'youtube_url': youtube_info.get('video_url'),
                        'youtube_title': youtube_info.get('title', '')
                    })
                else:
                    top3_songs_with_youtube.append({
                        'title': song_title,
                        'singer': singer,
                        'youtube_video_id': None,
                        'youtube_url': None,
                        'youtube_title': None
                    })
        
        # [중요] 위에서 구한 결과를 그대로 반환해야 함 (덮어쓰기 코드 삭제됨)
        graph_url = f"{str(request.base_url).rstrip('/')}/static/graphs/{graph_filename}"
        print(f"DEBUG: pitch_graph_url -> {graph_url}")

        user_range_str = f"{user_lowest_note} ~ {user_highest_note}" if user_lowest_note else "분석 불가"
        
        end_time = time.time()
        print(f"[Time Check] 총 API 처리 시간: {end_time - start_time:.4f} 초")

        # 반환값 생성
        return {
            "fileName" : voice_file.filename,
            "best_match": best_match_singer,
            "user_vocal_range": user_range_str,
            "recommended_songs": recommended_songs,
            "pitch_graph_url": graph_url, # <-- [핵심] 그래프 URL 추가
            # 프론트엔드 표시용 포맷으로 변환
            "top_k_results": [
                {"singer": res['singer'], "similarity": f"{res['similarity']:.2f}%"} 
                for res in raw_top_k
            ],
            "top3_songs_with_youtube": top3_songs_with_youtube, 
            "matched_singer_full_songs": matched_singer_full_songs,
            "top_singers_full_songs": top_singers_full_songs,
        }
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        # 변환된 파일도 삭제하는 것이 좋음
        if os.path.exists(wav_file_path) and analysis_path != temp_file_path:
            os.remove(wav_file_path)