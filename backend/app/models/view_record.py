"""
浏览记录模型
"""
from sqlalchemy import Column, Integer, ForeignKey, DateTime, func, Index
from sqlalchemy.orm import relationship
from app.database import Base


class ViewRecord(Base):
    """推荐浏览记录表"""
    __tablename__ = "view_records"

    id = Column(Integer, primary_key=True, index=True, comment="记录ID")
    user_id = Column(
        Integer,
        nullable=True,
        index=True,
        comment="浏览用户ID（游客为NULL，逻辑引用 user_web.id）"
    )
    recommendation_id = Column(
        Integer,
        ForeignKey("recommendations.id", ondelete="CASCADE"),
        nullable=False,
        comment="推荐ID"
    )
    viewed_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="浏览时间（UTC）"
    )

    # Relationships（user 逻辑关联 user_web，无 DB 级外键约束）
    user = relationship(
        "User",
        primaryjoin="ViewRecord.user_id == User.id",
        foreign_keys=[user_id],
        viewonly=True,
    )
    recommendation = relationship("Recommendation", foreign_keys=[recommendation_id])

    # 复合索引：按推荐ID查询浏览记录时提高性能
    __table_args__ = (
        Index('idx_recommendation_viewed', 'recommendation_id', 'viewed_at'),
        Index('idx_user_recommendation', 'user_id', 'recommendation_id'),
    )

    def __repr__(self):
        return f"<ViewRecord(id={self.id}, user_id={self.user_id}, recommendation_id={self.recommendation_id})>"
