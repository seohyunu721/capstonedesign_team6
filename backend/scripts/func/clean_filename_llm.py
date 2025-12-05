"""
LLM을 사용한 파일명 정제 스크립트
YouTube에서 다운로드한 복잡한 파일명을 깔끔하게 정제합니다.
"""

import os
import sys
import re
import json
from typing import Optional

# 경로 설정
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(SCRIPTS_DIR) == 'func':
    SCRIPTS_DIR = os.path.dirname(SCRIPTS_DIR)
BACKEND_DIR = os.path.dirname(SCRIPTS_DIR)
sys.path.append(BACKEND_DIR)

try:
    from app.utils import clean_song_title
except ImportError:
    print("⚠️ app.utils.clean_song_title을 찾을 수 없습니다. 기본 정제 함수를 사용합니다.")
    clean_song_title = None

# OpenAI API 사용 (선택사항)
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("⚠️ openai 패키지가 설치되지 않았습니다. LLM 기능은 사용할 수 없습니다.")


def clean_with_llm(filename: str, api_key: Optional[str] = None) -> str:
    """
    LLM을 사용하여 파일명을 정제합니다.
    
    Args:
        filename: 정제할 파일명
        api_key: OpenAI API 키 (None이면 환경 변수에서 가져옴)
    
    Returns:
        정제된 파일명
    """
    if not HAS_OPENAI:
        return clean_with_regex(filename)
    
    try:
        client = openai.OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        
        prompt = f"""다음은 YouTube에서 다운로드한 음악 파일명입니다. 
가수 이름과 노래 제목만 남기고 나머지는 모두 제거해주세요.

원본 파일명: {filename}

규칙:
1. 가수 이름과 노래 제목만 남기기
2. 형식: "가수명 - 노래제목"
3. 불필요한 정보 제거: [Official MV], (Audio), [가사], [Lyrics], 풀버전, ver., 등
4. 특수문자 최소화
5. 공백 정리

정제된 파일명만 출력하세요:"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 파일명 정제 전문가입니다. 가수명과 노래 제목만 남기고 나머지는 제거합니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=100
        )
        
        cleaned = response.choices[0].message.content.strip()
        # 파일명에 사용할 수 없는 문자 제거
        cleaned = re.sub(r'[<>:"/\\|?*]', '', cleaned)
        return cleaned
        
    except Exception as e:
        print(f"⚠️ LLM 정제 실패: {e}, 정규식 방법으로 대체합니다.")
        return clean_with_regex(filename)


def clean_with_regex(filename: str) -> str:
    """
    정규식을 사용한 파일명 정제 (LLM 없이도 동작)
    """
    if clean_song_title:
        # 기존 utils 함수 사용
        return clean_song_title(filename)
    
    # 기본 정제 로직
    cleaned = filename
    
    # 확장자 제거
    cleaned = re.sub(r'\.(wav|mp3|m4a|flac)$', '', cleaned, flags=re.IGNORECASE)
    
    # 괄호 내용 제거
    cleaned = re.sub(r'\[.*?\]', '', cleaned)
    cleaned = re.sub(r'\(.*?\)', '', cleaned)
    cleaned = re.sub(r'【.*?】', '', cleaned)
    
    # 불필요한 키워드 제거
    keywords = [
        'official', 'mv', 'music video', 'audio', 'lyrics', '가사',
        'full ver', 'ver.', 'ver', 'version', '풀버전', 'ost',
        'official audio', 'official video', 'official mv',
        '【', '】', '｜', '⧸', 'lyric', 'lyrics video'
    ]
    for keyword in keywords:
        cleaned = re.sub(rf'\b{re.escape(keyword)}\b', '', cleaned, flags=re.IGNORECASE)
    
    # 특수문자 정리
    cleaned = cleaned.replace('_', ' ').replace('｜', ' - ').replace('⧸', ' - ')
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # 맨 앞/뒤 특수문자 제거
    cleaned = re.sub(r'^[-.\s]+|[-.\s]+$', '', cleaned)
    
    return cleaned if cleaned else filename


def clean_filename_batch(directory: str, use_llm: bool = False, api_key: Optional[str] = None):
    """
    디렉토리 내의 모든 파일명을 정제합니다.
    
    Args:
        directory: 정제할 파일이 있는 디렉토리
        use_llm: LLM 사용 여부 (기본값: False, 정규식 사용)
        api_key: OpenAI API 키
    """
    audio_extensions = ['.wav', '.mp3', '.m4a', '.flac']
    renamed_count = 0
    
    print(f"📁 디렉토리 스캔: {directory}")
    
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if any(filename.lower().endswith(ext) for ext in audio_extensions):
                old_path = os.path.join(root, filename)
                name, ext = os.path.splitext(filename)
                
                # 파일명 정제
                if use_llm and HAS_OPENAI:
                    cleaned_name = clean_with_llm(name, api_key)
                else:
                    cleaned_name = clean_with_regex(name)
                
                new_filename = cleaned_name + ext
                new_path = os.path.join(root, new_filename)
                
                if filename != new_filename:
                    try:
                        os.rename(old_path, new_path)
                        print(f"  ✅ {filename} -> {new_filename}")
                        renamed_count += 1
                    except Exception as e:
                        print(f"  ❌ {filename} 이름 변경 실패: {e}")
    
    print(f"\n✅ 총 {renamed_count}개 파일명 정제 완료!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="파일명 정제 스크립트")
    parser.add_argument("directory", help="정제할 디렉토리 경로")
    parser.add_argument("--llm", action="store_true", help="LLM 사용 (OpenAI API 필요)")
    parser.add_argument("--api-key", help="OpenAI API 키 (또는 OPENAI_API_KEY 환경 변수 사용)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.directory):
        print(f"❌ 디렉토리를 찾을 수 없습니다: {args.directory}")
        sys.exit(1)
    
    clean_filename_batch(args.directory, use_llm=args.llm, api_key=args.api_key)

