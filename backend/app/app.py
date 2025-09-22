import os
import shutil
import glob
import numpy as np
import joblib
import torch
import torchaudio
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from speechbrain.pretrained import EncoderClassifier
from sklearn.metrics.pairwise import cosine_similarity

# --- 1. FastAPI 앱 인스턴스 생성 및 CORS 설정 ---
app = FastAPI()

origins = ["*"] # 개발 중에는 모든 출처 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. 경로 설정 및 모델 로딩 ---
# 이 파일(app.py)의 위치를 기준으로 경로를 설정합니다.
APP_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(APP_DIR)
MODELS_DIR = os.path.join(BACKEND_DIR, 'models')

print("필요한 모델들을 불러옵니다...")
try:
    classifier = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb")
    singer_models = {}
    for model_file in glob.glob(os.path.join(MODELS_DIR, '*.xvector')):
        singer_name = os.path.splitext(os.path.basename(model_file))[0]
        singer_models[singer_name] = joblib.load(model_file)
    print(f"--> {list(singer_models.keys())} 가수 모델 로딩 완료!")
except Exception as e:
    print(f"모델 로딩 중 오류 발생: {e}")
    classifier = None
    singer_models = {}

# --- 3. 핵심 함수 정의 ---
def get_xvector(file_path, model):
    try:
        signal, fs = torchaudio.load(file_path)
        with torch.no_grad():
            embedding = model.encode_batch(signal)
        return embedding.squeeze().cpu().numpy()
    except Exception as e:
        print(f"x-vector 추출 중 오류: {e}")
        return None

# --- 4. API 엔드포인트(경로) 정의 ---
@app.get("/")
def read_root():
    return {"message": "음성 분석 API 서버"}

@app.post("/analyze-voice")
async def analyze_voice(voice_file: UploadFile = File(...)):
    if not classifier or not singer_models:
        raise HTTPException(status_code=500, detail="서버 모델이 준비되지 않았습니다.")

    temp_file_path = f"temp_{voice_file.filename}"
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(voice_file.file, buffer)

        user_xvector = get_xvector(temp_file_path, classifier)
        if user_xvector is None:
            raise HTTPException(status_code=400, detail="음성 파일을 분석할 수 없습니다.")

        results = {}
        for singer_name, singer_avg_xvector in singer_models.items():
            similarity = cosine_similarity(singer_avg_xvector.reshape(1, -1), user_xvector.reshape(1, -1))
            results[singer_name] = similarity[0][0] * 100
            
        if not results:
            raise HTTPException(status_code=500, detail="유사도 계산 실패.")
        
        best_match_singer = max(results, key=results.get)
        
        return {
            "best_match": best_match_singer,
            "similarity_scores": {singer: f"{score:.2f}%" for singer, score in results.items()}
        }
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)