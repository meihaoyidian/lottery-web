"""
昨日战绩模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Date, DECIMAL, JSON, ForeignKey, func
from app.database import Base


class DailyAchievement(Base):
    """昨日战绩表"""
    __tablename__ = "daily_achievements"

    id = Column(Integer, primary_key=True, index=True, comment="战绩ID")
    date = Column(Date, nullable=False, unique=True, index=True, comment="战绩对应日期")
    title = Column(String(100), nullable=False, comment="标题，如'昨日5中4'")
    subtitle = Column(String(200), nullable=True, comment="副标题，如'足球3中3，篮球2中1'")
    total_count = Column(Integer, nullable=False, server_default="0", comment="总场次")
    win_count = Column(Integer, nullable=False, server_default="0", comment="命中场次")
    accuracy_rate = Column(DECIMAL(5, 2), nullable=False, server_default="0.00", comment="准确率（百分比）")
    highlights = Column(JSON, nullable=True, comment="亮点数据，如[{\"text\": \"连红3场\", \"icon\": \"🔥\"}]")
    description = Column(String(2000), nullable=True, comment="详细描述，最多2000字")
    banner_image = Column(String(500), nullable=True, comment="banner图片URL（可选）")
    is_active = Column(Boolean, nullable=False, server_default="1", comment="是否显示")
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建者ID")
    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间"
    )

    def __repr__(self):
        return f"<DailyAchievement(id={self.id}, date={self.date}, title={self.title}, accuracy_rate={self.accuracy_rate}%)>"
