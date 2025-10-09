# create_xvectors.py 최종 수정본
import os
import glob
import numpy as np
import torch
import torchaudio
from torchaudio.transforms import Resample
import joblib
from speechbrain.pretrained import EncoderClassifier

print("미리 학습된 x-vector 모델을 불러옵니다...")
try:
    classifier = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb")
    print("모델 로딩 완료!")
except Exception as e:
    print(f"모델 로딩 실패: {e}")
    exit()

def get_xvector(file_path, model):
    TARGET_SR = 16000
    try:
        signal, fs = torchaudio.load(file_path)

        # --- 아래 두 줄 추가: 스테레오를 모노로 변환 ---
        if signal.shape[0] > 1: # 채널 수가 1개보다 많으면 (스테레오이면)
            signal = torch.mean(signal, dim=0, keepdim=True)
        # ----------------------------------------------

        if fs != TARGET_SR:
            resampler = Resample(orig_freq=fs, new_freq=TARGET_SR)
            signal = resampler(signal)
        
        with torch.no_grad():
            embedding = model.encode_batch(signal)
        
        return embedding.squeeze().cpu().numpy()
    except Exception as e:
        print(f"'{os.path.basename(file_path)}' 처리 중 오류: {e}")
        return None

# --- 경로 설정 및 메인 로직 (이하 동일) ---
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPTS_DIR)
DATA_DIR = os.path.join(BACKEND_DIR, 'data')
MODELS_DIR = os.path.join(BACKEND_DIR, 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

SINGER_DIRS = glob.glob(os.path.join(DATA_DIR, '*_songs'))
print("\n각 가수별 통합 모델(.xvector) 생성을 시작합니다...")

for singer_dir in SINGER_DIRS:
    # ... (이하 로직은 이전과 동일하게 유지)
    singer_name = os.path.basename(singer_dir).replace("_songs", "")
    print(f"--> '{singer_name}' 학습 중...")
    
    singer_files = glob.glob(os.path.join(singer_dir, '*.wav'))
    all_xvectors = []

    if not singer_files:
        print(f"'{singer_dir}' 폴더에 파일이 없습니다. 건너뜁니다.")
        continue

    for file_path in singer_files:
        xvector = get_xvector(file_path, classifier)
        if xvector is not None:
            all_xvectors.append(xvector)
    
    if all_xvectors:
        singer_avg_xvector = np.mean(all_xvectors, axis=0)
        save_path = os.path.join(MODELS_DIR, f'{singer_name}.xvector')
        joblib.dump(singer_avg_xvector, save_path)
        print(f"'{singer_name}.xvector' 모델 저장 완료! 형태(shape): {singer_avg_xvector.shape}")

print("\n모든 개별 가수 모델 생성이 완료되었습니다.")