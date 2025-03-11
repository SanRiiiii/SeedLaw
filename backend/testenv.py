# test_config.py
from app.core.config import settings
import os

def test_config_loading():
    print(f"当前工作目录: {os.getcwd()}")
    print(f".env 文件位置: {os.path.join(os.getcwd(), '.env')}")
    print("\n配置加载测试:")
    print(f"项目名称: {settings.PROJECT_NAME}")
    print(f"MySQL 配置: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}")
    print(f"Milvus 配置: {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
    print(f"嵌入模型路径: {settings.EMBEDDING_MODEL_PATH}")
    print(f"构建的数据库URL: {settings.DATABASE_URL}")

if __name__ == "__main__":
    test_config_loading()