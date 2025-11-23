import joblib
import os

# 경로에 맞게 수정하세요
base_path = "/Users/yubin/Documents/캡스톤/com/Capstonedesign-6/backend/models"
file_path = os.path.join(base_path, "singer_id_map.pkl")

if os.path.exists(file_path):
    data = joblib.load(file_path)
    print("✅ singer_id_map 데이터:")
    print(data)
else:
    print(f"❌ 파일을 찾을 수 없습니다: {file_path}")