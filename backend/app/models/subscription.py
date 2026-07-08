"""
订阅消息模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, JSON, Text, func
from app.database import Base
import enum


class MessageStatus(str, enum.Enum):
    """消息发送状态枚举"""
    pending = "pending"
    sent = "sent"
    failed = "failed"


class RecommendationSubscription(Base):
    """推荐订阅消息表"""
    __tablename__ = "recommendation_subscriptions"

    id = Column(Integer, primary_key=True, index=True, comment="订阅ID")
    user_id = Column(Integer, nullable=False, index=True, comment="用户ID")
    openid = Column(String(100), nullable=False, index=True, comment="微信OpenID")
    template_id = Column(String(100), nullable=False, comment="模板ID")
    is_active = Column(Boolean, nullable=False, server_default="1", comment="是否启用")
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
        return f"<RecommendationSubscription(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"


class SubscriptionMessage(Base):
    """订阅消息发送记录表"""
    __tablename__ = "subscription_messages"

    id = Column(Integer, primary_key=True, index=True, comment="消息ID")
    subscription_id = Column(Integer, nullable=False, index=True, comment="订阅ID")
    recommendation_id = Column(Integer, nullable=False, index=True, comment="推荐ID")
    openid = Column(String(100), nullable=False, comment="接收者OpenID")
    template_id = Column(String(100), nullable=False, comment="模板ID")
    page = Column(String(200), nullable=True, comment="跳转页面路径")
    data = Column(JSON, nullable=False, comment="消息内容")
    status = Column(
        Enum(MessageStatus),
        nullable=False,
        server_default="pending",
        index=True,
        comment="发送状态"
    )
    error_msg = Column(Text, nullable=True, comment="错误信息")
    sent_at = Column(DateTime, nullable=True, comment="发送时间")
    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="创建时间"
    )

    def __repr__(self):
        return f"<SubscriptionMessage(id={self.id}, recommendation_id={self.recommendation_id}, status={self.status})>"
