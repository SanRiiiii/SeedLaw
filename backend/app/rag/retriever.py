# app/rag/retriever.py

from typing import List, Dict, Any, Tuple
import numpy as np
from pymilvus import Collection, DataType
import logging
import os
from app.core.config import settings
from app.db.vector_store import VectorStore
from app.rag.embedding import BGEEmbedding
from app.rag.bm25_search import BM25Searcher

# 配置日志
logger = logging.getLogger(__name__)

class HybridRetriever:
    """混合检索器，结合向量检索和关键词检索"""

    def __init__(self, use_bm25: bool = True):
        self.embedding = BGEEmbedding()
        self.vector_store = VectorStore()
        # 确保连接到Milvus
        self.vector_store.connect_to_milvus()
        # 获取集合
        self.collection_name = settings.MILVUS_COLLECTION
        self.collection = self.vector_store.get_collection(self.collection_name)
        self.collection.load()
        
        # BM25相关初始化
        self.use_bm25 = use_bm25
        self.bm25_searcher = None
        if use_bm25:
            self._initialize_bm25()
        
    def _initialize_bm25(self):
        """初始化BM25搜索器"""
        try:
            # 首先创建BM25搜索器
            self.bm25_searcher = BM25Searcher()
            
            # 尝试加载已有索引
            if self.bm25_searcher.load_index():
                logger.info("从缓存成功加载BM25索引")
                logger.info(f"索引信息: {self.bm25_searcher.get_index_info()}")
                return
            
            # 如果找不到缓存的索引文件，直接记录日志并返回
            logger.warning("未找到BM25索引缓存文件，请先运行索引构建脚本")
            self.use_bm25 = False
            return
                
        except Exception as e:
            logger.error(f"初始化BM25搜索器失败: {str(e)}")
            self.use_bm25 = False

    def _vector_search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """基于向量相似度的搜索"""
        # 获取查询的嵌入向量
        query_embedding = self.embedding.encode(query)
        
        # 确保向量格式正确，milvus要求向量格式为浮点数列表
        # 修改了encode函数后，现在返回的是一维numpy数组
        # 需要转换为浮点数列表以适配Milvus
        if isinstance(query_embedding, np.ndarray):
            query_embedding = query_embedding.astype(np.float32).tolist()
        
        # 定义输出字段
        output_fields = ["uuid", "content", "document_name", "chapter", "section", "effective_date", "is_effective"]
        
        # 使用vector_store的search_vectors方法进行向量搜索
        search_results = self.vector_store.search_vectors(
            collection_name=self.collection_name,
            query_embedding=query_embedding,
            limit=top_k,
            output_fields=output_fields
        )

        # 将search_results格式转换为vector_results格式
        vector_results = []
        for hit in search_results:
            result = {
                "id": hit.get('uuid', ''),
                "text": hit.get('content', ''),
                "source": hit.get('document_name', ''),
                "title": hit.get('chapter', ''),
                "article_number": hit.get('section', ''),
                "score": hit.get('score', 0.0)
            }
            vector_results.append(result)

        return vector_results

    def retrieve(self, query: str, top_k: int = 5, alpha: float = 0.7, use_bm25: bool = True) -> List[Dict[str, Any]]:
        """
        执行检索，支持纯向量检索或向量+BM25混合检索
        
        Args:
            query: 用户查询
            top_k: 返回的结果数量
            alpha: 向量搜索与关键词搜索的权重系数，越大越偏向向量搜索
            use_bm25: 是否使用BM25混合检索，为False时只使用向量检索
            
        Returns:
            检索结果列表
        """
        # 如果不使用BM25或BM25初始化失败，直接使用向量搜索
        if not use_bm25 or not self.use_bm25 or not self.bm25_searcher:
            return self._vector_search(query, top_k=top_k)
        
        # 进行向量搜索
        vector_results = self._vector_search(query, top_k=top_k * 2)
        if not vector_results:
            return []
        
        # 直接使用BM25进行搜索
        bm25_results = self.bm25_searcher.search(query, top_k=top_k * 2)
        if not bm25_results:
            return vector_results[:top_k]
            
        # 转换BM25结果格式以匹配向量结果
        formatted_bm25_results = []
        for doc in bm25_results:
            result = {
                "id": doc.get('uuid', ''),
                "text": doc.get('content', ''),
                "source": doc.get('document_name', ''),
                "title": doc.get('chapter', ''),
                "article_number": doc.get('section', ''),
                "score": doc.get('score', 0.0)
            }
            formatted_bm25_results.append(result)
        
        # 重排序结果
        reranked_results = self._rerank_results(vector_results, formatted_bm25_results, alpha=0.8)
        return reranked_results[:top_k]

    def _rerank_results(self, vector_results: List[Dict[str, Any]], keyword_results: List[Dict[str, Any]],
                        alpha: float = 0.7, k: int = 60) -> List[Dict[str, Any]]:
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
        for rank, doc in enumerate(vector_results):
            doc_id = doc["id"]
            if doc_id not in all_docs:
                all_docs[doc_id] = {
                    "doc": doc,
                    "vector_rank": rank + 1,  # 排名从1开始
                    "keyword_rank": float('inf'),  # 初始化为无穷大，表示未被关键词搜索检索到
                    "vector_score": doc["score"],
                    "keyword_score": 0.0
                }
        
        # 处理关键词搜索结果
        for rank, doc in enumerate(keyword_results):
            doc_id = doc["id"]
            if doc_id in all_docs:
                # 已经在向量结果中存在
                all_docs[doc_id]["keyword_rank"] = rank + 1
                all_docs[doc_id]["keyword_score"] = doc["score"]
            else:
                # 只在关键词结果中存在
                all_docs[doc_id] = {
                    "doc": doc,
                    "vector_rank": float('inf'),  # 未被向量搜索检索到
                    "keyword_rank": rank + 1,
                    "vector_score": 0.0,
                    "keyword_score": doc["score"]
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
            result["vector_score"] = item["vector_score"]  # 保留原始向量分数
            result["keyword_score"] = item["keyword_score"]  # 保留原始关键词分数
            result["vector_rank"] = item["vector_rank"] if item["vector_rank"] != float('inf') else None
            result["keyword_rank"] = item["keyword_rank"] if item["keyword_rank"] != float('inf') else None
            result["alpha"] = item["alpha"]  # 记录使用的alpha值
            result["vector_contribution"] = item["vector_contribution"]  # 向量检索贡献
            result["keyword_contribution"] = item["keyword_contribution"]  # 关键词检索贡献
            final_results.append(result)

        return final_results

    def close(self):
        """释放资源"""
        if hasattr(self, 'collection') and self.collection:
            self.collection.release()

    def print_collection_info(self):
        """打印集合信息，用于调试"""
        try:
            # 获取集合统计信息
            logger.info(f"\n集合统计信息:")
            logger.info(f"实体数量: {self.collection.num_entities}")
            
            # 获取集合索引信息
            index_infos = self.collection.index()
            logger.info(f"\n索引信息:")
            logger.info(f"索引参数: {index_infos}")
                
            # 获取集合字段信息
            schema_fields = self.collection.schema.fields
            logger.info(f"\n字段信息:")
            for field in schema_fields:
                logger.info(f"字段名称: {field.name}")
                logger.info(f"字段类型: {field.dtype}")
                if hasattr(field, 'is_primary'):
                    logger.info(f"是主键: {field.is_primary}")
                if hasattr(field, 'params') and field.params and 'dim' in field.params:
                    logger.info(f"维度: {field.params['dim']}")
                logger.info("-" * 30)
            
            # 打印BM25索引信息
            if self.use_bm25 and self.bm25_searcher:
                logger.info("\nBM25索引信息:")
                bm25_info = self.bm25_searcher.get_index_info()
                for key, value in bm25_info.items():
                    logger.info(f"{key}: {value}")
                
            return True
        except Exception as e:
            logger.error(f"获取集合信息失败: {str(e)}")
            return False


# 使用示例
if __name__ == "__main__":
    # 配置控制台日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建检索器，默认启用BM25
    retriever = HybridRetriever(use_bm25=True)
    try:
        # 打印集合信息
        logger.info("===== 集合信息 =====")
        retriever.print_collection_info()
        
        logger.info("\n===== 执行检索（向量+BM25重排序） =====")
        results = retriever.retrieve("公司注册需要哪些材料", top_k=5, use_bm25=True)
        for i, result in enumerate(results, 1):
            logger.info(f"结果 {i}:")
            logger.info(f"文档: {result['title']} {result['article_number']}")
            logger.info(f"内容: {result['text'][:100]}...")
            logger.info(
                f"综合得分: {result['score']:.4f} (向量: {result['vector_score']:.4f}, 关键词: {result['keyword_score']:.4f})")
            logger.info("-" * 50)
            
        logger.info("\n===== 执行检索（仅向量） =====")
        results = retriever.retrieve("公司注册需要哪些材料", top_k=5, use_bm25=False)
        for i, result in enumerate(results, 1):
            logger.info(f"结果 {i}:")
            logger.info(f"文档: {result['title']} {result['article_number']}")
            logger.info(f"内容: {result['text'][:100]}...")
            logger.info(f"向量得分: {result['score']:.4f}")
            logger.info("-" * 50)
    finally:
        retriever.close()