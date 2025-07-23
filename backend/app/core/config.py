# app/core/config.py
from pydantic_settings import BaseSettings
from typing import List, Optional
from dotenv import load_dotenv
import os
# 确定项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
# 加载 .env 文件
load_dotenv(os.path.join(BASE_DIR, ".env"))
class Settings(BaseSettings):
    PROJECT_NAME: str = "法律知识助手"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str

    # 数据库配置
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_HOST: str
    MYSQL_PORT: str
    MYSQL_DB: str
    DATABASE_URL: Optional[str] = None

    # Milvus配置
    MILVUS_HOST: str
    MILVUS_PORT: str
    MILVUS_COLLECTION: str = "legal_documents"

    # Redis配置
    REDIS_HOST: str
    REDIS_PORT: str

    # 火山引擎API
    VOLCENGINE_API_KEY: str
    VOLCENGINE_API_URL: str
    VOLCENGINE_MODEL: str

    SILICONFLOW_API_KEY: str
    SILICONFLOW_API_URL: str
    SILICONFLOW_MODEL: str
    
    # 意图识别模型
    INTENT_MODEL: Optional[str] = None

    # CORS设置
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # 向量嵌入模型设置
    EMBEDDING_DIMENSION: int 
    EMBEDDING_MODEL_PATH: str
    RERANKER_MODEL_PATH: str
    
    # 重排序配置
    USE_RERANKER: bool = True  # 是否默认使用重排序器
    RERANKER_CANDIDATES: int = 10  # 重排序候选数量

    # BM25配置
    BM25_CACHE_DIR: str 

    # 上下文长度
    CONTEXT_LENGTH: int

    # 缓存设置
    CACHE_EXPIRATION: int = 3600  # 秒

    # Elasticsearch配置
    ES_HOSTS: List[str] = ["http://localhost:9200"]
    ES_INDEX: str = "legal_documents"
    ES_USERNAME: Optional[str] = None
    ES_PASSWORD: Optional[str] = None
    ES_USE_SSL: bool = False

    # 搜索引擎选择
    SEARCH_ENGINE: str = "elasticsearch"  # 可选值: "bm25", "elasticsearch"

    class Config:
        env_file = "../../.env"
        case_sensitive = True


settings = Settings()

# 动态构建数据库URL
if not settings.DATABASE_URL:
    settings.DATABASE_URL = f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}"
