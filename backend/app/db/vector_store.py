from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
from app.core.config import settings
import logging

class VectorStore:
    def __init__(self):
        self.collection = None
     
    def connect_to_milvus(self):
        """连接到Milvus向量数据库"""
        try:
            connections.connect(
                alias="default",
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT
            )
            self.logger.info("Milvus连接成功")
            return True
        except Exception as e:
            self.logger.error(f"Milvus连接失败: {e}")
            return False

    def check_collection_exists(self,collection_name):
        """检查集合是否存在"""
        return utility.has_collection(collection_name)

    def get_collection(self,collection_name):
        """获取文档集合"""
        if not self.check_collection_exists(collection_name):
            return None
        self.collection = Collection(collection_name)
        return self.collection
    
    def create_collection(self,fields,collection_name,description):
        """
        创建集合
        需要外部传输fields和collection_name和description
        
        """
        if self.check_collection_exists(collection_name):
            self.logger.info(f"集合 {self.collection_name} 已存在")
            return self.get_collection()
        
        # 创建集合模式
        schema = CollectionSchema(fields, description)
        
        # 创建集合
        self.collection = Collection(collection_name, schema=schema)
        
        # 创建索引
        index_params = {
            "metric_type": "COSINE",  # 余弦相似度
            "index_type": "HNSW",     # 高效的近似最近邻搜索
            "params": {
                "M": 16,              # HNSW图中每个节点的最大边数
                "efConstruction": 200 # 构建时的搜索宽度
            }
        }
        self.collection.create_index(field_name="embedding", index_params=index_params)
        
        self.logger.info(f"已成功创建集合 {self.collection_name} 并设置索引")
        return self.collection
    
    def insert_vectors(self, entities):
        """插入向量数据"""
        if not self.collection:
            self.get_collection() or self.create_collection()
        
        try:
            insert_result = self.collection.insert(entities)
            self.collection.flush()
            self.logger.info(f"成功插入 {len(entities)} 条数据")
            return insert_result
        except Exception as e:
            self.logger.error(f"插入数据失败: {e}")
            return None
    
    def search_vectors(self, query_embedding, limit=10, output_fields=None):
        """搜索向量"""
        if not self.collection:
            self.get_collection()
            
        if not self.collection:
            self.logger.error(f"集合 {self.collection_name} 不存在")
            return []
        
        # 加载集合
        self.collection.load()
        
        # 设置默认输出字段
        if output_fields is None:
            output_fields = ["id", "content", "document_name", "chapter", "section"]
        
        # 搜索参数
        search_params = {
            "metric_type": "COSINE",
            "params": {"ef": 100}  # 搜索时的候选集大小
        }
        
        try:
            results = self.collection.search(
                data=[query_embedding], 
                anns_field="embedding", 
                param=search_params,
                limit=limit,
                output_fields=output_fields
            )
            
            # 处理结果
            search_results = []
            for hits in results:
                for hit in hits:
                    result = {
                        'uuid': hit.id,
                        'score': hit.score,
                    }
                    # 添加其他字段
                    for field in output_fields:
                        if field != "id":  # id已经作为uuid添加
                            result[field] = hit.entity.get(field)
                    
                    search_results.append(result)
            
            return search_results
        except Exception as e:
            self.logger.error(f"搜索失败: {e}")
            return []
    
    def delete_vectors(self, ids):
        """删除向量"""
        if not self.collection:
            self.get_collection()
            
        if not self.collection:
            self.logger.error(f"集合 {self.collection_name} 不存在")
            return False
        
        try:
            expr = f"id in {ids}"
            self.collection.delete(expr)
            self.logger.info(f"成功删除 ID 为 {ids} 的向量")
            return True
        except Exception as e:
            self.logger.error(f"删除向量失败: {e}")
            return False
    
    def drop_collection(self):
        """删除集合"""
        if self.check_collection_exists():
            utility.drop_collection(self.collection_name)
            self.logger.info(f"已删除集合 {self.collection_name}")
            self.collection = None
            return True
        return False
    
    def get_collection_stats(self):
        """获取集合统计信息"""
        if not self.collection:
            self.get_collection()
            
        if not self.collection:
            return {"error": f"集合 {self.collection_name} 不存在"}
        
        try:
            stats = {
                "name": self.collection_name,
                "num_entities": self.collection.num_entities,
                "index_status": "已建立" if self.collection.has_index() else "未建立"
            }
            return stats
        except Exception as e:
            self.logger.error(f"获取集合统计信息失败: {e}")
            return {"error": str(e)}