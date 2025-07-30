'''
elasticSearch 关键词搜索器 版本为ES8.x
最后的search接口langchain的结构进行集成，作为检索器的一部分

支持能力：
创建索引: def create_index() -> bool
批量索引文档: def build_index(self, documents: List[Dict[str, Any]], id_field: str = "uuid") -> bool
更新索引: def update_index(self, documents: List[Dict[str, Any]], id_field: str = "uuid") -> bool
获取索引信息: def get_index_info() -> Dict[str, Any]
搜索: def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]
 result = {
                    "uuid": doc.get("uuid", ""),
                    "content": content,
                    "document_name": doc.get("document_name", ""),
                    "chapter": doc.get("chapter", ""),
                    "section": doc.get("section", ""),
                    "effective_date": doc.get("effective_date", ""),
                    "is_effective": doc.get("is_effective", False),
                }


'''
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from typing import List, Dict, Any, Optional
import logging
import time
import jieba
from elasticsearch import Elasticsearch, helpers
from app.core.config import Settings

logger = logging.getLogger(__name__)
settings = Settings()

class ESSearcher:
    """Elasticsearch搜索器，替代BM25搜索实现"""

    def __init__(self):
        self.es_hosts = settings.ES_HOSTS
        self.es_index = settings.ES_INDEX
        self.es_username = settings.ES_USERNAME
        self.es_password = settings.ES_PASSWORD
        self.use_ssl = settings.ES_USE_SSL
        self.client = None
        self.last_updated = None
        self.tokenizer = jieba.Tokenizer()  # 保留中文分词能力
        
        # 连接ES
        self._connect()
    
    def _connect(self) -> bool:
        """连接到Elasticsearch服务器"""
        try:
            # 创建ES客户端 - 适用于ES 8.x
            connection_params = {
                'request_timeout': 30
            }
            
            # 添加认证信息(如果有)
            if self.es_username:
                connection_params['basic_auth'] = (self.es_username, self.es_password)
            
            # 添加SSL信息(如果启用)
            if self.use_ssl:
                connection_params['verify_certs'] = True
            
            # 创建客户端
            self.client = Elasticsearch(self.es_hosts, **connection_params)
            
            # 检查连接是否成功
            if self.client.ping():
                logger.info("成功连接到Elasticsearch")
                return True
            else:
                logger.error("无法连接到Elasticsearch")
                return False
        except Exception as e:
            logger.error(f"连接Elasticsearch时发生错误: {e}")
            return False
    
    def tokenize_zh(self, text: str) -> List[str]:
        """中文分词函数"""
        if not text or not isinstance(text, str):
            return ["placeholder"]
        tokens = list(jieba.cut(text))
        return tokens if tokens else ["placeholder"]
    
    def create_index(self) -> bool:
        """创建索引，如果不存在"""
        if not self.client:
            logger.error("未连接到Elasticsearch，无法创建索引")
            return False
        
        try:
            index_exists = False
            try:
                index_exists = self.client.indices.exists(index=self.es_index)
            except Exception as e:
                logger.error(f"检查索引是否存在失败: {e}")
                # 尝试继续创建索引
            
            if index_exists:
                logger.info(f"索引 {self.es_index} 已存在")
                return True
            
            # 定义索引映射 - 使用标准分词器(不重要，因为我们会预处理文本)
            mappings = {
                "properties": {
                    "uuid": {"type": "keyword"},
                    "content": {
                        "type": "text",
                        "analyzer": "standard"  # 这里不重要，因为内容已经被jieba预处理
                    },
                    "document_name": {"type": "keyword"},
                    "chapter": {"type": "keyword"},
                    "section": {"type": "keyword"},
                    "effective_date": {"type": "date", "format": "yyyy-MM-dd||yyyy-MM-dd'T'HH:mm:ss||epoch_millis", "ignore_malformed": True},
                    "is_effective": {"type": "boolean"},
                    "original_content": {"type": "text", "index": False}  # 存储原始内容但不索引
                }
            }
            
            settings = {
                "number_of_shards": 1,
                "number_of_replicas": 0
            }
            
            self.client.indices.create(
                index=self.es_index,
                mappings=mappings,
                settings=settings
            )
            
            logger.info(f"成功创建索引 {self.es_index}")
            return True
        except Exception as e:
            logger.error(f"创建Elasticsearch索引失败: {e}")
            return False
    
    def build_index(self, documents: List[Dict[str, Any]], id_field: str = "uuid") -> bool:
        """批量索引文档"""
        if not self.client:
            logger.error("未连接到Elasticsearch，无法构建索引")
            return False
        
        if not documents:
            logger.warning("没有提供文档，无法构建索引")
            return False
        
        # 确保索引存在
        if not self.create_index():
            return False
        
        try:
            # 准备批量索引数据
            operations = []
            for doc in documents:
                doc_id = doc.get(id_field)
                if not doc_id:
                    continue
                
                # 复制文档，避免修改原始数据
                processed_doc = doc.copy()
                
                # 保存原始内容
                if "content" in processed_doc and processed_doc["content"]:
                    original_content = processed_doc["content"]
                    processed_doc["original_content"] = original_content
                    
                    # 对content字段应用jieba分词，并将结果以空格连接
                    tokens = self.tokenize_zh(original_content)
                    processed_doc["content"] = " ".join(tokens)  # 直接替换为分词结果
                
                # 添加索引操作
                operations.append({"index": {"_index": self.es_index, "_id": doc_id}})
                operations.append(processed_doc)
            
            # 批量索引
            if operations:
                # 执行批量操作
                response = self.client.bulk(operations=operations)
                
                if response.get("errors", False):
                    logger.error(f"批量索引期间发生错误: {response}")
                    return False
                
                # 刷新索引
                self.client.indices.refresh(index=self.es_index)
                self.last_updated = time.time()
                # 计算操作数量是operations列表长度的一半（每个文档有两个操作）
                doc_count = len(operations) // 2
                logger.info(f"成功索引 {doc_count} 个文档到 Elasticsearch")
                return True
            else:
                logger.warning("没有有效的文档可索引")
                return False
        except Exception as e:
            logger.error(f"构建Elasticsearch索引失败: {e}")
            return False
    
    def update_index(self, documents: List[Dict[str, Any]], id_field: str = "uuid") -> bool:
        """
        更新索引，添加或更新文档
        
        Args:
            documents: 文档列表
            id_field: 文档ID字段名
            
        Returns:
            是否成功更新索引
        """
        # 更新就是重新索引，直接调用build_index
        return self.build_index(documents, id_field)
    
    def get_index_info(self) -> Dict[str, Any]:
        """
        获取索引信息
        
        Returns:
            包含索引信息的字典
        """
        if not self.client:
            return {
                "document_count": 0,
                "is_initialized": False,
                "last_updated": None,
                "index_name": self.es_index,
                "status": "未连接到Elasticsearch"
            }
        
        try:
            # 获取索引统计信息
            stats = self.client.indices.stats(index=self.es_index)
            doc_count = stats["indices"][self.es_index]["total"]["docs"]["count"]
            
            return {
                "document_count": doc_count,
                "is_initialized": True,
                "last_updated": self.last_updated,
                "index_name": self.es_index,
                "status": "已连接"
            }
        except Exception as e:
            logger.error(f"获取Elasticsearch索引信息失败: {e}")
            return {
                "document_count": 0,
                "is_initialized": False,
                "last_updated": self.last_updated,
                "index_name": self.es_index,
                "status": f"错误: {str(e)}"
            }
       

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """执行Elasticsearch搜索"""
        if not self.client:
            self.logger.warning("未连接到Elasticsearch，无法执行搜索")
            return []
        
        try:
            tokens = self.tokenize_zh(query)
            processed_query = " ".join(tokens)

            query_body = {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "content": {  # 在预处理的内容字段中搜索
                                    "query": processed_query,
                                    "operator": "or"
                                }
                            }
                        }
                    ],
                    "filter": [
                        {
                            "term": {
                                "is_effective": True
                            }
                        }
                    ]
                }
            }
            
            response = self.client.search(
                index=self.es_index,
                query=query_body,
                size=top_k
            )
            
            results = []
            for hit in response["hits"]["hits"]:
                doc = hit["_source"]
                content = doc.get("original_content") or doc.get("content", "")
                result = {
                    "uuid": doc.get("uuid", ""),
                    "content": content,
                    "document_name": doc.get("document_name", ""),
                    "chapter": doc.get("chapter", ""),
                    "section": doc.get("section", ""),
                    "effective_date": doc.get("effective_date", ""),
                    "is_effective": doc.get("is_effective", False),
                }
                results.append(result)
            
            return results
        except Exception as e:
            self.logger.error(f"Elasticsearch搜索失败: {e}")
            return [] 
            

# if __name__ == "__main__" :
#     searcher = ESSearcher()
#     print(searcher.search("公司注册需要资料"))
