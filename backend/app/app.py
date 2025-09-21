from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

# CORS 설정 수정
origins = [
    "http://localhost:3000",
    "http://localhost:8000", 
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "http://10.0.2.2:8000",
    "*"  # 개발 환경에서 모든 오리진 허용
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

class Item(BaseModel):
    name: str
    price: float

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}

######################################################################################################
@app.post("/items/")
def create_item(item: Item):
    return {"message": f"Item {item.name} with price {item.price} created successfully", "item": item}
######################################################################################################
# OPTIONS 요청을 명시적으로 처리
@app.options("/items/")
def options_items():
    return {"message": "OK"}

