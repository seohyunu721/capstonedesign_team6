# backend/app/utils.py
import re

def clean_song_title(title: str) -> str:
    """
    파일 이름에서 불필요한 부분을 제거하는 가장 단순하고 안정적인 함수
    """
    cleaned_title = title

    # 1. 괄호 [] 와 () 안의 모든 내용 제거
    cleaned_title = re.sub(r'\[.*?\]', '', cleaned_title).strip()
    cleaned_title = re.sub(r'\(.*?\)', '', cleaned_title).strip()

    # 2. 파일명에 사용할 수 없는 특수문자 변경
    cleaned_title = cleaned_title.replace('⧸', '-').replace('｜', '-').replace('/', '-')
    
    # 3. 불필요한 단어들 제거 (대소문자 무시)
    words_to_remove = [
        'mr제거', '무반주', 'acapella', 'vocal only', 'lyrics', '가사', 
        '_vocals', 'official', 'mv', 'music video'
    ]
    # 정규표현식을 사용하여 단어들을 한 번에 제거 (대소문자 무시)
    # | (OR) 연산자로 단어들을 연결
    pattern = re.compile('|'.join(words_to_remove), re.IGNORECASE)
    cleaned_title = pattern.sub('', cleaned_title)
    
    # 4. 최종 정리: 언더스코어, 따옴표 제거 및 공백 정리
    cleaned_title = cleaned_title.replace('_', ' ').replace('＂', '').replace('"', '').replace("'", "").strip()
    cleaned_title = re.sub(r'\s+', ' ', cleaned_title).strip() # 여러 공백을 하나로

    # '가수 - 제목' 형식에서 앞뒤 공백 제거
    cleaned_title = re.sub(r'\s*-\s*', ' - ', cleaned_title).strip()

    return cleaned_title if cleaned_title else title