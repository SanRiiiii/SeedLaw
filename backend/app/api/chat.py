from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
import datetime
import logging
from app.db.session import get_db
from app.db.models import User, Conversation, Message
from app.api.auth import get_current_active_user
from app.chat_management.chat_service import get_chat_service

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# 聊天请求模型
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    include_history: bool = True  # Whether to include conversation history context

# 聊天响应模型
class ChatResponse(BaseModel):
    reply: str
    sources: List = []
    conversation_id: str

# 对话模型
class ConversationModel(BaseModel):
    id: str
    title: str
    created_at: datetime.datetime

    class Config:
        orm_mode = True
        json_encoders = {
            datetime.datetime: lambda v: v.isoformat()
        }

# 消息模型
class MessageModel(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime.datetime
    
    class Config:
        orm_mode = True
        json_encoders = {
            datetime.datetime: lambda v: v.isoformat()
        }

# 包含消息的对话模型
class ConversationWithMessages(ConversationModel):
    messages: List[MessageModel]


# 创建聊天服务实例 - 纯工作流模式
chat_service = get_chat_service()


@router.post("/generate_chat", response_model=ChatResponse)
async def generate_chat(
    request: ChatRequest, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """处理聊天请求并保存到会话历史"""
    try:
        # 准备用户上下文
        user_context = None
        if current_user.company_info:
            user_context = {
                "company": {
                    "company_name": current_user.company_info.company_name,
                    "industry": current_user.company_info.industry,
                    "address": current_user.company_info.address,
                    "financing_stage": current_user.company_info.financing_stage,
                    "business_scope": current_user.company_info.business_scope,
                    "additional_info": current_user.company_info.additional_info
                }
            }
        
        # 使用聊天服务处理请求 - 所有数据库操作都在服务内处理
        response = await chat_service.process_chat(
            query=request.message,
            conversation_id=request.conversation_id,
            db_session=db,
            user_id=current_user.id,
            user_context=user_context,
            include_history=request.include_history
        )
        
        return ChatResponse(
            reply=response["answer"],
            sources=response.get("sources", []),
            conversation_id=response["conversation_id"]
        )
    except Exception as e:
        logger.error(f"处理聊天请求时发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# 登陆后，获取所有对话 
@router.get("/conversations", response_model=List[ConversationModel])
async def get_conversations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all conversations for current user"""
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).all()
    
    return conversations

# 获取某一个对话
@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific conversation with all messages"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return conversation

@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a conversation"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    db.delete(conversation)
    db.commit()
    
    return None

@router.put("/conversations/{conversation_id}/title", response_model=ConversationModel)
async def update_conversation_title(
    conversation_id: str,
    title: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update conversation title"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    conversation.title = title
    db.commit()
    db.refresh(conversation)
    
    return conversation