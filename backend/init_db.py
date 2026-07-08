"""
初始化数据库脚本
运行此脚本以创建所有数据表
"""
from app.database import engine, Base
from app.models.user import User
from app.models.recommendation import Recommendation
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db():
    """初始化数据库"""
    try:
        logger.info("开始创建数据表...")

        # 创建所有表
        Base.metadata.create_all(bind=engine)

        logger.info("✓ 数据表创建成功！")
        logger.info(f"已创建的表: {', '.join(Base.metadata.tables.keys())}")

    except Exception as e:
        logger.error(f"✗ 数据表创建失败: {str(e)}")
        raise


if __name__ == "__main__":
    init_db()
