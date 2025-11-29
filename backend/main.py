import os
import uvicorn

if __name__ == "__main__":
    # OMP_NUM_THREADS 환경 변수 설정 (멀티스레딩 충돌 방지)
    os.environ["OMP_NUM_THREADS"] = "1"
    
    # "app.app:app" -> app 폴더 안의 app.py 파일에서 app 객체를 찾아 실행하라는 의미
    # reload=True는 코드가 변경될 때마다 서버를 자동으로 재시작해주는 편리한 기능
    # host="0.0.0.0"으로 변경하여 모든 네트워크 인터페이스에서 접근 가능하도록 함
    uvicorn.run("app.app:app", host="0.0.0.0", port=8000, reload=True)