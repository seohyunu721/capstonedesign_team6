import os
import glob
import numpy as np
import joblib
import faiss

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
MODELS_DIR = os.path.join(BACKEND_DIR, "models")
print(f"'{MODELS_DIR}' 폴더에서 기존 가수 모델 파일(.xvector)을 불러옵니다...")

all_singer_xvectors = []
singer_id_map = {}
current_id = 0

for model_file in glob.glob(os.path.join(MODELS_DIR, '*.xvector')):
    print(f"--- 파일 처리 시작: {model_file} ---")
    singer_name = os.path.splitext(os.path.basename(model_file))[0]
    
    try:
        # 변수 이름을 avg_xvector로 통일
        avg_xvector = joblib.load(model_file)
        
        # 불러온 벡터가 2차원 이상일 경우, 평균을 내어 1차원으로 통일
        final_xvector = np.mean(avg_xvector, axis=0) if avg_xvector.ndim > 1 else avg_xvector
        
        if final_xvector is not None:
            print(f"성공적으로 로드 및 처리됨. 최종 형태(shape): {final_xvector.shape}")
            all_singer_xvectors.append(final_xvector)
            singer_id_map[current_id] = singer_name
            current_id += 1
        else:
            print(f"!!! 오류: 파일 내용이 비어있습니다.")

    except Exception as e:
        print(f"!!! 오류: {model_file} 파일을 불러오는 중 문제 발생: {e}")


if all_singer_xvectors:
    print("\nFaiss 인덱스를 생성하고 저장합니다...")
    
    # --- 디버깅 코드 추가 ---
    try:
        vectors = np.array(all_singer_xvectors).astype('float32')
        print(f"최종 'vectors' 배열의 형태(shape): {vectors.shape}") # 이 부분이 (3, 192) 여야 함
    except Exception as e:
        print(f"!!! 오류: Numpy 배열 변환 중 문제 발생. 각 벡터의 길이가 다를 수 있습니다. 오류: {e}")
        exit() # 문제가 있으면 여기서 종료
    # --------------------

    ids = np.array(list(singer_id_map.keys())).astype('int64')

    faiss.normalize_L2(vectors)

    dimension = vectors.shape[1]
    index = faiss.IndexFlatIP(dimension)
    id_index = faiss.IndexIDMap(index)
    id_index.add_with_ids(vectors, ids)

    faiss.write_index(id_index, os.path.join(MODELS_DIR, "singers.index"))
    joblib.dump(singer_id_map, os.path.join(MODELS_DIR, "singer_id_map.pkl"))
    print("Faiss 인덱스 및 가수 ID 맵 저장 완료!")
else:
    print("처리할 .xvector 파일이 없습니다.")