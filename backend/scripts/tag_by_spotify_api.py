import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# --- 사전 준비 ---
# 1. 스포티파이 개발자 사이트에서 계정 만들고 앱 등록
# 2. Client ID와 Client Secret 발급받기
CLIENT_ID = "a2c4860d3fd5488588e05b1e90f76b78"
CLIENT_SECRET = "1d8ac11f5f594384a31779cfe17a2941"
# -----------------

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET))

def get_info_from_spotify(song_title, artist_name):
    results = sp.search(q=f'track:{song_title} artist:{artist_name}', type='track', limit=1)

    if not results['tracks']['items']:
        return '정보 없음', '정보 없음'

    track = results['tracks']['items'][0]
    artist_id = track['artists'][0]['id']

    # 아티스트 정보를 가져와서 장르와 성별(추정) 확인
    artist_info = sp.artist(artist_id)
    genres = artist_info['genres'] # 스포티파이는 장르를 여러 개 제공

    # 성별 정보는 공식적으로 없지만, 다른 데이터를 활용해 추정 가능
    # ... (성별 추정 로직) ...

    return genres

def get_audio_features(song_title, artist_name):
    # 노래 검색
    results = sp.search(q=f'track:{song_title} artist:{artist_name}', type='track', limit=1)
    if not results['tracks']['items']:
        return None

    track_id = results['tracks']['items'][0]['id']
    # 오디오 특성 가져오기
    audio_features = sp.audio_features(track_id)[0]
    return audio_features

# 사용 예시
genres = get_info_from_spotify("죽일 놈", "다이나믹듀오")
print(f"아이유 - 밤편지'의 스포티파이 장르: {genres}")
# 이 결과를 songs_db.json에 업데이트

# 사용 예시
features = get_audio_features("Shape of You", "Ed Sheeran")
if features:
    print("오디오 특성:", features)
else:
    print("노래 정보를 찾을 수 없습니다.")