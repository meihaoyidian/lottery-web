"""
用户相关的 Pydantic Schema
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from app.models.user import UserRole
import re


class UserRegister(BaseModel):
    """用户注册请求"""
    phone: str = Field(..., min_length=8, max_length=20, description="手机号")
    password: str = Field(..., min_length=6, max_length=20, description="密码")
    nickname: Optional[str] = Field(None, min_length=2, max_length=20, description="昵称")
    code: Optional[str] = Field(None, description="微信登录code，用于防重复薅体验会员")

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        # 移除空格、横杠、括号等特殊字符
        clean_phone = v.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')

        # 检查是否只包含数字和加号
        if not re.match(r'^[\d+]+$', clean_phone):
            raise ValueError('手机号只能包含数字和加号')

        # 中国大陆手机号：1开头，第二位3-9，共11位
        china_mobile_pattern = r'^1[3-9]\d{9}$'

        # 国际手机号：可以以+开头，或直接是数字，长度8-15位
        international_pattern = r'^\+?\d{8,15}$'

        if re.match(china_mobile_pattern, clean_phone):
            # 中国大陆手机号格式正确
            return clean_phone
        elif re.match(international_pattern, clean_phone):
            # 国际手机号格式正确
            # 进一步验证：如果不是+开头且不是1开头的11位号码，长度至少8位
            if not clean_phone.startswith('+') and len(clean_phone) < 8:
                raise ValueError('手机号长度不正确')
            return clean_phone
        else:
            raise ValueError('手机号格式不正确')

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not re.search(r'[a-zA-Z]', v) or not re.search(r'\d', v):
            raise ValueError('密码必须包含字母和数字')
        return v


class UserLogin(BaseModel):
    """用户登录请求"""
    phone: str = Field(..., min_length=8, max_length=20, description="手机号")
    password: str = Field(..., min_length=1, description="密码")


class UserInfo(BaseModel):
    """用户信息响应"""
    id: int
    phone: str
    nickname: Optional[str]
    is_paid: bool
    paid_start_time: Optional[datetime] = None
    paid_end_time: Optional[datetime] = None
    is_trial_user: bool = False
    has_used_trial: bool = False
    trial_start_time: Optional[datetime] = None
    trial_end_time: Optional[datetime] = None
    role: UserRole
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WeChatLoginRequest(BaseModel):
    """微信登录请求"""
    code: str = Field(..., description="微信登录临时code")
    phone: str = Field(..., min_length=8, max_length=20, description="手机号")

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        # 移除空格、横杠、括号等特殊字符
        clean_phone = v.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')

        # 检查是否只包含数字和加号
        if not re.match(r'^[\d+]+$', clean_phone):
            raise ValueError('手机号只能包含数字和加号')

        # 中国大陆手机号：1开头，第二位3-9，共11位
        china_mobile_pattern = r'^1[3-9]\d{9}$'

        # 国际手机号：可以以+开头，或直接是数字，长度8-15位
        international_pattern = r'^\+?\d{8,15}$'

        if re.match(china_mobile_pattern, clean_phone):
            # 中国大陆手机号格式正确
            return clean_phone
        elif re.match(international_pattern, clean_phone):
            # 国际手机号格式正确
            # 进一步验证：如果不是+开头且不是1开头的11位号码，长度至少8位
            if not clean_phone.startswith('+') and len(clean_phone) < 8:
                raise ValueError('手机号长度不正确')
            return clean_phone
        else:
            raise ValueError('手机号格式不正确')


class WeChatLoginResponse(BaseModel):
    """微信登录响应"""
    openid: str
    user: Optional[UserInfo] = None
    access_token: Optional[str] = None
    token_type: str = "bearer"


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


class SubscriptionStatus(BaseModel):
    """订阅状态响应"""
    is_paid: bool
    paid_start_time: Optional[datetime] = None
    paid_end_time: Optional[datetime] = None
    role: UserRole
    can_view_recommendations: bool
    should_show_upgrade_prompt: bool
    is_key_match_member: bool = Field(False, description="是否为重心场次会员")
    is_trial: bool = Field(False, description="是否为有效体验会员")

    class Config:
        from_attributes = True


class GuidePopupStatus(BaseModel):
    """引导弹窗状态响应"""
    should_show_popup: bool
    is_paid_user: bool
    is_trial_user: bool

