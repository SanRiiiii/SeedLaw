# app/rag/response_generator.py
import json
import httpx
import asyncio
import logging
import re
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class DeepseekGenerator:
    """基于火山引擎Deepseek-v3的回答生成器"""

    def __init__(self):
        self.api_key = settings.VOLCENGINE_API_KEY
        self.api_url = settings.VOLCENGINE_API_URL
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        # 默认参数设置
        self.default_params = {
            "top_p": 0.8,
            "temperature": 0.15,
            "max_tokens": 1500
        }

    async def generate(self,
                       query: str,
                       retrieved_docs: List[Dict[str, Any]],
                       chat_history: Optional[List[Dict[str, str]]] = None,
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

        # 构建消息历史
        messages = [{"role": "system", "content": system_prompt}]

        # 添加历史对话（如果有）
        if chat_history:
            # 限制历史消息数量，避免超出上下文窗口
            for msg in chat_history[-5:]:  # 只保留最近5轮对话
                messages.append(msg)

        # 添加当前问题
        messages.append({"role": "user", "content": user_prompt})

        # 合并默认参数和自定义参数
        params = self.default_params.copy()
        params.update(kwargs)

        # 构建请求
        request_data = {
            "model": "deepseek-v3",  # 使用火山引擎的Deepseek-v3模型
            "messages": messages,
            **params
        }

        try:
            # 发送请求到火山引擎API
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    json=request_data
                )

                if response.status_code != 200:
                    logger.error(f"API请求失败: {response.status_code}, {response.text}")
                    return {
                        "answer": "抱歉，在生成回答时遇到了问题。请稍后再试。",
                        "sources": [],
                        "error": f"API错误: {response.status_code}"
                    }

                response_data = response.json()

                # 解析回答
                answer = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")

                # 提取引用的法律依据
                sources = self._extract_sources_from_answer(answer, retrieved_docs)

                return {
                    "answer": answer,
                    "sources": sources,
                    "raw_response": response_data
                }

        except Exception as e:
            logger.exception(f"生成回答时发生错误: {str(e)}")
            return {
                "answer": "抱歉，在生成回答时遇到了技术问题。请稍后再试。",
                "sources": [],
                "error": str(e)
            }

    def _build_system_prompt(self) -> str:
        """构建系统提示"""
        return """你是一个专业的法律顾问，专注于为中国科技创业者提供准确的法律信息和建议。
你的回答需要：
1. 使用简明易懂的语言解释复杂的法律概念，避免过多专业术语。
2. 基于提供的法律信息给出具体、实用的建议。
3. 清晰标明引用的法律依据，使用[n]格式引用相关法条或规定，如[1]、[2]等。
4. 如果提供的信息不足以完全回答问题，请诚实说明并提供基于已知信息的最佳建议。
5. 解释法律风险并提供可能的解决方案。
6. 避免给出过于绝对的法律判断，而是强调法律适用的可能性。
7. 提醒用户在处理重要法律事务时咨询专业律师。

在回答中，请遵循以下格式：
1. 简短总结你对问题的理解
2. 根据法律依据详细解答问题
3. 在回答相关部分引用具体法条[n]
4. 如果有实用的建议或风险提示，请在最后给出

记住，你是一个帮助科技创业者理解法律、规避风险的顾问，你的目标是提供既准确又实用的法律指导。"""

    def _build_user_prompt(self, query: str, retrieved_docs: List[Dict[str, Any]]) -> str:
        """构建用户提示，包含查询和检索到的文档"""
        prompt = f"我的问题是：{query}\n\n"
        prompt += "以下是相关的法律依据：\n\n"

        for i, doc in enumerate(retrieved_docs, 1):
            source = f"{doc.get('title', '未知来源')}"
            if doc.get('article_number'):
                source += f" {doc.get('article_number')}"

            prompt += f"[{i}] {source}:\n"
            prompt += f"{doc.get('text', '')}\n\n"

        prompt += "请根据以上法律依据回答我的问题，并在回答中引用相关的法条编号[n]。"
        return prompt

    def _extract_sources_from_answer(self, answer: str, retrieved_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从回答中提取引用的法律依据"""
        # 提取所有引用标记 [n]
        citation_pattern = r'\[(\d+)\]'
        citations = set(re.findall(citation_pattern, answer))

        # 收集引用的文档
        sources = []
        for citation in citations:
            try:
                idx = int(citation) - 1
                if 0 <= idx < len(retrieved_docs):
                    source = retrieved_docs[idx].copy()
                    # 删除一些不需要的字段
                    for key in ['score', 'vector_score', 'keyword_score']:
                        if key in source:
                            del source[key]
                    sources.append(source)
            except (ValueError, IndexError):
                logger.warning(f"无效的引用编号: {citation}")

        return sources


# 简单的缓存装饰器，用于减少重复请求
def cached_response(func):
    """缓存装饰器，基于查询和检索文档的哈希值缓存响应"""
    cache = {}

    async def wrapper(self, query, retrieved_docs, *args, **kwargs):
        # 创建缓存键
        cache_key = _create_cache_key(query, retrieved_docs)

        # 如果在缓存中，直接返回
        if cache_key in cache:
            return cache[cache_key]

        # 否则执行函数并缓存结果
        result = await func(self, query, retrieved_docs, *args, **kwargs)
        cache[cache_key] = result

        # 限制缓存大小
        if len(cache) > 100:  # 保留最近的100个响应
            # 删除最早的缓存项
            oldest_key = next(iter(cache))
            del cache[oldest_key]

        return result

    def _create_cache_key(query, docs):
        """创建缓存键"""
        # 从文档中提取ID和分数
        doc_signatures = []
        for doc in docs:
            sig = f"{doc.get('id', '')}_{doc.get('score', 0):.4f}"
            doc_signatures.append(sig)

        # 合并查询和文档签名
        key = f"{query}_{','.join(doc_signatures)}"

        # 使用哈希值减小键的大小
        return hash(key)

    return wrapper


# 增强版的生成器，增加缓存功能
class CachedDeepseekGenerator(DeepseekGenerator):
    """带缓存功能的Deepseek生成器"""

    @cached_response
    async def generate(self, query, retrieved_docs, chat_history=None, **kwargs):
        """带缓存的生成函数"""
        return await super().generate(query, retrieved_docs, chat_history, **kwargs)