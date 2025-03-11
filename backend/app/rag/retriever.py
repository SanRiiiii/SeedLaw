# app/rag/retriever.py
from typing import List, Dict, Any, Tuple
import numpy as np
from pymilvus import Collection
from rank_bm25 import BM25Okapi
import jieba
from app.core.config import settings
from app.db.vector_store import connect_to_milvus, get_collection
from app.rag.embedding import EmbeddingManager


class HybridRetriever:
    """混合检索器，结合向量检索和关键词检索"""

    def __init__(self):
        self.embedding_manager = EmbeddingManager()

        # 确保连接到Milvus
        connect_to_milvus()

        # 获取集合
        self.collection = Collection(name=settings.MILVUS_COLLECTION)
        self.collection.load()

    def _vector_search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """基于向量相似度的搜索"""
        # 获取查询的嵌入向量
        query_embedding = self.embedding_manager.get_embedding(query)

        # 执行向量搜索
        search_params = {"metric_type": "IP", "params": {"ef": 64}}
        results = self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["id", "text", "source", "title", "article_number", "law_type"]
        )

        # 处理结果
        vector_results = []
        for hits in results:
            for hit in hits:
                vector_results.append({
                    "id": hit.entity.get("id"),
                    "text": hit.entity.get("text"),
                    "source": hit.entity.get("source"),
                    "title": hit.entity.get("title"),
                    "article_number": hit.entity.get("article_number"),
                    "law_type": hit.entity.get("law_type"),
                    "score": hit.score
                })

        return vector_results

    def _keyword_search(self, query: str, documents: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
        """使用BM25关键词搜索"""

        # 中文分词
        def tokenize_zh(text):
            return list(jieba.cut(text))

        # 对所有文档进行分词
        tokenized_corpus = [tokenize_zh(doc["text"]) for doc in documents]

        # 创建BM25模型
        bm25 = BM25Okapi(tokenized_corpus)

        # 对查询进行分词
        tokenized_query = tokenize_zh(query)

        # 计算BM25分数
        scores = bm25.get_scores(tokenized_query)

        # 将分数与文档关联并排序
        scored_docs = [(doc, score) for doc, score in zip(documents, scores)]
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        # 取top_k结果
        keyword_results = []
        for doc, score in scored_docs[:top_k]:
            result = doc.copy()
            result["score"] = score
            keyword_results.append(result)

        return keyword_results

    def _rerank_results(self, vector_results: List[Dict[str, Any]], keyword_results: List[Dict[str, Any]],
                        alpha: float = 0.7) -> List[Dict[str, Any]]:
        """重新排序结果，合并向量搜索和关键词搜索结果"""
        # 创建结果字典，键为文档ID
        all_docs = {}

        # 添加向量搜索结果
        for doc in vector_results:
            doc_id = doc["id"]
            all_docs[doc_id] = {
                "doc": doc,
                "vector_score": doc["score"],
                "keyword_score": 0.0
            }

        # 添加关键词搜索结果
        for doc in keyword_results:
            doc_id = doc["id"]
            if doc_id in all_docs:
                all_docs[doc_id]["keyword_score"] = doc["score"]
            else:
                all_docs[doc_id] = {
                    "doc": doc,
                    "vector_score": 0.0,
                    "keyword_score": doc["score"]
                }

        # 标准化分数
        if vector_results:
            max_vector_score = max(doc["vector_score"] for doc in all_docs.values())
            min_vector_score = min(doc["vector_score"] for doc in all_docs.values())
            vector_range = max_vector_score - min_vector_score
        else:
            vector_range = 1.0
            min_vector_score = 0.0

        if keyword_results:
            max_keyword_score = max(doc["keyword_score"] for doc in all_docs.values())
            min_keyword_score = min(doc["keyword_score"] for doc in all_docs.values())
            keyword_range = max_keyword_score - min_keyword_score
        else:
            keyword_range = 1.0
            min_keyword_score = 0.0

        # 计算组合分数
        for doc_id, scores in all_docs.items():
            if vector_range > 0:
                norm_vector_score = (scores["vector_score"] - min_vector_score) / vector_range
            else:
                norm_vector_score = 0

            if keyword_range > 0:
                norm_keyword_score = (scores["keyword_score"] - min_keyword_score) / keyword_range
            else:
                norm_keyword_score = 0

            combined_score = alpha * norm_vector_score + (1 - alpha) * norm_keyword_score
            scores["combined_score"] = combined_score

        # 根据组合分数排序
        sorted_results = sorted(all_docs.values(), key=lambda x: x["combined_score"], reverse=True)

        # 格式化结果
        final_results = []
        for item in sorted_results:
            result = item["doc"].copy()
            result["score"] = item["combined_score"]
            result["vector_score"] = item["vector_score"]
            result["keyword_score"] = item["keyword_score"]
            final_results.append(result)

        return final_results

    def retrieve(self, query: str, top_k: int = 5, alpha: float = 0.7) -> List[Dict[str, Any]]:
        """执行混合检索，结合向量搜索和关键词搜索"""
        # 向量搜索，获取更多候选项以供后续重排序
        vector_results = self._vector_search(query, top_k=top_k * 2)

        # 对向量结果进行关键词重排序
        if vector_results:
            keyword_results = self._keyword_search(query, vector_results, top_k=top_k * 2)

            # 重排序结果
            reranked_results = self._rerank_results(vector_results, keyword_results, alpha=alpha)

            # 返回top_k个结果
            return reranked_results[:top_k]
        else:
            return []

    def close(self):
        """释放资源"""
        if hasattr(self, 'collection') and self.collection:
            self.collection.release()


# 使用示例
if __name__ == "__main__":
    retriever = HybridRetriever()
    try:
        results = retriever.retrieve("公司注册需要哪些材料", top_k=5)
        for i, result in enumerate(results, 1):
            print(f"结果 {i}:")
            print(f"文档: {result['title']} {result['article_number']}")
            print(f"内容: {result['text'][:100]}...")
            print(
                f"综合得分: {result['score']:.4f} (向量: {result['vector_score']:.4f}, 关键词: {result['keyword_score']:.4f})")
            print("-" * 50)
    finally:
        retriever.close()