import os
import subprocess
import glob
import shutil  # 파일/폴더 관리를 위한 라이브러리
import sys

# --- 설정 ---
# 원본 음원 파일이 있는 폴더 (MR 제거 대상) // 자기에 맞게 변경경
INPUT_DIR = "C:\\Users\\jun12\\OneDrive\\바탕 화면\\capstone\\capstonedesign_team6\\backend\\data\\original\\"

# 최종 보컬 파일을 저장할 기본 폴더 // 자기에 맞게 변경
OUTPUT_BASE_DIR = "C:\\Users\\jun12\\OneDrive\\바탕 화면\\capstone\\capstonedesign_team6\\backend\\data\\no_mr\\"
# ------------

# 결과 폴더가 없으면 생성
os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)

# 처리할 음원 파일 목록 가져오기
audio_files = glob.glob(os.path.join(INPUT_DIR, '*.wav')) + \
              glob.glob(os.path.join(INPUT_DIR, '*.mp3')) + \
              glob.glob(os.path.join(INPUT_DIR, '*.m4a'))

if not audio_files:
    print(f"'{INPUT_DIR}' 폴더에 처리할 음원 파일이 없습니다.")
    # 처리할 파일이 없는 경우에도 정상 종료하여 파이프라인이 다음 단계로 진행되도록 함
    sys.exit(0)
else:
    print(f"총 {len(audio_files)}개의 파일에 대해 MR 제거를 시작합니다...")
    for file_path in audio_files:
        print(f"\n--> 처리 중: {os.path.basename(file_path)}")
        
        # 가수 이름 추출 (파일 이름에서 가수 이름을 추출한다고 가정)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        singer_name = base_name.split('-')[0] + "_songs"  # 파일 이름이 "가수_노래제목" 형식이라고 가정
        singer_output_dir = os.path.join(OUTPUT_BASE_DIR, singer_name)

        # 가수별 폴더 생성
        os.makedirs(singer_output_dir, exist_ok=True)

        # 임시 결과물이 저장될 경로
        temp_output_dir = os.path.join(singer_output_dir, "temp_separated")

        command = [
            sys.executable, "-m", "demucs",
            "-n", "htdemucs_ft",
            "--two-stems=vocals",
            "-o", temp_output_dir,  # 임시 폴더에 결과 저장
            file_path
        ]
        
        try:
            # Demucs 명령 실행
            subprocess.run(command, check=True)

            # demucs가 생성한 보컬 파일의 경로
            vocal_file_path = os.path.join(temp_output_dir, "htdemucs_ft", base_name, "vocals.wav")

            if os.path.exists(vocal_file_path):
                # 최종적으로 저장될 파일 경로와 이름
                final_vocal_path = os.path.join(singer_output_dir, f"{base_name}_vocals.wav")
                
                # 보컬 파일을 최종 위치로 이동하고 이름 변경
                shutil.move(vocal_file_path, final_vocal_path)
                print(f"--> 보컬 파일 저장 완료: {final_vocal_path}")

                # 원본 음원 파일 삭제
                os.remove(file_path)
                print(f"--> 원본 파일 삭제 완료: {file_path}")

                # demucs가 만든 임시 폴더 전체를 삭제
                shutil.rmtree(os.path.join(temp_output_dir, "htdemucs_ft"))
            else:
                print(f"--> 오류: '{base_name}' 파일 처리 후 보컬 파일을 찾을 수 없습니다.")
        except subprocess.CalledProcessError as e:
            print(f"!!! 오류: '{os.path.basename(file_path)}' 처리 중 문제 발생: {e}")
        except Exception as e:
            print(f"!!! 예기치 못한 오류 발생: {e}")

    # 임시 폴더가 비어있으면 삭제
    if os.path.exists(temp_output_dir) and not os.listdir(temp_output_dir):
        os.rmdir(temp_output_dir)

    print("\n모든 작업이 완료되었습니다!")
    print(f"결과물은 '{OUTPUT_BASE_DIR}' 폴더 안에 저장되었습니다.")