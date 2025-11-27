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
from speechbrain.inference import EncoderClassifier
from torchaudio.transforms import Resample
import matplotlib
# macOS에서 GUI 백엔드가 쓰여서 발생하는 에러 방지: 반드시 pyplot 이전에 backend 설정
matplotlib.use("Agg")   # non-GUI backend (파일로 저장 전용)
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from fastapi.staticfiles import StaticFiles # <-- 추가

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


# --- 3. API 엔드포인트 ---
@app.get("/")
def read_root():
    return {"message": "AI 음성 분석 및 노래 추천 API"}

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
        k = 5 # 후보를 넉넉하게 5명 정도 뽑습니다
        scores, ids = singer_index.search(user_xvector_normalized, k)
        
        # [수정 2] raw_top_k 정의 (필터링을 위한 원본 데이터)
        raw_top_k = []
        for i in range(k):
            singer_id = ids[0][i]
            if singer_id != -1:
                raw_top_k.append({
                    "singer": singer_id_map[singer_id],
                    "similarity": float(scores[0][i]) * 100 # 숫자형으로 저장
                })

        # --- 필터링 로직 ---
        
        # 1. 성별 필터링
        filtered_artists = []
        if gender == 'none':
            filtered_artists = [res['singer'] for res in raw_top_k]
        else:
            for res in raw_top_k:
                artist_name = res['singer']
                # singer_info에 정보가 없으면 일단 포함하거나 제외 (여기선 포함으로 가정)
                if singer_info.get(artist_name) == gender:
                    filtered_artists.append(artist_name)
        
        # 만약 성별 필터링 후 남은 가수가 없으면, 원래 Top K 그대로 사용 (Fallback)
        if not filtered_artists:
             filtered_artists = [res['singer'] for res in raw_top_k]

        # 2. 최종 노래 추천 (장르, 년도, 음역대)
        recommended_songs = []
        best_match_singer = filtered_artists[0] if filtered_artists else "N/A"
        target_gtzan_genres = USER_TO_GTZAN_MAP.get(genre, []) # 상단에 정의된 MAP 사용

        # 필터링된 가수 목록을 순회하며 조건에 맞는 노래 찾기
        for artist_name in filtered_artists:
            if recommended_songs: # 이미 추천곡을 찾았다면 루프 중단
                break
                
            singer_song_list = songs_db.get(artist_name, [])
            
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
                    recommended_songs.append(song['title'])
        
        # [중요] 위에서 구한 결과를 그대로 반환해야 함 (덮어쓰기 코드 삭제됨)
        graph_url = f"{str(request.base_url).rstrip('/')}/static/graphs/{graph_filename}"
        print(f"DEBUG: pitch_graph_url -> {graph_url}")

        user_range_str = f"{user_lowest_note} ~ {user_highest_note}" if user_lowest_note else "분석 불가"
        
        end_time = time.time()
        print(f"[Time Check] 총 API 처리 시간: {end_time - start_time:.4f} 초")

        # 반환값 생성
        return {
            "best_match": best_match_singer,
            "user_vocal_range": user_range_str,
            "recommended_songs": recommended_songs,
            "pitch_graph_url": graph_url, # <-- [핵심] 그래프 URL 추가
            # 프론트엔드 표시용 포맷으로 변환
            "top_k_results": [
                {"singer": res['singer'], "similarity": f"{res['similarity']:.2f}%"} 
                for res in raw_top_k
            ],
        }
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        # 변환된 파일도 삭제하는 것이 좋음
        # if os.path.exists(wav_file_path) and analysis_path != temp_file_path:
        #     os.remove(wav_file_path)