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

    # CORS设置
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # 向量嵌入模型设置
    EMBEDDING_DIMENSION: int 
    EMBEDDING_MODEL_PATH: str
    RERANKER_MODEL_PATH: str
    RERANKER_DIMENSION: int 

    # 缓存设置
    CACHE_EXPIRATION: int = 3600  # 秒

    class Config:
        env_file = "../../.env"
        case_sensitive = True


settings = Settings()

# 动态构建数据库URL
if not settings.DATABASE_URL:
    settings.DATABASE_URL = f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}"
