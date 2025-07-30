'''
rag的基本模块
检索器+生成器
'''
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from typing import List, Dict, Any, Optional, Callable
import logging
import asyncio
from app.rag.HybridRetriever import HybridRetriever
from app.rag.response_generator import Generator
from app.core.config import settings
from app.models.llm import get_llm_service, LLMService
from app.rag.hyde import HyDEGenerator
from app.rag.reflection import reflection_llm

logger = logging.getLogger(__name__)

class RAGChain:
    def __init__(self,use_dense:bool=True,use_sparse:bool=True,use_rerank:bool=True,llm_service:LLMService=None,use_hyde:bool=True):
        self.use_dense = use_dense
        self.use_sparse = use_sparse
        self.use_rerank = use_rerank
        self.llm_service = llm_service
        self.use_hyde = use_hyde 
        self.retriever = HybridRetriever(use_dense=use_dense,use_sparse=use_sparse,use_rerank=use_rerank)
        self.generator = Generator(llm_service=self.llm_service)

    async def rag_chain(self,query:str,top_k:int=10):
        if self.use_hyde:
            query = self.hyde_generator.generate_document(query)
        retrieved_docs = self.retriever.hybridRetrieve(query,top_k)
        reflection_response = await reflection_llm(query,retrieved_docs)
        response = await self.generator.generate(query,reflection_response)
        return response
      

# if __name__ == "__main__":
#     rag_chain = RAGChain()
#     response = asyncio.run(rag_chain.rag_chain(query="注册公司需要什么材料？",top_k=10))
#     print(response)



