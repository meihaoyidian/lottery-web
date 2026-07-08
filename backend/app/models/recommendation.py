"""
推荐模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class RecommendationStatus(str, enum.Enum):
    """推荐状态枚举（仅用于类型提示）"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    COMPLETED = "completed"


class Recommendation(Base):
    """推荐表"""
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True, comment="推荐ID")
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, comment="创建管理员ID")
    prediction_type = Column(String(20), nullable=False, index=True, comment="预测类型")
    title = Column(String(50), nullable=False, comment="推荐标题")
    promotion_title = Column(String(100), nullable=True, comment="推广标题（选填，用于分享和推广展示）")
    prediction_data = Column(JSON, nullable=False, comment="预测数据（预测类型特定）")
    analysis_text = Column(Text, nullable=False, comment="分析说明（支持富文本）")
    status = Column(String(20), nullable=False, server_default="active", index=True, comment="推荐状态")
    is_confirmed = Column(Boolean, nullable=False, server_default="0", comment="管理员是否已确认")
    actual_outcome = Column(JSON, nullable=True, comment="实际结果（用于历史记录）")
    archived_at = Column(DateTime, nullable=True, index=True, comment="归档时间（90天后归档）")
    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="UTC时间戳"
    )
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间"
    )

    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])

    def __repr__(self):
        return f"<Recommendation(id={self.id}, prediction_type={self.prediction_type}, status={self.status})>"
