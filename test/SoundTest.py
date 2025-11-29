import sys
import numpy as np
import librosa
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5 import QtWidgets, QtCore, QtGui

# -----------------------
# 설정 파라미터 (정확도 조절용)
# -----------------------
SR = 22050           # 샘플링 레이트 (표준)
HOP_LENGTH = 256     # 촘촘하게 분석 (작을수록 시간 해상도 높음)
FRAME_LENGTH = 2048  # 저음 분석을 위한 프레임 길이
CONF_THRESH = 0.6   # 피치 신뢰도 (이 값보다 낮은 확률의 피치는 무시)
RMS_THRESH = 0.05    # 에너지 임계값 (이 값보다 작은 소리는 무시 - 잡음 제거 핵심)

# -----------------------
# 유틸리티 함수
# -----------------------
def midi_to_note_name(midi_val):
    """MIDI 번호를 'C4', 'D#5' 형태의 문자열로 변환"""
    if np.isnan(midi_val): return ""
    return librosa.midi_to_note(int(round(midi_val)))

def format_axis(x, pos):
    """Matplotlib 축을 위한 포맷터"""
    return midi_to_note_name(x)

# -----------------------
# 분석 로직 (핵심)
# -----------------------
def analyze_audio_precision(file_path):
    # 1. 오디오 로드
    y, sr = librosa.load(file_path, sr=SR, mono=True)
    
    # 2. 피치 추출 (pYIN 알고리즘 - 가장 정확함)
    f0, voiced_flag, voiced_probs = librosa.pyin(
        y, 
        fmin=librosa.note_to_hz('C2'), # 일반적인 가창 범위 고려
        fmax=librosa.note_to_hz('C7'), 
        sr=sr, 
        hop_length=HOP_LENGTH,
        frame_length=FRAME_LENGTH,
        fill_na=np.nan
    )
    
    # 3. 에너지(RMS) 계산 - 소리 크기가 너무 작은 구간 필터링용
    rms = librosa.feature.rms(y=y, frame_length=FRAME_LENGTH, hop_length=HOP_LENGTH)[0]
    # RMS 길이를 f0 길이에 맞춤 (가끔 1프레임 차이 날 수 있음)
    rms = librosa.util.fix_length(rms, size=len(f0))

    # 4. 정밀 필터링 (정확도 향상의 핵심)
    # 조건: 피치 신뢰도가 높고 AND 소리 크기(RMS)가 일정 이상이어야 함
    valid_mask = (voiced_probs > CONF_THRESH) & (rms > RMS_THRESH)
    
    # 유효하지 않은 구간은 NaN 처리
    f0_clean = np.where(valid_mask, f0, np.nan)
    
    # 5. Hz -> MIDI 변환
    midi_clean = librosa.hz_to_midi(f0_clean)

    # 6. 통계 계산 (이상치 제거)
    valid_midi = midi_clean[~np.isnan(midi_clean)]
    
    if len(valid_midi) == 0:
        return None  # 유효한 음정이 없음

    # 삑사리(Outlier) 제거: 상위/하위 1%를 제외한 범위를 진짜 범위로 인정
    # 이렇게 해야 순간적인 잡음을 최고음으로 인식하는 오류를 막음
    low_p = np.percentile(valid_midi, 1)  
    # high_p = np.percentile(valid_midi, 99) 
    high_p = np.percentile(valid_midi) 
    
    # 가장 빈번하게 등장한 음 (중심음)
    median_midi = np.median(valid_midi)

    times = librosa.times_like(midi_clean, sr=sr, hop_length=HOP_LENGTH)
    
    return {
        "times": times,
        "midi": midi_clean,
        "min_midi": low_p,
        "max_midi": high_p,
        "min_note": midi_to_note_name(low_p),
        "max_note": midi_to_note_name(high_p),
        "median_note": midi_to_note_name(median_midi)
    }

# -----------------------
# GUI 구현
# -----------------------
class AnalysisWorker(QtCore.QThread):
    finished = QtCore.pyqtSignal(object)

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        result = analyze_audio_precision(self.path)
        self.finished.emit(result)

class PrecisePitchApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("정밀 음역대 분석기 (Post-Processor)")
        self.resize(1000, 700)
        self.init_ui()

    def init_ui(self):
        # 레이아웃
        main_layout = QtWidgets.QVBoxLayout()
        
        # 상단 컨트롤
        control_layout = QtWidgets.QHBoxLayout()
        self.btn_load = QtWidgets.QPushButton("📂 오디오 파일 열기")
        self.btn_load.setMinimumHeight(40)
        self.btn_load.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        self.btn_load.clicked.connect(self.load_file)
        
        self.status_label = QtWidgets.QLabel("파일을 선택해주세요.")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        
        control_layout.addWidget(self.btn_load)
        control_layout.addWidget(self.status_label)
        
        # 결과 표시 패널
        info_layout = QtWidgets.QHBoxLayout()
        self.lbl_low = self.create_info_box("최저음 (Low)", "-")
        self.lbl_high = self.create_info_box("최고음 (High)", "-")
        self.lbl_avg = self.create_info_box("중심음 (Avg)", "-")
        
        info_layout.addWidget(self.lbl_low)
        info_layout.addWidget(self.lbl_high)
        info_layout.addWidget(self.lbl_avg)

        # 그래프 영역
        self.fig, self.ax = plt.subplots(figsize=(10, 5))
        self.canvas = FigureCanvas(self.fig)
        
        main_layout.addLayout(control_layout)
        main_layout.addLayout(info_layout)
        main_layout.addWidget(self.canvas)
        
        self.setLayout(main_layout)

    def create_info_box(self, title, init_val):
        group = QtWidgets.QGroupBox(title)
        layout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel(init_val)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setFont(QtGui.QFont("Arial", 16, QtGui.QFont.Bold))
        label.setStyleSheet("color: #333333;")
        layout.addWidget(label)
        group.setLayout(layout)
        # 나중에 값을 바꾸기 위해 객체에 label 저장
        group.value_label = label 
        return group

    def load_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "오디오 선택", "", "Audio (*.wav *.mp3 *.flac *.m4a)")
        if path:
            self.status_label.setText("분석 중입니다... (잠시만 기다려주세요)")
            self.btn_load.setEnabled(False)
            
            # 스레드 시작
            self.worker = AnalysisWorker(path)
            self.worker.finished.connect(self.on_finished)
            self.worker.start()

    def on_finished(self, result):
        self.btn_load.setEnabled(True)
        
        if result is None:
            self.status_label.setText("분석 실패: 유효한 음정을 찾지 못했습니다.")
            return
            
        self.status_label.setText("분석 완료")
        
        # 텍스트 업데이트
        self.lbl_low.value_label.setText(result['min_note'])
        self.lbl_high.value_label.setText(result['max_note'])
        self.lbl_avg.value_label.setText(result['median_note'])
        
        # 그래프 그리기
        self.draw_graph(result)

    def draw_graph(self, res):
        self.ax.clear()
        
        times = res['times']
        midi = res['midi']
        
        # 1. 메인 피치 라인 그리기 (파란색)
        # 산점도(Scatter)로 그리면 끊어짐이 더 잘 보여서 분석에 유리함
        self.ax.scatter(times, midi, s=5, c='#2980b9', alpha=0.6, label='Pitch Detected')
        
        # 2. Y축 설정 (핵심: MIDI 숫자 -> 음계 이름)
        min_m = int(np.nanmin(midi)) - 2
        max_m = int(np.nanmax(midi)) + 2
        
        # Y축 범위를 데이터에 맞춤
        self.ax.set_ylim(min_m, max_m)
        
        # Y축 눈금을 1단위(반음)로 설정
        self.ax.set_yticks(range(min_m, max_m + 1))
        
        # Y축 포맷터를 적용하여 C4, C#4 등으로 표시
        self.ax.yaxis.set_major_formatter(FuncFormatter(format_axis))
        
        # 3. 최저/최고 가이드라인 (점선)
        self.ax.axhline(res['min_midi'], color='green', linestyle='--', linewidth=2, label=f"Min: {res['min_note']}")
        self.ax.axhline(res['max_midi'], color='red', linestyle='--', linewidth=2, label=f"Max: {res['max_note']}")
        
        # 4. 그리드 및 스타일
        self.ax.grid(True, which='both', linestyle='-', alpha=0.3)
        self.ax.set_xlabel("Time (seconds)")
        self.ax.set_ylabel("Musical Note")
        self.ax.set_title("Vocal Pitch Analysis")
        self.ax.legend(loc='upper right')
        
        self.fig.tight_layout()
        self.canvas.draw()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    
    # 앱 스타일링 (선택사항)
    app.setStyle("Fusion")
    
    window = PrecisePitchApp()
    window.show()
    sys.exit(app.exec_())