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
import yt_dlp
#########################
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from speechbrain.inference import EncoderClassifier
from torchaudio.transforms import Resample

# --- 1. FastAPI 앱 및 모델 로딩 ---
app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 모델 로드 [spkrec-ecapa-voxceleb] ECAPA 사용
model = EncoderClassifier.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    run_opts={"device":"cuda" if torch.cuda.is_available() else "cpu"}
# 저장 dir 지울 가능성 있음
)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(APP_DIR)
MODELS_DIR = os.path.join(BACKEND_DIR, 'models')
DATA_DIR = os.path.join(BACKEND_DIR, 'data')

try:
    classifier = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb")
    singer_index = faiss.read_index(os.path.join(MODELS_DIR, "singers.index"))
    singer_id_map = joblib.load(os.path.join(MODELS_DIR, "singer_id_map.pkl"))
    with open(os.path.join(DATA_DIR, "songs_db.json"), 'r', encoding='utf-8') as f:
        songs_db = json.load(f)
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
            hop_length=256  # 최고음 (약 2093Hz)
        )
        
        # 2. '노래가 불린 구간(voiced)'의 유효한 음높이 값만 추출
        valid_pitches = f0[voiced_flag]

        if valid_pitches is None or valid_pitches.size == 0:
            return None, None
            
        # 3. NaN 값 제거 (pYIN 결과에 포함될 수 있음)
        valid_pitches = valid_pitches[~np.isnan(valid_pitches)]
        
        if valid_pitches.size == 0:
            return None, None

        # 4. 백분위수를 사용해 극단적인 아웃라이어 값 제거
        min_freq = np.percentile(valid_pitches, 5)  # 하위 5%
        max_freq = np.percentile(valid_pitches, 95) # 상위 95%
        
        lowest_note = librosa.hz_to_note(min_freq)
        highest_note = librosa.hz_to_note(max_freq)
        
        return lowest_note, highest_note
        
    except Exception as e:
        print(f"'{os.path.basename(file_path)}' 음역대 분석 중 오류: {e}")
        return None, None
    



def is_in_range(song_low, song_high, user_low, user_high):
    try:
        return librosa.note_to_midi(user_low) <= librosa.note_to_midi(song_low) and librosa.note_to_midi(user_high) >= librosa.note_to_midi(song_high)
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
            # ytsearch: 접두사를 사용한 검색
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

@app.post("/analyze")
async def analyze(voice_file: UploadFile = File(...)):
    start_time = time.time()
    if not all([classifier, singer_index, singer_id_map, songs_db]):
        raise HTTPException(status_code=500, detail="서버 모델/데이터가 준비되지 않았습니다.")

    temp_file_path = f"temp_{voice_file.filename}"
    # 추가
    wav_file_path = temp_file_path.rsplit('.',1)[0] + ".wav"
    analysis_path = temp_file_path

    try:
        # --- 업로드된 파일 임시 저장 ---
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(voice_file.file, buffer)
        # 추가ㅏㅏㅏㅏㅏㅏㅏㅏㅏㅏㅏㅏㅏㅏㅏㅏㅏㅏㅏㅏㅏ
        # AAC / 다른 포맷이면 WAV로 변환
        ext = temp_file_path.rsplit('.', 1)[-1].lower()
        if ext in ["m4a", "aac", "mp4"]:
            audio = AudioSegment.from_file(temp_file_path, format=ext)
            audio = audio.set_frame_rate(16000).set_channels(1)  # librosa 용으로 16kHz mono
            audio.export(wav_file_path, format="wav")
            analysis_path = wav_file_path
        else:
            analysis_path = temp_file_path


        # --- 비동기 작업 실행 ---
        loop = asyncio.get_running_loop()
        
        # 1. x-vector 추출 (별도 스레드에서)
        xvector_task = loop.run_in_executor(None, get_xvector, analysis_path, classifier)
        
        # 2. 음역대 분석 (별도 스레드에서)
        vocal_range_task = loop.run_in_executor(None, analyze_vocal_range, analysis_path)

        # 두 개의 무거운 작업을 동시에 실행하고 결과를 기다림
        user_xvector, (user_lowest_note, user_highest_note) = await asyncio.gather(
            xvector_task,
            vocal_range_task
        )
        
        t_after_analysis = time.time()
        print(f"[Time Check] x-vector 및 음역대 동시 분석 시간: {t_after_analysis - start_time:.4f} 초")

        if user_xvector is None:
            raise HTTPException(status_code=400, detail="음성 파일을 분석할 수 없습니다.")

        # --- Faiss 검색 (매우 빠르므로 직접 실행) ---
        user_xvector_normalized = user_xvector.astype('float32').reshape(1, -1)
        faiss.normalize_L2(user_xvector_normalized)
        k = 3
        scores, ids = singer_index.search(user_xvector_normalized, k)
        
        # --- 결과 처리 ---
        similarity_results = []
        for i in range(k):
            singer_id = ids[0][i]
            if singer_id != -1:
                similarity_results.append({
                    "singer": singer_id_map[singer_id],
                    "similarity": f"{scores[0][i] * 100:.2f}%"
                })

        best_match_singer = similarity_results[0]['singer'] if similarity_results else "N/A"
        user_range_str = f"{user_lowest_note} ~ {user_highest_note}" if user_lowest_note else "분석 불가"
        
        recommended_songs = []
        if user_lowest_note and best_match_singer in songs_db:
            for song in songs_db[best_match_singer]:
                if is_in_range(song['lowest_note'], song['highest_note'], user_lowest_note, user_highest_note):
                    recommended_songs.append(song['title'])
        
        # Top3 노래에 대해 YouTube 비디오 ID 검색
        top3_songs_with_youtube = []
        
        # 음역대 기반 추천곡이 있으면 그것을 사용, 없으면 best_match 가수의 대표곡 사용
        songs_to_search = []
        if recommended_songs:
            songs_to_search = [(best_match_singer, song_title) for song_title in recommended_songs[:3]]
        else:
            # 음역대 데이터가 없을 때: best_match 가수의 노래 중 처음 3개 사용
            if best_match_singer in songs_db:
                songs_to_search = [(best_match_singer, song['title']) for song in songs_db[best_match_singer][:3]]

        # 그래도 비어있다면 top-k 가수들의 대표곡을 찾아봄
        if not songs_to_search:
            seen_singers = set()
            for result in similarity_results:
                singer_name = result['singer']
                if singer_name in seen_singers:
                    continue
                seen_singers.add(singer_name)
                if singer_name in songs_db and songs_db[singer_name]:
                    songs_to_search.append((singer_name, songs_db[singer_name][0]['title']))
                if len(songs_to_search) >= 3:
                    break

        # 그래도 없으면 가수 이름만으로 검색 (임의 타이틀)
        if not songs_to_search:
            for result in similarity_results[:3]:
                singer_name = result['singer']
                songs_to_search.append((singer_name, f"{singer_name} 노래"))
        
        if songs_to_search:
            # 비동기로 YouTube 검색 실행
            loop = asyncio.get_running_loop()
            youtube_search_tasks = []
            
            for singer, song_title in songs_to_search:
                task = loop.run_in_executor(None, search_youtube_video, singer, song_title)
                youtube_search_tasks.append((singer, song_title, task))
            
            # 모든 YouTube 검색 완료 대기
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
                    # YouTube 검색 실패 시에도 노래 정보는 포함
                    top3_songs_with_youtube.append({
                        'title': song_title,
                        'singer': singer,
                        'youtube_video_id': None,
                        'youtube_url': None,
                        'youtube_title': None
                    })
        
        end_time = time.time()
        print(f"[Time Check] 총 API 처리 시간: {end_time - start_time:.4f} 초")

        # best_match 가수의 전체 곡 목록 (프론트에서 전체 플레이리스트 UI용)
        matched_singer_full_songs = []
        if best_match_singer in songs_db:
            matched_singer_full_songs = songs_db[best_match_singer]

        # Top3 가수의 전곡 리스트 데이터
        top_singers_full_songs = []
        seen_top_singers = set()
        for result in similarity_results:
            singer_name = result['singer']
            if singer_name in seen_top_singers:
                continue
            seen_top_singers.add(singer_name)
            if singer_name in songs_db:
                top_singers_full_songs.append({
                    'singer': singer_name,
                    'songs': songs_db[singer_name]
                })
            if len(top_singers_full_songs) >= 3:
                break

        return {
            "best_match": best_match_singer,
            "user_vocal_range": user_range_str,
            "recommended_songs": recommended_songs,
            "top_k_results": similarity_results,
            "top3_songs_with_youtube": top3_songs_with_youtube,  # YouTube 정보 포함
            "matched_singer_full_songs": matched_singer_full_songs,
            "top_singers_full_songs": top_singers_full_songs,
        }
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        # if os.path.exists(wav_file_path):
        #     os.remove(wav_file_path)