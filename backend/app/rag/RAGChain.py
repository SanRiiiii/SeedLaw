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

logger = logging.getLogger(__name__)

class RAGChain:
    def __init__(self,use_dense:bool=True,use_sparse:bool=True,use_rerank:bool=True,llm_service:LLMService=None):
        self.use_dense = use_dense
        self.use_sparse = use_sparse
        self.use_rerank = use_rerank
        self.llm_service = llm_service
        self.hyde_generator = HyDEGenerator(llm_service=self.llm_service)
        self.retriever = HybridRetriever(use_dense=use_dense,use_sparse=use_sparse,use_rerank=use_rerank)
        self.generator = Generator(llm_service=self.llm_service)

    async def rag_chain(self,query:str,rewrite_query:bool=False,top_k:int=10):
        if rewrite_query:
            query = self.hyde_generator.generate_document(query)
        retrieved_docs = self.retriever.hybridRetrieve(query,top_k)
        response = await self.generator.generate(query,retrieved_docs)
        return response
      

if __name__ == "__main__":
    rag_chain = RAGChain(use_hyde=True,use_reranker=True)
    response = asyncio.run(rag_chain.rag_chain(query="我想注册一个公司，应该怎么做？",top_k=10))
    print(response)



