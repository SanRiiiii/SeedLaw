import logging
import os
import sys
from typing import Dict, List, Any, Optional
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.app.models.llm import get_llm_service, LLMService
from app.core.config import settings
from app.db.models import Conversation, Message
from sqlalchemy.orm import Session

# 导入chat_workflow
from backend.app.chat_management.chat_workflow import process_with_workflow

# 配置日志格式
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)




class ChatService:
    """
    聊天服务类，使用LangGraph工作流进行消息处理
    """
    
    def __init__(self, llm_service: LLMService = None):
        """
        初始化聊天服务
        
        Args:
            llm_service: 大语言模型服务，如果为None则使用默认服务
        """
        logger.info("====================== 初始化 ChatService ======================")
        # 创建或使用提供的LLM服务
        self.llm_service = llm_service or get_llm_service()
        logger.info(f"LLM服务初始化完成: {type(self.llm_service).__name__}")
        logger.info("使用LangGraph工作流模式")
        logger.info("ChatService初始化完成")
    
    async def process_chat(
        self,
        query: str,
        conversation_id: str,
        db_session: Session,
        user_id: int = None,
        user_context: Optional[Dict[str, Any]] = None,
        include_history: bool = True
    ) -> Dict[str, Any]:
        """
        处理聊天请求，包括数据库操作
        
        Args:
            query: 用户查询
            conversation_id: 会话ID
            db_session: 数据库会话
            user_id: 用户ID
            user_context: 用户上下文
            include_history: 是否包含历史记录
            
        Returns:
            包含回答的字典
        """
        logger.info(f"====================== 开始处理聊天请求 ======================")
        logger.info(f"用户查询: {query}")
        logger.info(f"会话ID: {conversation_id}")
        logger.info(f"用户ID: {user_id}")
        logger.info(f"包含历史: {include_history}")
        
        # 如果是新会话ID (temp)，创建新对话
        conversation = None
        is_new_conversation = False
        try:
            if "temp" in conversation_id and user_id:
                logger.info(f"检测到临时会话ID，正在创建新会话...")
                # 创建新会话
                conversation = Conversation(user_id=user_id)
                db_session.add(conversation)
                db_session.commit()
                db_session.refresh(conversation)
                conversation_id = conversation.id
                is_new_conversation = True
                logger.info(f"新会话创建成功，ID: {conversation_id}")
            else:
                # 获取现有会话
                logger.info(f"获取现有会话: {conversation_id}")
                conversation = db_session.query(Conversation).filter(
                    Conversation.id == conversation_id
                ).first()
                
                if not conversation:
                    logger.error(f"会话ID不存在: {conversation_id}")
                    raise ValueError(f"会话ID不存在: {conversation_id}")
                logger.info(f"成功获取会话: {conversation.id}, 标题: {conversation.title}")
        except Exception as e:
            logger.error(f"处理会话时出错: {str(e)}", exc_info=True)
            raise
        
        # 获取聊天历史
        chat_history = None
        try:
            if include_history:
                logger.info(f"获取聊天历史...")
                messages = db_session.query(Message).filter(
                    Message.conversation_id == conversation_id
                ).order_by(Message.created_at.desc()).limit(10).all()
                
                # 反转顺序，使最早的消息在前
                messages.reverse()
                
                chat_history = [
                    {"role": msg.role, "content": msg.content}
                    for msg in messages
                ]
                logger.info(f"获取到 {len(chat_history)} 条历史消息")
                if chat_history:
                    for i, msg in enumerate(chat_history):
                        logger.debug(f"历史消息 {i+1}: [角色:{msg['role']}] {msg['content'][:50]}...")
        except Exception as e:
            logger.error(f"获取聊天历史时出错: {str(e)}", exc_info=True)
            chat_history = []
        
        # 保存用户消息
        try:
            logger.info(f"保存用户消息...")
            user_message = Message(
                conversation_id=conversation_id,
                role="user",
                content=query
            )
            db_session.add(user_message)
            db_session.commit()
            logger.info(f"用户消息保存成功，ID: {user_message.id}")
        except Exception as e:
            logger.error(f"保存用户消息时出错: {str(e)}", exc_info=True)
        
        # 处理消息
        try:
            logger.info(f"开始调用process_message处理消息...")
            result = await self.process_message(
                query=query,
                session_id=conversation_id,
                chat_history=chat_history,
                user_context=user_context
            )
            logger.info(f"消息处理完成，回答长度: {len(result.get('answer', ''))}")
        except Exception as e:
            logger.error(f"处理消息时出错: {str(e)}", exc_info=True)
            raise
        
        # 保存助手回复
        try:
            logger.info(f"保存助手回复...")
            assistant_message = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=result["answer"]
            )
            db_session.add(assistant_message)
            
            # 如果是新对话，设置标题
            if is_new_conversation:
                logger.info(f"设置新会话标题...")
                # 使用用户第一条消息的前30个字符作为标题
                title = query[:30] + ("..." if len(query) > 30 else "")
                conversation.title = title
                logger.info(f"会话标题设置为: {title}")
            
            db_session.commit()
            logger.info(f"助手回复保存成功，ID: {assistant_message.id}")
        except Exception as e:
            logger.error(f"保存助手回复时出错: {str(e)}", exc_info=True)
        
        # 构建响应
        logger.info(f"处理聊天请求完成")
        return {
            "answer": result["answer"],
            "sources": result.get("sources", []),
            "conversation_id": conversation_id,
            "needs_more_info": result.get("needs_more_info", False),
            "intent_result": result.get("intent_result", {})
        }
    
    async def process_message(
        self, 
        query: str,
        session_id: str = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        使用LangGraph工作流处理用户消息
        
        Args:
            query: 用户查询
            session_id: 会话ID
            chat_history: 聊天历史
            user_context: 用户上下文
            
        Returns:
            包含回答的字典
        """
        logger.info(f"====================== 开始process_message ======================")
        logger.info(f"处理用户消息: {query}")
        logger.info(f"会话ID: {session_id}")
        logger.info(f"聊天历史长度: {len(chat_history) if chat_history else 0}")
        logger.info(f"用户上下文: {user_context}")
        
        try:
            # 使用LangGraph工作流处理消息
            logger.info("使用LangGraph工作流处理消息...")
            
            # 调用工作流
            workflow_result = await process_with_workflow(
                user_input=query,
                chat_history=chat_history,
                user_context=user_context
            )
            
            logger.info(f"工作流处理完成")
            logger.info(f"工作流返回结果: {list(workflow_result.keys())}")
            
            # 提取结果
            answer = workflow_result.get("answer", "")
            intent = workflow_result.get("intent", "UNKNOWN")
            sources = workflow_result.get("sources", [])
            messages = workflow_result.get("messages", [])
            
            logger.info(f"识别的意图: {intent}")
            logger.info(f"回答长度: {len(answer)}")
            logger.info(f"检索到的文档数量: {len(sources)}")
            logger.info(f"消息链长度: {len(messages)}")
            
            # 验证必要的返回值
            if not answer:
                logger.warning("工作流返回的答案为空")
                answer = "抱歉，我无法生成回答。请重新提问。"
            
            # 构建标准化返回格式
            return {
                "query": query,
                "answer": answer,
                "sources": sources,
                "intent_result": {
                    "intent": intent,
                    "workflow_used": True,
                    "message_count": len(messages)
                },
                "needs_more_info": False,
                # 额外的工作流信息
                "workflow_messages": [
                    {"role": "user" if msg.__class__.__name__ == "HumanMessage" else "assistant", 
                     "content": msg.content} 
                    for msg in messages
                ] if hasattr(messages[0] if messages else None, 'content') else []
            }
                
        except Exception as e:
            logger.error(f"工作流处理失败: {str(e)}", exc_info=True)
            
            # 最终错误处理
            return {
                "query": query,
                "answer": "抱歉，在处理您的消息时遇到了技术问题。请稍后再试。",
                "sources": [],
                "intent_result": {
                    "intent": "ERROR",
                    "workflow_used": True,
                    "error": str(e)
                },
                "needs_more_info": False,
                "error": str(e)
            } 

# 创建服务实例的工厂函数
def get_chat_service(llm_service: LLMService = None) -> ChatService:
    """
    获取聊天服务实例
    
    Args:
        llm_service: 大语言模型服务
        
    Returns:
        ChatService实例
    """
    logger.info(f"获取聊天服务实例")
    return ChatService(llm_service=llm_service) 