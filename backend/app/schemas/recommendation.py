"""
推荐相关的 Pydantic Schema
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, Dict, Any, Literal
from app.models.recommendation import RecommendationStatus

# 定义预测类型的字面量类型
PredictionTypeLiteral = Literal["football", "basketball"]


class RecommendationCreate(BaseModel):
    """创建推荐请求"""
    prediction_type: PredictionTypeLiteral = Field(..., description="预测类型")
    title: str = Field(..., min_length=1, max_length=50, description="推荐标题")
    promotion_title: Optional[str] = Field(None, max_length=100, description="推广标题（选填）")
    prediction_data: Dict[str, Any] = Field(..., description="预测数据")  # 临时改为 Dict 以调试
    analysis_text: str = Field(..., min_length=0, max_length=500, description="分析说明")

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('标题不能为空')
        return v.strip()

    @field_validator('promotion_title')
    @classmethod
    def validate_promotion_title(cls, v):
        if v:
            return v.strip()
        return None

    @field_validator('analysis_text')
    @classmethod
    def validate_analysis(cls, v):
        # 允许空字符串，只做trim处理
        return v.strip()

class RecommendationUpdate(BaseModel):
    """更新推荐请求"""
    prediction_type: Optional[PredictionTypeLiteral] = None
    title: Optional[str] = Field(None, min_length=1, max_length=50)
    promotion_title: Optional[str] = Field(None, max_length=100)
    prediction_data: Optional[Dict[str, Any]] = None
    analysis_text: Optional[str] = Field(None, min_length=0, max_length=500)
    status: Optional[RecommendationStatus] = None


class RecommendationResponse(BaseModel):
    """推荐响应"""
    id: int
    created_by_id: int
    prediction_type: str
    title: str
    promotion_title: Optional[str] = None
    prediction_data: Dict[str, Any]
    analysis_text: str
    status: RecommendationStatus
    is_confirmed: bool = False
    actual_outcome: Optional[Dict[str, Any]] = None
    archived_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ActualOutcome(BaseModel):
    """实际比赛结果输入"""
    hit_status: str = Field(..., description="命中状态: 可以是 hit/partial/miss 或其他自定义状态")
    partial_detail: Optional[str] = Field(None, max_length=20, description="部分命中详情，如 2✓1")
    notes: Optional[str] = Field(None, description="备注说明")
    is_highlight: bool = Field(False, description="是否在近期好评场次展示，默认否")

    @field_validator('hit_status')
    @classmethod
    def validate_hit_status(cls, v):
        # 允许任意文本，但需要去除首尾空格且不能为空
        v = v.strip()
        if not v:
            raise ValueError('命中状态不能为空')
        if len(v) > 20:
            raise ValueError('命中状态不能超过20个字符')
        return v

    @field_validator('notes')
    @classmethod
    def validate_notes(cls, v):
        if v and len(v.strip()) > 200:
            raise ValueError('备注说明不能超过200个字符')
        return v.strip() if v else None


class RecommendationComplete(BaseModel):
    """完成推荐请求"""
    actual_outcome: ActualOutcome = Field(..., description="实际结果")


class StatisticsResponse(BaseModel):
    """统计数据响应"""
    total_count: int = Field(..., description="总场次数")
    accurate_count: int = Field(..., description="准确场次数")
    accuracy_rate: float = Field(..., description="总准确率")
    total_recs_count: int = Field(0, description="总推荐数（不受免费用户过滤影响）")
    football_stats: Optional[Dict[str, Any]] = Field(None, description="足球统计（VIP专享）")
    basketball_stats: Optional[Dict[str, Any]] = Field(None, description="篮球统计（VIP专享）")
    key_match_stats: Optional[Dict[str, Any]] = Field(None, description="重心场次统计（VIP专享）")

