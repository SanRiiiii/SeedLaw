# Redis缓存连接配置
# app/cache/redis_client.py
import redis
from app.core.config import settings

# 创建Redis连接池
redis_pool = redis.ConnectionPool(
    host=settings.REDIS_HOST,
    port=int(settings.REDIS_PORT),
    db=0,
    decode_responses=True  # 自动将响应解码为字符串
)

def get_redis_client():
    """获取Redis客户端连接"""
    return redis.Redis(connection_pool=redis_pool)

