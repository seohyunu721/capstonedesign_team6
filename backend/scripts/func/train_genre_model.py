import os
import glob
import librosa
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# --- 1. 경로 및 설정 ---
# 현재 파일(train_genre_model.py)이 있는 func 폴더
FUNC_DIR = os.path.dirname(os.path.abspath(__file__))
# func 폴더의 부모인 scripts 폴더
SCRIPTS_DIR = os.path.dirname(FUNC_DIR)
# scripts 폴더의 부모인 backend 폴더 (올바른 경로)
BACKEND_DIR = os.path.dirname(SCRIPTS_DIR) 

# GTZAN 데이터셋 폴더 경로를 올바르게 설정
DATASET_PATH = os.path.join(BACKEND_DIR, 'data', 'genres') 
MODELS_DIR = os.path.join(BACKEND_DIR, 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

GENRE_LABELS = ['blues', 'classical', 'country', 'disco', 'hiphop', 'jazz', 'metal', 'pop', 'reggae', 'rock']

# --- 2. 특징 추출 함수 ---
def extract_librosa_features(file_path):
    try:
        y, sr = librosa.load(file_path, mono=True, duration=30)
        mfccs = np.mean(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20).T, axis=0)
        chroma = np.mean(librosa.feature.chroma_stft(y=y, sr=sr).T, axis=0)
        contrast = np.mean(librosa.feature.spectral_contrast(y=y, sr=sr).T, axis=0)
        return np.hstack([mfccs, chroma, contrast])
    except Exception as e:
        print(f"특징 추출 오류: {file_path}, {e}")
        return None

# --- 3. 데이터 로드 및 학습 ---
print("장르 데이터셋 로드 및 특징 추출을 시작합니다...")
X, y = [], []
for i, genre in enumerate(GENRE_LABELS):
    genre_path = os.path.join(DATASET_PATH, genre, '*.wav')
    print(f"'{genre}' 장르 처리 중...")
    for file_path in glob.glob(genre_path):
        features = extract_librosa_features(file_path)
        if features is not None:
            X.append(features)
            y.append(i)

if not X:
    print(f"오류: '{DATASET_PATH}'에서 학습 데이터를 찾을 수 없습니다. GTZAN 데이터셋을 다운로드하고 경로를 확인해주세요.")
else:
    X = np.array(X)
    y = np.array(y)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    print("\nRandom Forest 모델 학습을 시작합니다...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"모델 정확도: {accuracy * 100:.2f}%")

    # --- 4. 모델 저장 ---
    save_path = os.path.join(MODELS_DIR, "genre_classifier.pkl")
    joblib.dump(model, save_path)
    print(f"\n✅ 장르 분류 모델 저장 완료! 파일 위치: {save_path}")