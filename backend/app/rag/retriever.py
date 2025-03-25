# app/rag/retriever.py
import sys
import os
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from typing import List, Dict, Any, Tuple
import numpy as np
from pymilvus import Collection, DataType
from rank_bm25 import BM25Okapi
import jieba
import logging
from app.core.config import settings
from app.db.vector_store import VectorStore
from app.rag.embedding import BGEEmbedding


class HybridRetriever:
    """混合检索器，结合向量检索和关键词检索"""

    def __init__(self):
        self.embedding = BGEEmbedding()
        self.vector_store = VectorStore()
        self.collection_name = settings.MILVUS_COLLECTION
        # 确保连接到Milvus
        self.vector_store.connect_to_milvus()

        # 获取集合
        self.collection = self.vector_store.get_collection(self.collection_name)
        self.collection.load()

    def _vector_search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """基于向量相似度的搜索"""
        # 获取查询的嵌入向量
        query_embedding = self.embedding.encode(query)
        
        # 确保向量格式正确 - 修改了encode函数后，现在返回的是一维numpy数组
        # 需要转换为浮点数列表以适配Milvus
        if isinstance(query_embedding, np.ndarray):
            query_embedding = query_embedding.astype(np.float32).tolist()
        
        # 执行向量搜索
        search_params = {"metric_type": "COSINE", "params": {"ef": 64}}
        results = self.collection.search(
            data=[query_embedding],  # 确保是列表的列表格式
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["uuid", "content", "document_name", "chapter", "section", "effective_date", "is_effective"]
        )

        # 处理结果
        vector_results = []
        for hits in results:
            for hit in hits:
                # 定义一个安全获取字段的函数
                def safe_get_field(entity, field_name):
                    """安全地从实体中获取字段值"""
                    try:
                        # 尝试作为字典访问
                        if hasattr(entity, 'get'):
                            return entity.get(field_name, "")
                        # 尝试作为属性访问
                        elif hasattr(entity, field_name):
                            return getattr(entity, field_name, "")
                        # 尝试作为索引访问
                        elif field_name in entity:
                            return entity[field_name]
                        else:
                            return ""
                    except Exception:
                        return ""
                
                # 使用安全获取字段的方式创建结果
                result = {
                    "id": safe_get_field(hit.entity, "uuid"),
                    "text": safe_get_field(hit.entity, "content"),
                    "source": safe_get_field(hit.entity, "document_name"),
                    "title": safe_get_field(hit.entity, "chapter"),
                    "article_number": safe_get_field(hit.entity, "section"),
                    "law_type": "",  # 如果需要可以添加相应的字段
                    "score": hit.score
                }
                vector_results.append(result)

        return vector_results

    def _keyword_search(self, query: str, documents: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
        """使用BM25关键词搜索"""
        # 检查文档列表是否为空
        if not documents:
            return []

        # 中文分词
        def tokenize_zh(text):
            if not text or not isinstance(text, str):
                return []  # 返回空列表而不是None
            tokens = list(jieba.cut(text))
            return tokens if tokens else ["placeholder"]  # 确保即使分词结果为空也返回一个token

        # 对所有文档进行分词
        tokenized_corpus = []
        for doc in documents:
            if "text" not in doc or not doc["text"]:
                tokenized_corpus.append(["placeholder"])  # 对于空文本添加一个占位符token
            else:
                tokens = tokenize_zh(doc["text"])
                tokenized_corpus.append(tokens)
        
        # 确保语料库不为空
        if not tokenized_corpus or all(not tokens for tokens in tokenized_corpus):
            # 如果所有文档都没有有效的分词结果，直接返回原始文档并设置相同的得分
            return [{**doc, "score": 1.0} for doc in documents[:top_k]]

        # 创建BM25模型
        try:
            bm25 = BM25Okapi(tokenized_corpus)
        except Exception as e:
            print(f"创建BM25模型失败: {e}")
            # 发生错误时返回原始文档并设置相同的得分
            return [{**doc, "score": 1.0} for doc in documents[:top_k]]

        # 对查询进行分词
        tokenized_query = tokenize_zh(query)
        if not tokenized_query:
            # 如果查询分词为空，直接返回原始文档并设置相同的得分
            return [{**doc, "score": 1.0} for doc in documents[:top_k]]

        # 计算BM25分数
        try:
            scores = bm25.get_scores(tokenized_query)
        except Exception as e:
            print(f"计算BM25分数失败: {e}")
            # 发生错误时返回原始文档并设置相同的得分
            return [{**doc, "score": 1.0} for doc in documents[:top_k]]

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
        """执行混合检索，结合向量搜索和关键词检索"""
        # 向量搜索，获取更多候选项以供后续重排序
        vector_results = self._vector_search(query, top_k=top_k * 2)

        # 对向量结果进行关键词重排序
        if vector_results:
            keyword_results = self._keyword_search(query, vector_results, top_k=top_k * 2)
            
            # 如果关键词搜索结果为空，直接使用向量搜索结果
            if not keyword_results:
                return vector_results[:top_k]

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

    def print_collection_info(self):
        """打印集合信息，用于调试"""
        try:
            # 获取集合统计信息
            print(f"\n集合统计信息:")
            print(f"实体数量: {self.collection.num_entities}")
            
            # 获取集合索引信息
            index_infos = self.collection.index()
            print(f"\n索引信息:")
            print(f"索引参数: {index_infos}")
                
            # 获取集合字段信息
            schema_fields = self.collection.schema.fields
            print(f"\n字段信息:")
            for field in schema_fields:
                print(f"字段名称: {field.name}")
                print(f"字段类型: {field.dtype}")
                if hasattr(field, 'is_primary'):
                    print(f"是主键: {field.is_primary}")
                if hasattr(field, 'params') and field.params and 'dim' in field.params:
                    print(f"维度: {field.params['dim']}")
                print("-" * 30)
                
            return True
        except Exception as e:
            print(f"获取集合信息失败: {e}")
            return False


# 使用示例
if __name__ == "__main__":
    retriever = HybridRetriever()
    try:
        # 打印集合信息
        print("===== 集合信息 =====")
        retriever.print_collection_info()
        
        print("\n===== 执行检索 =====")
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