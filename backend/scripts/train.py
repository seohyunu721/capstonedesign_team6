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
        if signal.shape[0] > 1:
            signal = torch.mean(signal, dim=0, keepdim=True)
        if fs != TARGET_SR:
            resampler = Resample(orig_freq=fs, new_freq=TARGET_SR)
            signal = resampler(signal)
        with torch.no_grad():
            embedding = model.encode_batch(signal)
        return embedding.squeeze().cpu().numpy()
    except Exception as e:
        print(f"    - 오류 발생: '{os.path.basename(file_path)}' 처리 중 문제 발생 ({e})")
        return None

# --- 경로 설정 ---
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPTS_DIR)
DATA_DIR = os.path.join(BACKEND_DIR, 'data')
MODELS_DIR = os.path.join(BACKEND_DIR, 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

SINGER_DIRS = glob.glob(os.path.join(DATA_DIR, '*_songs'))
print("\n각 가수별 통합 모델(.xvector) 생성을 시작합니다...")
print("-" * 40)

for singer_dir in SINGER_DIRS:
    singer_name = os.path.basename(singer_dir).replace("_songs", "")
    print(f"🎤 가수 '{singer_name}'의 학습을 시작합니다...")
    
    singer_files = glob.glob(os.path.join(singer_dir, '**', '*.wav'), recursive=True)
    all_xvectors = []

    if not singer_files:
        print(f"-> '{singer_dir}' 폴더에 파일이 없습니다. 건너뜁니다.\n")
        continue
    
    print(f"-> 총 {len(singer_files)}개의 음원 파일을 발견했습니다.")
    
    # 각 파일 처리 진행 상황을 보여줌
    for i, file_path in enumerate(singer_files):
        print(f"  ({i+1}/{len(singer_files)}) '{os.path.basename(file_path)}' 파일 분석 중...")
        xvector = get_xvector(file_path, classifier)
        if xvector is not None:
            all_xvectors.append(xvector)
    
    if all_xvectors:
        # X-vector 저장
        singer_avg_xvector = np.mean(all_xvectors, axis=0)
        save_path = os.path.join(MODELS_DIR, f'{singer_name}.xvector')
        joblib.dump(singer_avg_xvector, save_path)
        print(f"✅ '{singer_name}.xvector' 모델 저장 완료! (총 {len(all_xvectors)}개 파일 사용)\n")
        
        # 폴더 이름 변경
        new_singer_dir = singer_dir.replace("_songs", "_song")
        os.rename(singer_dir, new_singer_dir)
        print(f"📂 폴더 이름 변경: '{singer_dir}' → '{new_singer_dir}'\n")
    else:
        print(f"-> '{singer_name}'의 파일을 처리하지 못했습니다.\n")

print("-" * 40)
print("모든 개별 가수 모델 생성이 완료되었습니다.")