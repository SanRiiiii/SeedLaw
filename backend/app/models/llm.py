import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import httpx
import logging
import asyncio
from typing import Dict, Any, Optional, List, Union
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """
    大语言模型服务类，负责处理与LLM的交互
    支持不同的模型提供商和接口
    """
    
    def __init__(
        self,
        model: str = None,
        api_url: str = None,
        api_key: str = None,
        timeout: float = None,
        **kwargs
    ):
        """
        初始化LLM服务
        
        Args:
            model: 模型名称，如果为None则使用配置中的默认模型
            api_url: API端点URL，如果为None则使用配置中的默认URL
            api_key: API密钥，如果为None则使用配置中的默认密钥
            timeout: 请求超时时间（秒）
            **kwargs: 其他参数，如temperature, max_tokens等
        """
        self.model = model or settings.SILICONFLOW_MODEL
        self.api_url = api_url or settings.SILICONFLOW_API_URL
        self.api_key = api_key or settings.SILICONFLOW_API_KEY
        self.timeout = timeout
        
        # 默认生成参数
        self.default_params = {
            "top_p": 0.8,
            "temperature": 0.15,
            "max_tokens": 4096
        }
        self.default_params.update(kwargs)
        
        logger.info(f"LLM服务初始化完成，使用模型: {self.model}")
    
    async def generate(
        self, 
        prompt: str, 
        system_prompt: str = None,
        **kwargs
    ) -> str:
        """
        生成文本响应
        
        Args:
            prompt: 用户输入的提示词
            system_prompt: 系统提示词，用于设置模型行为
            chat_history: 聊天历史记录
            **kwargs: 其他参数，如temperature, max_tokens等
            
        Returns:
            模型生成的文本响应
        """
        print(f'开始生成文本响应，使用模型: {self.model}')
        # 构建消息
        messages = []
        
        # 添加系统提示
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 添加当前用户提示
        messages.append({"role": "user", "content": prompt})
        
        # 调用模型
        return await self._call_model(messages, **kwargs)
    
    async def _call_model(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        调用模型API
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            模型响应文本
        """
        # 合并默认参数和自定义参数
        params = self.default_params.copy()
        params.update(kwargs)
        
        # 构建请求头
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 构建请求体
        request_data = {
            "model": self.model,
            "messages": messages,
            **params
        }
        
        try:
            # 发送请求
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=request_data
                )
                
                # 检查响应状态
                if response.status_code != 200:
                    logger.error(f"API请求失败: {response.status_code}, {response.text}")
                    return f"API请求失败: {response.status_code}"
                
                # 解析响应 - 只针对火山引擎格式
                response_data = response.json()
                return response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
        except Exception as e:
            logger.exception(f"调用模型API时发生错误: {str(e)}")
            return f"调用模型API时发生错误: {str(e)}"
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        直接调用聊天完成API，返回完整响应
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            完整的API响应
        """
        # 合并默认参数和自定义参数
        params = self.default_params.copy()
        params.update(kwargs)
        
        # 构建请求头
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 构建请求体
        request_data = {
            "model": self.model,
            "messages": messages,
            **params
        }
        
        try:
            # 发送请求
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=request_data
                )
                
                # 检查响应状态
                if response.status_code != 200:
                    logger.error(f"API请求失败: {response.status_code}, {response.text}")
                    return {"error": f"API请求失败: {response.status_code}"}
                
                # 返回完整响应
                return response.json()
                
        except Exception as e:
            logger.exception(f"调用模型API时发生错误: {str(e)}")
            return {"error": str(e)}


def get_llm_service(
    model: str = None,
    api_url: str = None,
    api_key: str = None,
    **kwargs
) -> LLMService:
    """
    获取LLM服务实例
    
    Args:
        model: 模型名称
        api_url: API端点URL
        api_key: API密钥
        **kwargs: 其他参数
        
    Returns:
        LLMService实例
    """
    return LLMService(
        model=model,
        api_url=api_url,
        api_key=api_key,
        **kwargs
    ) 

# if __name__ == "__main__":
#     llm = LLMService()
#     answer = asyncio.run(llm.generate("你好"))
#     print(answer)
