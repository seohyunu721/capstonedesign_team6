# 백엔드 실행

Windows에서는 아래 명령어를 사용하세요:

```
set OMP_NUM_THREADS=1 && python main.py
```

필요한 파이썬 패키지를 한 번에 설치하려면 아래 명령어를 사용하세요:

```
pip install -r backend/requirements.txt
```

# 프론트 실행

```
cd frontend
flutter run -d chrome
```

# 개발 환경 및 설치 가이드

## 1. Python 버전 안내
- **Python 3.10** 또는 **3.11** 버전 사용을 권장합니다.
- 최신 버전(예: 3.13)은 일부 AI/음성 라이브러리와 호환되지 않을 수 있습니다.

## 2. Python 3.10 설치 및 가상환경 생성
1. [Python 3.10 다운로드](https://www.python.org/downloads/release/python-3100/) 후 설치 시 "Add Python to PATH" 체크
2. 터미널에서 아래 명령어 실행:
   ```
   py -3.10 -m venv venv
   venv\Scripts\activate
   ```

## 3. pip 업그레이드
가상환경 활성화 후 아래 명령어로 pip를 최신 버전으로 업그레이드:
```
venv\Scripts\python.exe -m pip install --upgrade pip
```

## 4. 필수 모듈 설치
아래 명령어로 모든 필요한 패키지를 한 번에 설치:
```
pip install -r backend/requirements.txt
```

## 5. 백엔드 실행
```
set OMP_NUM_THREADS=1 && python main.py
```

## 6. 프론트엔드 실행
```
cd frontend
flutter run -d chrome
```

## 7. 자주 발생하는 오류 및 해결법

- **ModuleNotFoundError: No module named 'xxx'**
  - requirements.txt에 해당 모듈이 없으면 추가 후 재설치
- **Could not find a version that satisfies the requirement torch==2.2.2**
  - Python 3.13에서는 torch 2.2.2 설치 불가 → Python 3.10 사용
- **AttributeError: module 'torchaudio' has no attribute 'list_audio_backends'**
  - torchaudio 버전 호환 문제 → torch/torchaudio를 2.2.2로 맞추기
- **pip 경고**
  - pip 업그레이드 필요 → 위 명령어 참고

---

# requirements.txt 예시

아래 파일을 `backend/requirements.txt`로 저장하세요.

````plaintext
# filepath: [requirements.txt](http://_vscodecontentref_/0)
fastapi
uvicorn
numpy
joblib
librosa
scikit-learn
pandas
soundfile
faiss-cpu
pyyaml
huggingface-hub
speechbrain
torch==2.2.2
torchaudio==2.2.2