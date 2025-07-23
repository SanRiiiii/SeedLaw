import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from app.rag.dense_search import DenseSearch
from app.rag.sparse_search import SparseSearch
from app.rag.reranker import Reranker
from typing import List, Dict, Any, Optional

class HybridRetriever:
    def __init__(self,use_dense=True,use_sparse=True,use_rerank=True):
    
        self.use_dense = use_dense
        self.use_sparse = use_sparse
        self.use_rerank = use_rerank
        self.dense_searcher = DenseSearch()
        self.sparse_searcher = SparseSearch()
        self.reranker = Reranker()
        self.RRF_alpha = 0.7
        self.RRF_top_k = 20
        self.dense_top_k = 20
        self.sparse_top_k = 20


    def RRF(self, dense_results: List[Dict[str, Any]], sparse_results: List[Dict[str, Any]],
                        alpha: float = 0.7,top_k: int = 20, k: int = 60) -> List[Dict[str, Any]]:
        """
        使用Reciprocal Rank Fusion (RRF)算法重新排序结果，合并向量搜索和关键词搜索结果
        
        Args:
            vector_results: 向量检索结果列表
            keyword_results: 关键词检索结果列表
            alpha: 向量检索权重系数，取值范围[0,1]，越大越偏向向量检索结果
                  alpha=1.0时只考虑向量检索结果，alpha=0.0时只考虑关键词检索结果
            k: RRF算法中的常数，用于降低排名差异的影响，一般取值为60
            
        Returns:
            重排序后的结果列表
        """
        # 创建结果字典，键为文档ID
        all_docs = {}

        # 添加向量搜索结果和关键词搜索结果的原始信息
        # 先处理向量搜索结果
        for rank, doc in enumerate(dense_results):
            doc_id = doc["uuid"]
            if doc_id not in all_docs:
                all_docs[doc_id] = {
                    "doc": doc,
                    "vector_rank": rank + 1,  # 排名从1开始
                    "keyword_rank": float('inf'),  # 初始化为无穷大，表示未被关键词搜索检索到

                }
        
        # 处理关键词搜索结果
        for rank, doc in enumerate(sparse_results):
            doc_id = doc["uuid"]
            if doc_id in all_docs:
                # 已经在向量结果中存在
                all_docs[doc_id]["keyword_rank"] = rank + 1
            else:
                # 只在关键词结果中存在
                all_docs[doc_id] = {
                    "doc": doc,
                    "vector_rank": float('inf'),  # 未被向量搜索检索到
                    "keyword_rank": rank + 1,

                }

        # 计算考虑alpha权重的RRF分数
        # RRF(d) = α·(1/(r_vector(d) + k)) + (1-α)·(1/(r_keyword(d) + k))
        for doc_id, info in all_docs.items():
            vector_contribution = 1.0 / (info["vector_rank"] + k)
            keyword_contribution = 1.0 / (info["keyword_rank"] + k)
            
            # 使用alpha权重调整两种搜索方式的贡献
            rrf_score = alpha * vector_contribution + (1.0 - alpha) * keyword_contribution
            info["rrf_score"] = rrf_score
            
            # 记录组合方式
            info["alpha"] = alpha
            info["vector_contribution"] = vector_contribution
            info["keyword_contribution"] = keyword_contribution

        # 根据RRF分数排序
        sorted_results = sorted(all_docs.values(), key=lambda x: x["rrf_score"], reverse=True)

        # 格式化结果
        final_results = []
        for item in sorted_results:
            result = item["doc"].copy()
            result["score"] = item["rrf_score"]  # 总分使用RRF分数
            
            result["vector_rank"] = item["vector_rank"] if item["vector_rank"] != float('inf') else None
            result["keyword_rank"] = item["keyword_rank"] if item["keyword_rank"] != float('inf') else None
            result["alpha"] = item["alpha"]  # 记录使用的alpha值
            result["vector_contribution"] = item["vector_contribution"]  # 向量检索贡献
            result["keyword_contribution"] = item["keyword_contribution"]  # 关键词检索贡献
            final_results.append(result)

        return final_results[:top_k]




    def hybridRetrieve(self,query:str,top_k:int):
        if not self.use_dense:
            return self.sparse_searcher.search(query,top_k)
        if not self.use_sparse:
            return self.dense_searcher.search(query,top_k)
        if not self.use_rerank:
            return self.RRF(self.dense_searcher.search(query,self.dense_top_k),self.sparse_searcher.search(query,self.sparse_top_k),self.RRF_alpha,top_k)
        else:
            return self.reranker.rerank(query,self.RRF(self.dense_searcher.search(query,self.dense_top_k),self.sparse_searcher.search(query,self.sparse_top_k),self.RRF_alpha,self.RRF_top_k),top_k)

    

if __name__ == "__main__":
    hybrid_retriever = HybridRetriever(use_dense=True,use_sparse=True,use_rerank=True)
    results = hybrid_retriever.hybridRetrieve(query="我想注册一个公司，应该怎么做？",top_k=10)
    print(results.join("\n"))
