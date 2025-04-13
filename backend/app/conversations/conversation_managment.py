from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models import Conversation, Message, User
from app.core.config import settings                                                                                                                              
class ConversationService:
    @staticmethod
    def get_conversation_history(db: Session, conversation_id: str, limit: int = settings.CONTEXT_LENGTH) -> List[Dict[str, Any]]:
        """
        Get conversation history for a specific conversation
        Returns the last 'limit' messages in chronological order
        """
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.desc()).limit(limit).all()
        
        # Reverse to get chronological order
        messages.reverse()
        
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "metadata": msg.metadata
            }
            for msg in messages
        ]
    
    @staticmethod
    def format_history_for_llm(history: List[Dict[str, Any]]) -> str:
        """
        Format conversation history for the LLM
        """
        formatted_history = ""
        for msg in history:
            role_prefix = "用户: " if msg["role"] == "user" else "助手: "
            formatted_history += f"{role_prefix}{msg['content']}\n\n"
        
        return formatted_history
    
    @staticmethod
    def create_new_conversation(db: Session, user_id: int) -> Conversation:
        """
        Create a new conversation
        """
        conversation = Conversation(user_id=user_id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation
    
    @staticmethod
    def save_message(
        db: Session, 
        conversation_id: str, 
        role: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """
        Save a message to a conversation
        """
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata=metadata or {}
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
    
    @staticmethod
    def update_conversation_title(db: Session, conversation_id: str, message_content: str) -> None:
        """
        Update conversation title based on user message
        """
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation and conversation.title == "New Conversation" and message_content:
            # Use first few characters of user message as title
            title = message_content[:30] + ("..." if len(message_content) > 30 else "")
            conversation.title = title
            db.commit()