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
import time  # <-- 시간 측정을 위한 라이브러리
import asyncio
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from speechbrain.pretrained import EncoderClassifier
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
def get_xvector(file_path, model):
    TARGET_SR = 16000
    try:
        signal, fs = torchaudio.load(file_path)
        if signal.shape[0] > 1:
            signal = torch.mean(signal, dim=0, keepdim=True)
        if fs != TARGET_SR:
            resampler = Resample(orig_freq=fs, new_freq=TARGET_SR)
            signal = resampler(signal)
        with torch.no_grad():
            embedding = model.encode_batch(signal)
        return embedding.squeeze().cpu().numpy()
    except Exception as e:
        print(f"x-vector 추출 중 오류: {e}")
        return None

def analyze_vocal_range(file_path):
    try:
        y, sr = librosa.load(file_path, sr=16000)
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        valid_pitches = [pitches[magnitudes[:, t].argmax(), t] for t in range(pitches.shape[1]) if pitches[magnitudes[:, t].argmax(), t] > 0]
        if not valid_pitches: return None, None
        min_freq, max_freq = np.percentile(valid_pitches, 5), np.percentile(valid_pitches, 95)
        return librosa.hz_to_note(min_freq), librosa.hz_to_note(max_freq)
    except Exception as e:
        print(f"음역대 분석 중 오류: {e}")
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
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(voice_file.file, buffer)

        # --- 비동기 작업 실행 ---
        loop = asyncio.get_running_loop()
        
        # 1. x-vector 추출 (별도 스레드에서)
        xvector_task = loop.run_in_executor(None, get_xvector, temp_file_path, classifier)
        
        # 2. 음역대 분석 (별도 스레드에서)
        vocal_range_task = loop.run_in_executor(None, analyze_vocal_range, temp_file_path)

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
        
        end_time = time.time()
        print(f"[Time Check] 총 API 처리 시간: {end_time - start_time:.4f} 초")

        return {
            "best_match": best_match_singer,
            "user_vocal_range": user_range_str,
            "recommended_songs": recommended_songs,
            "top_k_results": similarity_results,
        }
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)