"""
浏览记录相关Schema
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class ViewRecordCreate(BaseModel):
    """创建浏览记录请求"""
    recommendation_id: int


class ViewRecordResponse(BaseModel):
    """浏览记录响应"""
    id: Optional[int] = None
    user_id: Optional[int] = None
    recommendation_id: Optional[int] = None
    viewed_at: Optional[datetime] = None
    # 用户信息
    user_phone: Optional[str] = None
    user_nickname: Optional[str] = None  # 新增：用户昵称
    user_created_at: Optional[datetime] = None  # 新增：用户注册时间
    user_role: Optional[str] = None
    user_is_paid: Optional[bool] = None
    user_is_trial: Optional[bool] = None
    user_is_key_match_member: Optional[bool] = None
    # 新增：浏览统计字段
    view_count: Optional[int] = None  # 该用户的浏览次数
    last_viewed_at: Optional[datetime] = None  # 最后浏览时间
    first_viewed_at: Optional[datetime] = None  # 首次浏览时间

    model_config = ConfigDict(from_attributes=True)


class ViewRecordListResponse(BaseModel):
    """浏览记录列表响应"""
    records: list[ViewRecordResponse]
    total: int  # 总浏览次数（含游客）
    unique_viewers: int  # 登录用户浏览人数
    guest_view_count: int = 0  # 游客浏览次数
