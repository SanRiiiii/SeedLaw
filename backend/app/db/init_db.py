# app/db/init_db.py
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine
from app.core.config import settings

def init_db():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)
