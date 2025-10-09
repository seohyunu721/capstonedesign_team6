import numpy as np
import faiss
import timeit

# --- 테스트 환경 설정 ---
DIMENSION = 192  # x-vector의 차원
NUM_VECTORS = 10  # DB에 있는 가수 수 (넉넉하게 10으로 설정)
K = 3            # 검색할 상위 K개

# --- 1. 가상 데이터 생성 ---
# 실제 DB와 유사하게 (가수 수, 차원) 모양의 가상 벡터 데이터 생성
db_vectors = np.random.random((NUM_VECTORS, DIMENSION)).astype('float32')
faiss.normalize_L2(db_vectors)

# 가상 사용자 목소리 벡터 생성
query_vector = np.random.random((1, DIMENSION)).astype('float32')
faiss.normalize_L2(query_vector)

# --- 2. Faiss 인덱스 생성 ---
index = faiss.IndexFlatIP(DIMENSION)
index.add(db_vectors)

print(f"{NUM_VECTORS}개의 벡터로 인덱스 생성 완료.")
print("Faiss.search() 순수 실행 속도를 10,000회 반복하여 측정합니다...")

# --- 3. 성능 측정 ---
# timeit을 사용하여 search 함수를 10,000번 실행하는 데 걸리는 총 시간 측정
total_time = timeit.timeit(lambda: index.search(query_vector, K), number=10000)

avg_time_ms = (total_time / 10000) * 1000  # 평균 시간을 밀리초(ms)로 변환

print("\n--- 측정 결과 ---")
print(f"1회 검색 평균 소요 시간: {avg_time_ms:.6f} ms (밀리초)")