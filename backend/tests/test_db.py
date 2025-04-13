from sqlalchemy import text
import sys
import os
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))) 
from app.db.session import engine
from app.db.models import Base


def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            for row in result:
                print(row)
            print("数据库连接成功!")
    except Exception as e:
        print(f"数据库连接失败: {e}")

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    test_connection()
