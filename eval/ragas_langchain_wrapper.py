import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

import asyncio
from typing import List, Optional, Dict, Any, Mapping
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
from backend.app.models.llm import LLMService
from backend.app.core.config import settings
from ragas.llms import LangchainLLMWrapper
from pydantic import Field


class LangchainLLMAdapter(LLM):
    """
    将项目的LLMService适配为Langchain LLM接口
    """
    
    # 定义字段
    model_name: str = Field(default="")
    api_url: str = Field(default="")
    api_key: str = Field(default="")
    llm_service: Any = Field(default=None)
    
    def __init__(
        self,
        model: str = None,
        api_url: str = None,
        api_key: str = None,
        **kwargs
    ):
        # 先初始化字段值
        model_name = model or settings.SILICONFLOW_MODEL
        api_url_val = api_url or settings.SILICONFLOW_API_URL
        api_key_val = api_key or settings.SILICONFLOW_API_KEY
        
        # 创建LLM服务
        llm_service = LLMService(
            model=model_name,
            api_url=api_url_val,
            api_key=api_key_val,
            **kwargs
        )
        
        # 调用父类初始化
        super().__init__(
            model_name=model_name,
            api_url=api_url_val,
            api_key=api_key_val,
            llm_service=llm_service,
            **kwargs
        )
    
    @property
    def _llm_type(self) -> str:
        return "custom_llm_service"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """同步调用接口"""
        return asyncio.run(self._acall(prompt, stop, run_manager, **kwargs))
    
    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """异步调用接口"""
        try:
            response = await self.llm_service.generate(prompt, **kwargs)
            return response
        except Exception as e:
            print(f"LLM调用失败: {e}")
            return ""
    
    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """识别参数"""
        return {
            "model": self.model_name,
            "api_url": self.api_url,
        }





def get_langchain_llm_for_ragas(**kwargs) -> LangchainLLMWrapper:
    """
    获取用于Ragas的Langchain LLM包装器
    """
    langchain_llm = LangchainLLMAdapter(**kwargs)
    return LangchainLLMWrapper(langchain_llm)


# 测试示例
if __name__ == "__main__":
    # 测试LLM适配器
    llm_adapter = LangchainLLMAdapter()
    response = llm_adapter._call("什么是法律？")
    print(f"LLM适配器响应: {response}")
    
    # 测试Ragas包装器
    ragas_llm = get_langchain_llm_for_ragas()
    print("Ragas LLM包装器创建成功") 