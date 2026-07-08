"""
昨日战绩相关的 Pydantic Schema
"""
from pydantic import BaseModel, field_validator
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal


class DailyAchievementCreate(BaseModel):
    """创建昨日战绩请求"""
    date: date
    title: str
    subtitle: Optional[str] = None
    total_count: int
    win_count: int
    highlights: Optional[List[dict]] = None
    description: Optional[str] = None
    banner_image: Optional[str] = None
    is_active: bool = True


class DailyAchievementUpdate(BaseModel):
    """更新昨日战绩请求 - 所有字段可选"""
    date: Optional[date] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    total_count: Optional[int] = None
    win_count: Optional[int] = None
    highlights: Optional[List[dict]] = None
    description: Optional[str] = None
    banner_image: Optional[str] = None
    is_active: Optional[bool] = None


class DailyAchievementResponse(BaseModel):
    """昨日战绩响应"""
    id: int
    date: date
    title: str
    subtitle: Optional[str] = ""
    total_count: int
    win_count: int
    accuracy_rate: Decimal
    highlights: Optional[List[dict]] = None
    description: Optional[str] = None
    banner_image: Optional[str] = None
    is_active: bool
    created_by_id: int
    created_at: datetime
    updated_at: datetime

    @field_validator('subtitle', mode='before')
    @classmethod
    def convert_none_to_empty(cls, v):
        """将None转换为空字符串"""
        return v if v is not None else ""

    class Config:
        from_attributes = True
