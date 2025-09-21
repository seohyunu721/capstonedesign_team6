from fastapi import FastAPI
app = FastAPI()

# from fastapi.middleware.cors import CORSMiddleware

# origins = ["http://localhost",
#            "http://localhost:8000",
#            "http://10.0.2.2:8000"]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origns=origins, # 허용할 출저 설정
#     allow_credentials=True, # 인증 정보(쿠키, 인증 헤더 등 ) 허용 여부
#     allow_methods=["*"], # 모든 HTTP 메서드 (GET, POST, PUT 등) 허용
#     allow_headers=["*"], # 모든 HTTP 헤더를 허용 --> 헤더
# )


@app.get("/")
def 작명():
    return {"message": "Hello from FastAPI"}


# from fastapi.responses import FileResponse
# @app.get("/")
# def 작명(): 
#     return FileResponse('index.html')

# @app.get("/data")
# def 작명():
#     return {'hello' : 1234}