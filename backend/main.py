import uvicorn

if __name__ == "__main__":
    # "app.app:app" -> app 폴더 안의 app.py 파일에서 app 객체를 찾아 실행하라는 의미
    # reload=True는 코드가 변경될 때마다 서버를 자동으로 재시작해주는 편리한 기능
    uvicorn.run("app.app:app", host="127.0.0.1", port=8000, reload=True)