'''
向量检索器，用于检索向量库中的文档

'''
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from typing import List, Dict, Any
import numpy as np
from app.db.milvus import VectorStore
from app.models.Embeddings.bge_embedding import BGEEmbedding  
from app.core.config import Settings
settings = Settings()


class DenseSearch:
    def __init__(self):
        self.embedding = BGEEmbedding()
        self.vector_store = VectorStore()
        self.collection_name = settings.MILVUS_COLLECTION

        

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """基于向量相似度的搜索"""
        # 获取查询的嵌入向量
        query_embedding = self.embedding.encode(query)
        
        # 确保向量格式正确，milvus要求向量格式为浮点数列表
        # 修改了encode函数后，现在返回的是一维numpy数组
        # 需要转换为浮点数列表以适配Milvus

        if isinstance(query_embedding, np.ndarray):
            query_embedding = query_embedding.astype(np.float32).tolist()
        
        output_fields = ["uuid", "content", "document_name", "chapter", "section", "effective_date", "is_effective"]
        vector_results = self.vector_store.search_vectors(
            collection_name=self.collection_name,
            query_embedding=query_embedding,
            limit=top_k,
            output_fields=output_fields,
            expr="is_effective == True"  # 添加过滤条件，只返回有效的文档
        )

        return vector_results

# if __name__ == "__main__":
#     dense_search = DenseSearch()
#     vector_results = dense_search.search(collection_name=settings.MILVUS_COLLECTION, query="我想注册一个公司，应该怎么做？")
#     print(vector_results)