"""
用户模型（Web 端）
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, func
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    """用户角色枚举"""
    user = "user"
    admin = "admin"


class User(Base):
    """Web 端用户表（独立于小程序 users 表）"""
    __tablename__ = "user_web"

    id = Column(Integer, primary_key=True, index=True, comment="用户ID")
    phone = Column(String(20), unique=True, nullable=False, index=True, comment="手机号（支持国际号码）")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    nickname = Column(String(50), nullable=True, comment="昵称")
    is_paid = Column(Boolean, nullable=False, server_default="0", comment="是否为付费用户")
    paid_start_time = Column(DateTime, nullable=True, comment="付费开始时间")
    paid_end_time = Column(DateTime, nullable=True, comment="付费结束时间")
    token_version = Column(Integer, nullable=False, server_default="0", comment="Token版本号，用于单设备登录控制")
    role = Column(Enum(UserRole), nullable=False, server_default="user", comment="用户角色")
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
        return f"<User(id={self.id}, phone={self.phone}, role={self.role}, is_paid={self.is_paid})>"
