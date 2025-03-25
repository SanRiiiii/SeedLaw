# app/db/init_db.py
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine
from app.core.config import settings
import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def init_db():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)

