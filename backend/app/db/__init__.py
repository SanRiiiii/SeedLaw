from sqlalchemy.orm import Session

from app.db.models import Base
from app.db.session import engine
import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def __init__():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)

