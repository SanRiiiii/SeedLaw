# app/rag/embedding.py
from typing import List, Dict, Any
import numpy as np
import torch
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from pymilvus import Collection, DataType, FieldSchema, CollectionSchema, utility
from app.core.config import settings
from app.db.vector_store import connect_to_milvus, check_collection_exists


class EmbeddingManager:
    """负责文本向量化和向量存储管理"""

    def __init__(self):
        # 使用BGE中文模型作为嵌入模型
        self.embedding_model = HuggingFaceEmbeddings(
            model_name="BAAI/bge-large-zh",
            model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )

        # 向量维度
        self.embedding_dim = settings.EMBEDDING_DIMENSION

        # 连接到Milvus
        connect_to_milvus()

        # 确保集合存在
        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        """确保Milvus中存在所需的集合"""
        collection_name = settings.MILVUS_COLLECTION

        if not check_collection_exists(collection_name):
            # 定义集合字段
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=100, is_primary=True),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=4000),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.embedding_dim),
                FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=200),
                FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=200),
                FieldSchema(name="article_number", dtype=DataType.VARCHAR, max_length=50),
                FieldSchema(name="law_type", dtype=DataType.VARCHAR, max_length=50),
            ]

            # 创建集合架构
            schema = CollectionSchema(fields=fields, description="法律文档集合")

            # 创建集合
            collection = Collection(name=collection_name, schema=schema)

            # 创建索引
            index_params = {
                "index_type": "HNSW",  # 快速最近邻搜索
                "metric_type": "IP",  # 内积相似度
                "params": {"M": 8, "efConstruction": 64}
            }
            collection.create_index(field_name="embedding", index_params=index_params)

            print(f"创建了新的集合 '{collection_name}'")
        else:
            print(f"集合 '{collection_name}' 已存在")

    def get_embedding(self, text: str) -> List[float]:
        """获取文本的嵌入向量"""
        return self.embedding_model.embed_query(text)

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """批量获取文本的嵌入向量"""
        return self.embedding_model.embed_documents(texts)

    def insert_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """将文档插入到向量数据库"""
        if not documents:
            return False

        collection = Collection(name=settings.MILVUS_COLLECTION)
        collection.load()

        # 提取所有文本用于批量嵌入
        texts = [doc["text"] for doc in documents]
        embeddings = self.get_embeddings(texts)

        # 准备要插入的数据
        ids = [doc["id"] for doc in documents]
        texts = [doc["text"] for doc in documents]
        sources = [doc["metadata"].get("source", "") for doc in documents]
        titles = [doc["metadata"].get("title", "") for doc in documents]
        article_numbers = [doc["metadata"].get("article_number", "") for doc in documents]
        law_types = [doc["metadata"].get("law_type", "") for doc in documents]

        # 插入数据
        try:
            collection.insert([
                ids,
                texts,
                embeddings,
                sources,
                titles,
                article_numbers,
                law_types
            ])
            collection.flush()
            return True
        except Exception as e:
            print(f"插入文档时出错: {e}")
            return False
        finally:
            collection.release()