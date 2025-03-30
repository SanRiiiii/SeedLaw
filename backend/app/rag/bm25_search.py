# app/rag/bm25_search.py
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
import jieba
import logging
import pickle
import os
import time
from app.core.config import Settings
logger = logging.getLogger(__name__)

settings = Settings()

class BM25Searcher:
    """BM25关键词搜索器，支持中文搜索"""
    

    def __init__(self):       

        self.cache_dir = settings.BM25_CACHE_DIR
        self.cache_file = os.path.join(self.cache_dir, 'bm25_index.pkl')
        self.bm25_model = None
        self.tokenizer = jieba.Tokenizer()
        self.corpus = []
        self.id_mapping = {}  # 用于将BM25索引映射回原始文档ID
        self.last_updated = None  # 上次更新时间
    
    def tokenize_zh(self, text: str) -> List[str]:
        """中文分词函数"""
        if not text or not isinstance(text, str):
            return ["placeholder"]  # 返回占位符，避免空列表导致问题
        tokens = list(jieba.cut(text))
        return tokens if tokens else ["placeholder"]  # 确保即使分词结果为空也返回一个token

    def build_index(self, documents: List[Dict[str, Any]], text_field: str = "content", id_field: str = "uuid") -> bool:
        """
        从文档列表构建BM25索引
        
        Args:
            documents: 文档列表
            text_field: 文档内容字段名
            id_field: 文档ID字段名
            
        Returns:
            是否成功构建索引
        """
        if not documents:
            logger.warning("没有提供文档，无法构建BM25索引")
            return False
            
        try:
            # 重置索引
            self.corpus = []
            self.id_mapping = {}
            
            # 对所有文档进行分词
            for i, doc in enumerate(documents):
                doc_id = doc.get(id_field, f"doc_{i}")
                content = doc.get(text_field, "")
                
                # 分词并添加到语料库
                tokens = self.tokenize_zh(content)
                self.corpus.append(tokens)
                
                # 记录映射关系，保存完整文档以便后续查询
                self.id_mapping[i] = doc
            
            # 创建BM25模型
            if self.corpus:
                self.bm25_model = BM25Okapi(self.corpus)
                self.last_updated = time.time()
                logger.info(f"成功构建BM25索引，共索引了 {len(self.corpus)} 个文档")
                self._save_index()
                return True
            else:
                logger.warning("BM25语料库为空，无法创建索引")
                return False
                
        except Exception as e:
            logger.error(f"构建BM25索引失败: {e}")
            return False

    def _save_index(self)->bool:
        """保存BM25索引到文件"""
        try:
            data = {
                "corpus": self.corpus,
                "id_mapping": self.id_mapping,
                "bm25_model": self.bm25_model,
                "last_updated": self.last_updated
            }
            with open(self.cache_file, 'wb') as f:
                pickle.dump(data, f)
            logger.info(f"BM25索引已保存到 {self.cache_file}")
            return True
        except Exception as e:
            logger.error(f"保存BM25索引失败: {e}")
            return False
    
    def load_index(self)->bool:
        """加载BM25索引
        
        Returns:
            是否成功加载索引
        """
        if not os.path.exists(self.cache_file):
            logger.warning(f"缓存文件 {self.cache_file} 不存在")
            return False
        
        try:
            with open(self.cache_file, 'rb') as f:
                data = pickle.load(f)
                self.corpus = data["corpus"]
                self.id_mapping = data["id_mapping"]
                self.bm25_model = data["bm25_model"]
                self.last_updated = data.get("last_updated", time.time())
                logger.info(f"成功加载BM25索引，共索引了 {len(self.corpus)} 个文档")
                return True
        except Exception as e:
            logger.error(f"加载BM25索引失败: {e}")
            return False
    
    def update_index(self, documents: List[Dict[str, Any]], text_field: str = "content", id_field: str = "uuid") -> bool:
        """
        更新BM25索引，添加新文档而不重建整个索引
        
        Args:
            documents: 新增文档列表
            text_field: 文档内容字段名
            id_field: 文档ID字段名
            
        Returns:
            是否成功更新索引
        """
        if not documents:
            logger.warning("没有提供更新文档")
            return False
            
        # 如果模型未初始化，则进行完整构建
        if not self.bm25_model:
            return self.build_index(documents, text_field, id_field)
            
        try:
            # 记录原始索引大小
            original_size = len(self.corpus)
            
            # 处理新文档
            for doc in documents:
                doc_id = doc.get(id_field, f"doc_{len(self.corpus)}")
                content = doc.get(text_field, "")
                
                # 分词并添加到语料库
                tokens = self.tokenize_zh(content)
                self.corpus.append(tokens)
                
                # 记录映射关系
                self.id_mapping[len(self.corpus) - 1] = doc
            
            # 重新初始化BM25模型
            self.bm25_model = BM25Okapi(self.corpus)
            self.last_updated = time.time()
            
            # 保存更新后的索引
            self._save_index()
            
            logger.info(f"成功更新BM25索引，新增了 {len(self.corpus) - original_size} 个文档，当前共 {len(self.corpus)} 个文档")
            return True
            
        except Exception as e:
            logger.error(f"更新BM25索引失败: {e}")
            return False
    
    def get_index_info(self) -> Dict[str, Any]:
        """
        获取索引信息
        
        Returns:
            包含索引信息的字典
        """
        return {
            "document_count": len(self.corpus),
            "is_initialized": self.bm25_model is not None,
            "last_updated": self.last_updated,
            "cache_file": self.cache_file
        }
                
    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        执行BM25搜索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表，每个结果包含原始文档信息和BM25分数
        """
        if not self.bm25_model or not self.corpus:
            logger.warning("BM25模型未初始化，无法执行搜索")
            return []
            
        try:
            # 对查询进行分词
            tokenized_query = self.tokenize_zh(query)
            if not tokenized_query:
                logger.warning("查询分词结果为空")
                return []
                
            # 获取BM25分数
            scores = self.bm25_model.get_scores(tokenized_query)
            
            # 将分数与文档关联并排序
            scored_docs = [(i, score) for i, score in enumerate(scores)]
            scored_docs.sort(key=lambda x: x[1], reverse=True)
            
            # 取top_k结果
            results = []
            for doc_idx, score in scored_docs[:top_k]:
                if doc_idx in self.id_mapping:
                    doc = self.id_mapping[doc_idx].copy()
                    doc["score"] = float(score)  # 确保分数是浮点数
                    results.append(doc)
            
            return results
            
        except Exception as e:
            logger.error(f"BM25搜索失败: {e}")
            return [] 