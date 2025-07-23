import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import logging
import asyncio
import time
import traceback
import httpx

from app.core.config import settings
from app.models.llm import get_llm_service, LLMService

logger = logging.getLogger(__name__)

class HyDEGenerator:
    """
    假设性文档嵌入(Hypothetical Document Embeddings)生成器
    将用户查询转换为结构化的"伪文档"，用于提高检索质量
    """
    
    def __init__(self, llm_service: LLMService = None, max_tokens: int = 300):
        """
        初始化HyDE生成器
        
        Args:
            llm_service: 大语言模型服务，如果为None则使用默认服务
            max_tokens: 伪文档的最大token数量，控制生成长度和性能
        """
        # 使用提供的LLM服务或创建新的
        self.llm_service = llm_service or get_llm_service(
            model=settings.SILICONFLOW_MODEL,
            api_url=settings.SILICONFLOW_API_URL,
            api_key=settings.SILICONFLOW_API_KEY,
            temperature=0.1,  # 伪文档生成需要更确定性的输出
            max_tokens=max_tokens
        )
        self.max_tokens = max_tokens
        logger.info(f"HyDE生成器初始化完成，使用模型: {self.llm_service.model}")
    
    async def generate_document(self, enhanced_query: str) -> str:
        """
        根据增强查询生成伪文档
        
        Args:
            enhanced_query: 已经包含历史和上下文的增强查询
            
        Returns:
            生成的伪文档
        """
        start_time = time.time()
        logger.info("开始生成伪文档...")
        
        # 构建提示词，引导模型生成类似法律文档的格式
        prompt = self._build_hyde_prompt(enhanced_query)
        
        # 系统提示
        system_prompt = "你是一位专业的法律文档生成助手，善于将用户查询转化为专业、简洁的法律文档格式。"
        
        try:
            # 使用LLM服务生成伪文档
            hypothetical_doc = await self.llm_service.generate(
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            # 记录性能指标
            elapsed_time = time.time() - start_time
            logger.info(f"伪文档生成成功，长度: {len(hypothetical_doc)} 字符")
            logger.info(f"耗时: {elapsed_time:.2f}秒")
            
            return hypothetical_doc
                
        except Exception as e:
            logger.error(f"生成伪文档时发生未知错误: {type(e).__name__}: {str(e)}")
            return enhanced_query
    
    def _build_hyde_prompt(self, enhanced_query: str) -> str:
        """
        构建用于生成伪文档的提示词
        
        Args:
            enhanced_query: 增强查询
            
        Returns:
            构建好的提示词
        """
        return f"""请生成一份专业、简洁的法律参考文档，回答以下查询中的法律问题：

{enhanced_query}

要求:
1. 使用专业法律术语和规范表述
2. 引用相关法律法规名称和条款编号
3. 结构清晰，重点突出
4. 内容精简，控制在300字以内
5. 不要使用"根据您的问题"等回应式语言，直接以法律文档格式呈现
6. 确保文档完整且自成一体

请生成:"""


# # 使用示例
# if __name__ == "__main__":
#     # 配置详细日志
#     logging.basicConfig(level=logging.DEBUG, 
#                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
#     async def test():
#         # 创建HyDE生成器
#         hyde = HyDEGenerator()
        
#         # 先测试API连接
#         logger.info("\n===== 开始API连接测试 =====")
#         api_ok = await hyde.test_api_connection()
#         if not api_ok:
#             logger.warning("API连接测试失败，请检查API凭证和网络连接")
#             return
            
#         logger.info("\n===== API连接正常，开始测试伪文档生成 =====")
        
#         # 示例查询
#         enhanced_query = """
#         对话历史:
#         用户: 我想注册一家科技公司
#         助手: 注册科技公司需要准备一系列材料，您具体想了解哪方面的信息？
        
#         当前问题:
#         公司注册需要哪些材料？
        
#         用户上下文:
#         公司名称: 示例科技有限公司
#         行业: 软件开发
#         地址: 北京市海淀区
#         融资阶段: 天使轮
#         经营范围: 软件开发、技术咨询
#         """
        
#         # 生成伪文档
#         pseudo_doc = await hyde.generate_document(enhanced_query)
#         logger.info("\n========= 生成的伪文档 =========")
#         logger.info(pseudo_doc)
    
#     # 运行测试
#     asyncio.run(test())