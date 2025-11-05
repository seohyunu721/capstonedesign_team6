import yt_dlp
import os

# 1. 다운로드할 유튜브 영상 주소
url = 'https://www.youtube.com/watch?v=Xm5R1OIYScU'

# 2. yt-dlp 옵션 설정
ydl_opts = {
    # 'bestaudio/best' -> 최고 음질의 오디오를 선택
    'format': 'bestaudio/best',
    
    # 저장할 폴더와 파일명 형식 지정
    # 예: 'data/iu_songs/영상제목.wav'
    'outtmpl': '/Users/yubin/Documents/캡스톤/com/Capstonedesign-6/backend/data/original/%(title)s.%(ext)s',
    
    # 후처리(postprocessors) 설정: 다운로드 후 오디오만 wav로 추출
    'postprocessors': [{
        'key': 'FFmpegExtractAudio', # FFmpeg를 사용해 오디오 추출
        'preferredcodec': 'wav',     # 선호하는 코덱을 wav로 설정
    }],
}

print(f"'{url}' 영상의 오디오 다운로드를 시작합니다...")

try:
    # 3. yt-dlp 객체를 생성하고 다운로드 실행
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        
    print("다운로드 및 .wav 변환이 완료되었습니다!")

except Exception as e:
    print(f"오류가 발생했습니다: {e}")