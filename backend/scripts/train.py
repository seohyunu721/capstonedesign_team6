import librosa
import numpy as np
from speechbrain.pretrained import EncoderClassifier
import os
import glob
import torch
import torchaudio
import joblib

# --- 현재 파일 위치 기준으로 backend 폴더 경로 설정 ---
# 이 스크립트 파일(train_models.py)이 있는 위치를 기준으로 경로를 잡습니다.
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPTS_DIR)
# ---------------------------------------------------

# --- 특징 추출 함수 (수정 없음) ---
def get_xvector(file_path, model):
    # ... (이전과 동일)
    try:
        signal, fs = torchaudio.load(file_path)
        with torch.no_grad():
            embedding = model.encode_batch(signal)
        return embedding.squeeze().cpu().numpy()
    except Exception as e:
        print(f"'{os.path.basename(file_path)}' 처리 중 오류: {e}")
        return None

# --- 모델 불러오기 (수정 없음) ---
print("미리 학습된 x-vector 모델을 불러옵니다...")
classifier = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb")
print("모델 로딩 완료!")

# --- 각 가수별 평균 x-vector 생성 및 저장 ---
DATA_DIR = os.path.join(BACKEND_DIR, 'data') # data 폴더 경로
MODELS_DIR = os.path.join(BACKEND_DIR, 'models') # models 폴더 경로
os.makedirs(MODELS_DIR, exist_ok=True) # models 폴더가 없으면 생성

SINGER_DIRS = ["iu_songs"]
print("\n각 가수별 통합 모델 학습 및 저장을 시작합니다...")

for singer_dir_name in SINGER_DIRS:
    singer_name = singer_dir_name.replace("_songs", "")
    print(f"--> '{singer_name}' 학습 중...")
    
    singer_dir_path = os.path.join(DATA_DIR, singer_dir_name) # 정확한 폴더 경로
    singer_files = glob.glob(os.path.join(singer_dir_path, '*.wav'))
    all_xvectors = []

    if not singer_files:
        print(f"'{singer_dir_path}' 폴더에 파일이 없습니다. 건너뜁니다.")
        continue

    for file_path in singer_files:
        xvector = get_xvector(file_path, classifier)
        if xvector is not None:
            all_xvectors.append(xvector)
    
    if all_xvectors:
        singer_avg_xvector = np.mean(all_xvectors, axis=0)
        
        # 모델을 models 폴더에 저장
        save_path = os.path.join(MODELS_DIR, f'{singer_name}.xvector')
        joblib.dump(singer_avg_xvector, save_path)
        print(f"'{singer_name}.xvector' 모델을 {MODELS_DIR} 폴더에 저장 완료!")

print("\n모든 가수 모델의 학습 및 저장이 완료되었습니다.")