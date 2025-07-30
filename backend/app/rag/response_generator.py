# app/rag/response_generator.py
import json
import httpx
import asyncio
import logging
import re
import os
import sys
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.models.llm import get_llm_service, LLMService
# 初始化检索器
from app.rag.HybridRetriever import HybridRetriever
        

logger = logging.getLogger(__name__)


class Generator:
    """基于大语言模型的回答生成器"""

    def __init__(self, llm_service: LLMService = None):
        """
        初始化生成器
        
        Args:
            llm_service: 大语言模型服务，如果为None则使用默认服务
        """
        # 使用提供的LLM服务或创建新的
        self.llm_service = llm_service or get_llm_service(
            model=settings.SILICONFLOW_MODEL,
            api_url=settings.SILICONFLOW_API_URL,
            api_key=settings.SILICONFLOW_API_KEY,
            temperature=0.15,
            max_tokens=4000
        )
        self.retriever = HybridRetriever()
       

    async def generate(self,
                       query: str,
                       retrieved_docs: List[Dict[str, Any]] = None,
                       **kwargs) -> Dict[str, Any]:
        """
        根据检索到的文档生成回答

        Args:
            query: 用户问题
            retrieved_docs: 检索到的文档列表
            chat_history: 聊天历史记录，格式为[{"role": "user", "content": "..."},
                                          {"role": "assistant", "content": "..."}]
            **kwargs: 其他生成参数，如temperature, max_tokens等

        Returns:
            Dict: 包含生成的回答和引用的来源
        """

        # 构建提示
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(query, retrieved_docs)

        messages = [{"role": "system", "content": system_prompt}]

        messages.append({"role": "user", "content": user_prompt})

        try:
            response_data = await self.llm_service.chat_completion(messages, **kwargs)
            
            if "error" in response_data:
                logger.error(f"生成回答时发生错误: {response_data['error']}")
                return {
                    "answer": "抱歉，在生成回答时遇到了问题。请稍后再试。",
                    "sources": [],
                    "error": response_data["error"]
                }
            
            answer = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")

            return {
                "answer": answer,
                "retrieved_docs": [
                    {
                        "document_name": doc.get('document_name', ''),
                        "chapter": doc.get('chapter', ''),
                        "section": doc.get('section', ''),
                        "content": doc.get('content', ''),
                        "effective_status": doc.get('effective_status', ''),
                        "effective_date": doc.get('effective_date', '')
                    } for doc in retrieved_docs
                ]
            }

        except Exception as e:
            logger.exception(f"生成回答时发生错误: {str(e)}")
            return {
                "answer": "抱歉，在生成回答时遇到了技术问题。请稍后再试。",
                "sources": [],
                "raw_response": None,
                "retrieved_docs": [],
                "error": str(e)
            }

    def _build_system_prompt(self) -> str:
        """构建系统提示"""
        return """
## 背景 ##
你是一个专业的法律顾问，专注于为中国科技创业者提供准确的法律信息和建议。
## 任务 ##
你将收到一个用户的问题，以及检索到的相关法律依据。你需要根据用户的问题和检索到的法律依据，给出具体的法律建议。

## 要求 ##
1. 如果收到的法律依据为空，请返回，抱歉我没有找到相关的法律依据，请您咨询专业律师。
2.基于提供的法律信息给出具体、实用的建议，不要偏离给出的法律依据！！
3. 清晰标明引用的法律依据，使用[n]格式引用相关法条或规定，如[1]、[2]等。
4. 如果提供的信息不足以完全回答问题，请诚实说明并提供基于已知信息的最佳建议。
5. 建议用户在处理重要法律事务时咨询专业律师。

## 注意 ##
在回答中，必须遵循以下格式：
1. 用plain text格式回答,不要使用markdown格式,不要使用markdown格式,不要使用markdown格式
2. 在回答相关部分引用具体法条[n]
3. 在回答最后，添加"【法律依据】"部分，完整列出所有引用的法律条文，格式如：
   【法律依据】
   [1] 《中华人民共和国公司法》第二条：有限责任公司是指...
   [2] 《中华人民共和国民法典》第六十条：...
4. 如果有实用的建议或风险提示，请在法律依据之前给出
请确保你引用的每个法条编号[n]都准确对应提供给你的法律依据列表中的编号。不要自行编造法条内容，只能引用我提供给你的法律依据。"""

    def _build_user_prompt(self, query: str, retrieved_docs: List[Dict[str, Any]]) -> str:
        """构建用户提示，包含查询和检索到的文档"""
        prompt = f"我的问题是：{query}\n\n"
        prompt += "以下是相关的法律依据：\n\n"

        for i, doc in enumerate(retrieved_docs, 1):
            # 构建来源信息
            source_parts = []
            if doc.get('document_name'):
                source_parts.append(doc.get('document_name'))
                
            if doc.get('chapter'):
                source_parts.append(doc.get('chapter'))
    
                
            if doc.get('section'):
                source_parts.append(doc.get('section'))
        
            
            is_effective = doc.get('is_effective', True)
            effective_status = "（现行有效）" if is_effective else "（已失效）"
            
            source = " - ".join(source_parts) if source_parts else "未知来源"
            source += effective_status

            prompt += f"[{i}] {source}:\n"
            prompt += f"{doc.get('text', '') or doc.get('content', '')}\n\n"

        prompt += "请根据以上法律依据回答我的问题，必须在回答中准确引用相关的法条编号[n]，并在回答最后列出所有引用的法条原文。"
        return prompt

    # def _extract_sources_from_answer(self, answer: str, retrieved_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    #     """从回答中提取引用的法律依据"""
    #     # 提取所有引用标记 [n]
    #     citation_pattern = r'\[(\d+)\]'
    #     citations = set(re.findall(citation_pattern, answer))

    #     # 收集引用的文档
    #     sources = []
    #     for citation in citations:
    #         try:
    #             idx = int(citation) - 1
    #             if 0 <= idx < len(retrieved_docs):
    #                 source = {
    #                     "document_name": retrieved_docs[idx].get('document_name', ''),
    #                     "chapter": retrieved_docs[idx].get('chapter', ''),
    #                     "section": retrieved_docs[idx].get('section', ''),
    #                     "content": retrieved_docs[idx].get('content', ''),
    #                     "effective_status": retrieved_docs[idx].get('effective_status', ''),
    #                     "effective_date": retrieved_docs[idx].get('effective_date', ''),
    #                 }
    #                 sources.append(source)
    #         except (ValueError, IndexError):
    #             logger.warning(f"无效的引用编号: {citation}")

    #     return sources




# if __name__ == "__main__":
#     generator = CachedDeepseekGenerator()
#     query = "什么是有限责任公司？"
#     retrieved_docs = []
#     try:
#             retrieved_docs = generator.retriever.retrieve(query)
#             logger.info(f"检索到 {len(retrieved_docs)} 条相关文档")
#     except Exception as e:
#             logger.error(f"检索文档时发生错误: {str(e)}")
#             retrieved_docs = []
#     result = asyncio.run(generator.generate(query, retrieved_docs))
#     print(result)
