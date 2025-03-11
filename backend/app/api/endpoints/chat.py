
# app/api/chat.py - 聊天API路由
from fastapi import APIRouter
from pydantic import BaseModel
from app.services.rag_service import RagService

router = APIRouter(prefix="/api", tags=["chat"])
rag_service = RagService()

# API接受的请求体格式，目前是message，后续也可以加用户信息等等
class ChatRequest(BaseModel):
    message: str

# 定义法律来源的数据结构
class Source(BaseModel):
    title: str
    content: str

# 定义API返回的相应格式
class ChatResponse(BaseModel):
    reply: str
    sources: list[Source] = []

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """处理用户聊天请求"""
    reply, sources = rag_service.get_response(request.message)
    return ChatResponse(reply=reply, sources=sources)