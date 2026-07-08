"""
用户模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, func, JSON
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    """用户角色枚举"""
    user = "user"
    admin = "admin"


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, comment="用户ID")
    phone = Column(String(20), unique=True, nullable=False, index=True, comment="手机号（支持国际号码）")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    nickname = Column(String(50), nullable=True, comment="昵称")
    openid = Column(String(100), unique=True, nullable=True, index=True, comment="微信OpenID")
    is_paid = Column(Boolean, nullable=False, server_default="0", comment="是否为付费用户")
    paid_start_time = Column(DateTime, nullable=True, comment="付费开始时间")
    paid_end_time = Column(DateTime, nullable=True, comment="付费结束时间")
    is_trial_user = Column(Boolean, nullable=False, server_default="0", comment="是否为体验用户")
    has_used_trial = Column(Boolean, nullable=False, server_default="0", comment="是否已使用过体验（永久标记，防重复薅）")
    trial_start_time = Column(DateTime, nullable=True, comment="体验开始时间")
    trial_end_time = Column(DateTime, nullable=True, comment="体验结束时间")
    is_key_match_member = Column(Boolean, nullable=False, server_default="0", comment="是否为重心场次付费用户（只能看重心场次）")
    key_match_recommendation_ids = Column(JSON, nullable=True, comment="绑定的重心场次推荐ID数组")
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
        return f"<User(id={self.id}, phone={self.phone}, role={self.role}, is_paid={self.is_paid}, is_trial_user={self.is_trial_user}, is_key_match_member={self.is_key_match_member})>"


class TrialUsage(Base):
    """体验会员使用记录表（永久保留，不随用户删除而清除）"""
    __tablename__ = "trial_usage"

    id = Column(Integer, primary_key=True, index=True)
    openid = Column(String(100), unique=True, nullable=False, index=True, comment="已使用过体验的微信OpenID")
    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        comment="记录创建时间"
    )
