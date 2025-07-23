# app/main.py - 应用入口
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router
from app.db.session import engine
from app.db.models import Base  

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(title="法律知识问答系统")

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "法律知识问答系统API"}
