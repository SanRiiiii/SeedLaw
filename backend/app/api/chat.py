from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models import User, Conversation, Message
from app.api.auth import get_current_active_user
from app.rag.response_generator import Generator
from app.conversations.conversation_managment import ConversationService
from app.core.config import settings

router = APIRouter(prefix="/chat", tags=["chat"])
rag_service = Generator()
conversation_service = ConversationService()

# 来源模型
class Source(BaseModel):
    title: str
    content: str

# 聊天请求模型
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    include_history: bool = True  # Whether to include conversation history context

# 聊天响应模型
class ChatResponse(BaseModel):
    reply: str
    sources: List[Source] = []
    conversation_id: str

# 对话模型
class ConversationModel(BaseModel):
    id: str
    title: str
    created_at: str
    
    class Config:
        orm_mode = True

# 消息模型
class MessageModel(BaseModel):
    id: int
    role: str
    content: str
    created_at: str
    
    class Config:
        orm_mode = True

# 包含消息的对话模型
class ConversationWithMessages(ConversationModel):
    messages: List[MessageModel]

@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Handle chat request and save to conversation history"""
    # 获取或者创建对话
    conversation = None
    if request.conversation_id:
        # 获取现有对话
        conversation = db.query(Conversation).filter(
            Conversation.id == request.conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
    else:
        # 创建新对话
        conversation = conversation_service.create_new_conversation(db, current_user.id)
    
    # 保存用户消息
    conversation_service.save_message(
        db,
        conversation.id,
        "user",
        request.message,
    )
    
    # 如果可用，将公司上下文添加到查询中
    company_context = ""
    if current_user.company_info:
        company_context = f"Company: {current_user.company_info.company_name},、
          Industry: {current_user.company_info.industry},
          Address: {current_user.company_info.address},
          Financing Stage: {current_user.company_info.financing_stage},
          Business Scope: {current_user.company_info.business_scope},
          Additional Info: {current_user.company_info.additional_info}"

    # 准备查询
    enhanced_query = request.message
    
    # 如果请求包含历史，将历史添加到查询中
    conversation_history = ""
    if request.include_history and request.conversation_id:
        # 从对话历史中获取最后N条消息
        history = conversation_service.get_conversation_history(db, conversation.id, limit=settings.CONTEXT_LENGTH)
        if history:
            conversation_history = conversation_service.format_history_for_llm(history)
    
    # 将上下文添加到查询中
    if conversation_history:
        enhanced_query = f"Conversation history:\n{conversation_history}\n\nCurrent message: {request.message}"
    
    # 如果可用，将公司上下文添加到查询中
    if company_context:
        enhanced_query = f"{enhanced_query}\n\nContext: {company_context}"
    
    # 从RAG服务获取回复
    reply, sources = rag_service.get_response(enhanced_query)
    
    # 保存助手消息
    conversation_service.save_message(
        db,
        conversation.id,
        "assistant",
        reply,
        {"sources": [{"title": s.title, "content": s.content} for s in sources]}
    )
    
    # 如果对话是新对话，更新对话标题
    conversation_service.update_conversation_title(db, conversation.id, request.message)
    
    return ChatResponse(
        reply=reply,
        sources=sources,
        conversation_id=conversation.id
    )

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