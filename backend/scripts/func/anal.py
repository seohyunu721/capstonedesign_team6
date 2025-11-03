import os
import glob
import numpy as np
import librosa
from spleeter.separator import Separator

# === 1. 보컬 분리 ===
def isolate_vocals(input_path, output_dir='separated'):
    separator = Separator('spleeter:2stems')
    separator.separate_to_file(input_path, output_dir)
    base = os.path.splitext(os.path.basename(input_path))[0]
    vocal_path = os.path.join(output_dir, base, 'vocals.wav')
    return vocal_path

# === 2. 피치 추출 ===
def extract_valid_pitches(file_path):
    y, sr = librosa.load(file_path, sr=16000)
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
    valid = []
    for t in range(pitches.shape[1]):
        i = magnitudes[:, t].argmax()
        pitch = pitches[i, t]
        mag = magnitudes[i, t]
        if 65 < pitch < 1000 and mag > 0.1:
            valid.append(pitch)
    return valid

# === 3. 음역대 계산 ===
def get_vocal_range(pitches):
    if not pitches:
        return None, None
    low = librosa.hz_to_note(np.percentile(pitches, 5))
    high = librosa.hz_to_note(np.percentile(pitches, 95))
    return low, high

# === 4. 전체 실행 ===
def analyze_all_audio_files():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    audio_files = glob.glob(os.path.join(current_dir, '*.mp3')) + glob.glob(os.path.join(current_dir, '*.wav'))

    if not audio_files:
        print("❌ 분석할 오디오 파일이 없습니다.")
        return

    for audio in audio_files:
        print(f"\n🎙️ '{os.path.basename(audio)}' 분석 중...")
        vocal = isolate_vocals(audio)
        pitches = extract_valid_pitches(vocal)
        low, high = get_vocal_range(pitches)
        print(f"🎯 최저음: {low}, 최고음: {high}")

# === 5. 실행 ===
if __name__ == '__main__':
    analyze_all_audio_files()
