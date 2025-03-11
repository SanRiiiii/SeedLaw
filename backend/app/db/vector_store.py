# Milvus向量数据库连接配置
# app/db/vector_store.py
from pymilvus import connections, Collection, utility
from app.core.config import settings

def connect_to_milvus():
    """连接到Milvus向量数据库"""
    try:
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT
        )
        print("Milvus连接成功")
        return True
    except Exception as e:
        print(f"Milvus连接失败: {e}")
        return False

def check_collection_exists(collection_name=settings.MILVUS_COLLECTION):
    """检查集合是否存在"""
    return utility.has_collection(collection_name)

def get_collection(collection_name=settings.MILVUS_COLLECTION):
    """获取文档集合"""
    if not check_collection_exists(collection_name):
        return None
    return Collection(name=collection_name)
