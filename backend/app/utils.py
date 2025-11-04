import re

def clean_song_title(title: str) -> str:
    """
    파일 이름에서 불필요한 부분을 최대한 제거하여 순수한 '노래 제목'만 반환하는 함수
    (참고: 이 함수는 더 이상 'singer_name' 인자를 받지 않습니다)
    """
    cleaned_title = title

    # 1. 파일 확장자 제거 (가장 먼저)
    cleaned_title = re.sub(r'(\.wav|\.mp3|\.m4a)$', '', cleaned_title, flags=re.IGNORECASE).strip()

    # 2. 괄호 [], () 안의 모든 내용 제거
    cleaned_title = re.sub(r'\[.*?\]', '', cleaned_title).strip()
    cleaned_title = re.sub(r'\(.*?\)', '', cleaned_title).strip()

    # 3. '가수 - 제목' 형식에서 가수 부분 제거 (하이픈 앞의 모든 것)
    #    "가수 - 부제 - 제목" 같은 경우를 대비해, 가장 마지막 '-'를 기준으로 분리 시도
    parts = cleaned_title.rsplit(' - ', 1) # 오른쪽에서부터 ' - '로 1번만 분리
    if len(parts) > 1:
        cleaned_title = parts[1].strip() # ' - ' 뒤의 내용을 제목으로 간주
    
    # 4. 불필요한 단어들 제거 (대소문자 무시)
    words_to_remove = [
        'mr제거', 'mr removed', '무반주', 'acapella', 'vocal only', 'lyrics', '가사',
        'vocals', 'official', 'mv', 'music video', 'audio', 'full ver', 'ver\.', 'ver',
        '역대급 고퀄리티', '반주제거', '풀버전', 'ost part', 'ost'
    ]
    # 단어 경계(\b)를 사용하여 더 정확하게 제거
    pattern = re.compile(r'\b(?:' + '|'.join(re.escape(word) for word in words_to_remove) + r')\b', re.IGNORECASE)
    cleaned_title = pattern.sub('', cleaned_title)

    # 5. 최종 정리: 언더스코어, 따옴표, 숫자, 맨앞/뒤 '-' 제거 및 공백 정리
    cleaned_title = cleaned_title.replace('_', ' ').replace('＂', '').replace('"', '').replace("'", "").strip()
    cleaned_title = cleaned_title.replace('⧸', '-').replace('｜', '-').replace('/', '-')
    cleaned_title = re.sub(r'^\d+\s*', '', cleaned_title).strip() # 맨 앞 숫자
    cleaned_title = re.sub(r'\s+', ' ', cleaned_title).strip() # 여러 공백을 하나로
    cleaned_title = re.sub(r'^\s*-\s*|\s*-\s*$', '', cleaned_title).strip() # 맨 앞/뒤 '-'

    return cleaned_title if len(cleaned_title) > 1 else title.split('[')[0].split('(')[0].strip()