"""
订阅消息相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SubscribeRequest(BaseModel):
    """订阅请求"""
    openid: str = Field(..., description="微信OpenID")
    template_id: Optional[str] = Field(None, description="模板ID（可选）")


class SubscriptionResponse(BaseModel):
    """订阅响应"""
    id: int
    user_id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SubscriptionStatusResponse(BaseModel):
    """订阅状态响应"""
    is_subscribed: bool = Field(..., description="是否已订阅")
