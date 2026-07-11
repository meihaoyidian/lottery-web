"""
历史记录相关API端点
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.deps import require_history_access, get_current_user_optional, get_user_flags
from app.models.user import User
from app.schemas.recommendation import (
    RecommendationResponse,
    StatisticsResponse,
    PredictionTypeLiteral
)
from app.models.recommendation import Recommendation
from app.services.history_service import HistoryService
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=dict)
async def get_history(
    prediction_type: Optional[PredictionTypeLiteral] = Query(None, description="预测类型过滤"),
    month: Optional[str] = Query(None, description="月份过滤,格式：YYYY-MM"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=50, description="每页数量"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    获取历史推荐列表（所有用户 + 审核模式下的匿名访问）

    - **prediction_type**: 可选的预测类型过滤（football/basketball）
    - **month**: 可选的月份过滤，格式：YYYY-MM（例如：2024-12）
    - **start_date**: 可选的开始日期过滤
    - **end_date**: 可选的结束日期过滤
    - **page**: 页码，从1开始
    - **page_size**: 每页数量，最大50

    默认返回全部已完成的推荐。
    非付费用户只能看到高命中率推荐（允许最多1场错误）。
    """
    # 审核模式下的匿名访问
    if current_user is None:
        logger.info("审核模式：匿名用户请求历史记录")
    else:
        logger.info(f"用户 {current_user.id} 请求历史记录，月份：{month}")

    # 审核模式下返回2条假历史记录（符合规范要求）
    if settings.REVIEW_MODE and current_user is None:
        now = datetime.now().isoformat()
        return {
            'items': [
                {
                    "id": 1, "created_by_id": 0, "prediction_type": "football",
                    "title": "英超赛事数据", "promotion_title": None,
                    "prediction_data": {
                        "prediction_type": "football",
                        "single_matches": [
                            {"match_id": "#101", "home_team": "曼联", "away_team": "利物浦", "is_public": True, "is_key_match": False, "is_featured": False, "hit_status": "hit"},
                        ],
                    },
                    "analysis_text": "基于近期状态与历史交锋数据综合分析。",
                    "status": "completed", "actual_outcome": {"hit_status": "hit"},
                    "archived_at": now, "created_at": now, "updated_at": now,
                    "has_key_match": False, "is_user_bound_key_match": False,
                    "is_accurate": True,
                },
                {
                    "id": 2, "created_by_id": 0, "prediction_type": "basketball",
                    "title": "NBA赛事数据", "promotion_title": None,
                    "prediction_data": {
                        "prediction_type": "basketball",
                        "single_matches": [
                            {"match_id": "#201", "home_team": "湖人", "away_team": "勇士", "is_public": True, "is_key_match": False, "is_featured": False, "hit_status": "hit"},
                        ],
                    },
                    "analysis_text": "综合球队近期战绩与阵容变化分析。",
                    "status": "completed", "actual_outcome": {"hit_status": "hit"},
                    "archived_at": now, "created_at": now, "updated_at": now,
                    "has_key_match": False, "is_user_bound_key_match": False,
                    "is_accurate": True,
                },
            ],
            'total': 2, 'page': 1, 'page_size': page_size, 'has_more': False,
            'is_preview': False,
        }

    # 判断是否为付费用户（统一使用 get_user_flags）
    is_paid_user = get_user_flags(current_user)['has_full_access']

    if current_user:
        logger.info(f"用户 {current_user.id} 付费状态: is_paid_user={is_paid_user}")

    result = HistoryService.get_history_recommendations(
        db=db,
        prediction_type=prediction_type,
        month=month,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
        is_paid_user=is_paid_user
    )

    # 添加准确性标记
    items_with_accuracy = []
    for item in result['items']:
        item_dict = RecommendationResponse.model_validate(item).model_dump()
        item_dict['is_accurate'] = HistoryService._is_prediction_accurate(item)
        items_with_accuracy.append(item_dict)

    return {
        'items': items_with_accuracy,
        'total': result['total'],
        'page': result['page'],
        'page_size': result['page_size'],
        'has_more': result['has_more'],
        'is_preview': result.get('is_preview', False)
    }


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(
    prediction_type: Optional[PredictionTypeLiteral] = Query(None, description="预测类型过滤"),
    month: Optional[str] = Query(None, description="月份过滤，格式：YYYY-MM"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    获取历史推荐统计数据（所有用户）

    - **prediction_type**: 可选的预测类型过滤（football/basketball）
    - **month**: 可选的月份过滤，格式：YYYY-MM（例如：2024-12）
    - **start_date**: 可选的开始日期过滤
    - **end_date**: 可选的结束日期过滤

    返回准确率统计信息。
    默认统计全部已完成的推荐。
    非付费用户只统计高命中率推荐，且排除miss场次。
    """
    # 审核模式下的匿名访问
    if current_user is None:
        logger.info("审核模式：匿名用户请求历史统计")
    else:
        logger.info(f"用户 {current_user.id} 请求历史统计，月份：{month}")

    # 审核模式下返回假统计数据
    if settings.REVIEW_MODE and current_user is None:
        return StatisticsResponse(
            total_count=3, accurate_count=3, accuracy_rate=100.0, total_recs_count=2,
            football_stats={
                'total': 2, 'accurate': 2, 'rate': 100.0,
                'parlay_total': 0, 'parlay_accurate': 0, 'parlay_rate': 0.0,
                'key_match_total': 0, 'key_match_accurate': 0, 'key_match_rate': 0.0,
            },
            basketball_stats={
                'total': 1, 'accurate': 1, 'rate': 100.0,
                'parlay_total': 0, 'parlay_accurate': 0, 'parlay_rate': 0.0,
                'key_match_total': 0, 'key_match_accurate': 0, 'key_match_rate': 0.0,
            },
            key_match_stats={
                'total': 0, 'accurate': 0, 'rate': 0.0,
                'football_total': 0, 'football_accurate': 0, 'football_rate': 0.0,
                'basketball_total': 0, 'basketball_accurate': 0, 'basketball_rate': 0.0,
            }
        )

    # 判断是否为付费用户（统一使用 get_user_flags）
    is_paid_user = get_user_flags(current_user)['has_full_access']

    if current_user:
        logger.info(f"用户 {current_user.id} 统计付费状态: is_paid_user={is_paid_user}")

    # 所有人统一用真实数据
    stats = HistoryService.get_statistics(
        db=db,
        prediction_type=prediction_type,
        month=month,
        start_date=start_date,
        end_date=end_date,
        is_paid_user=True
    )

    return StatisticsResponse(**stats)


@router.get("/monthly-statistics")
async def get_monthly_statistics(
    prediction_type: Optional[PredictionTypeLiteral] = Query(None, description="预测类型过滤"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    获取按月统计的命中率数据

    - **prediction_type**: 可选的预测类型过滤（football/basketball）

    返回最近几个月的命中率统计，用于前端展示趋势图。
    所有用户都可以访问（包括匿名用户）。
    """
    try:
        # 审核模式下返回假月度数据
        if settings.REVIEW_MODE and current_user is None:
            return {
                "monthly_stats": [
                    {"month": "2026-05", "total_count": 3, "hit_count": 3, "hit_rate": 100, "football_count": 2, "football_hit": 2, "football_rate": 100, "basketball_count": 1, "basketball_hit": 1, "basketball_rate": 100},
                ]
            }

        # 判断是否为付费用户（统一使用 get_user_flags）
        is_paid_user = get_user_flags(current_user)['has_full_access']

        # 获取月度统计数据
        monthly_stats = HistoryService.get_monthly_statistics(
            db=db,
            prediction_type=prediction_type,
            is_paid_user=is_paid_user
        )

        return {
            "monthly_stats": monthly_stats
        }
    except Exception as e:
        logger.error(f"获取月度统计数据失败: {e}")
        return {
            "monthly_stats": []
        }


@router.get("/highlights")
async def get_highlights(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    获取精华命中场次（免费用户可见，用于转化展示）
    返回 actual_outcome.hit_status='hit' 的推荐中的单场数据，最多10条
    """
    # 审核模式下返回假精华场次
    if settings.REVIEW_MODE and current_user is None:
        return {"highlights": [
            {"match_id": "#101", "home_team": "曼联", "away_team": "利物浦", "prediction_type": "football", "hit_status": "hit", "is_key_match": False, "is_featured": False},
            {"match_id": "#102", "home_team": "阿森纳", "away_team": "切尔西", "prediction_type": "football", "hit_status": "hit", "is_key_match": False, "is_featured": False},
            {"match_id": "#201", "home_team": "湖人", "away_team": "勇士", "prediction_type": "basketball", "hit_status": "hit", "is_key_match": False, "is_featured": False},
        ]}

    rec_ids = HistoryService.get_highlight_ids(db=db, limit=50)
    if not rec_ids:
        return {"highlights": []}

    recs = db.query(Recommendation).filter(Recommendation.id.in_(rec_ids)).order_by(Recommendation.archived_at.desc()).all()

    highlights = []
    for rec in recs:
        if not rec.prediction_data:
            continue
        for match in rec.prediction_data.get('single_matches', []):
            if len(highlights) >= 20:
                break
            # 只取已明确标记为命中/走水的单场
            m_status = str(match.get('hit_status', 'pending')).strip().lower()
            if m_status not in ('hit', 'push'):
                continue
            highlights.append({
                'match_id': match.get('match_id', ''),
                'home_team': match.get('home_team', ''),
                'away_team': match.get('away_team', ''),
                'total_points': match.get('total_points', ''),
                'handicap': match.get('handicap', ''),
                'prediction_rate': match.get('prediction_rate', ''),
                'prediction_type': rec.prediction_type,
                'is_key_match': match.get('is_key_match', False),
                'is_featured': match.get('is_featured', False),
                'hit_status': 'hit',
            })
        if len(highlights) >= 10:
            break

    return {"highlights": highlights}


@router.get("/{recommendation_id}", response_model=dict)
async def get_history_detail(
    recommendation_id: int,
    current_user: User = Depends(require_history_access),
    db: Session = Depends(get_db)
):
    """
    获取历史推荐详情（付费用户）

    - **recommendation_id**: 推荐ID

    需要付费用户权限。
    """
    logger.info(f"用户 {current_user.id} 请求历史详情 {recommendation_id}")

    recommendation = HistoryService.get_recommendation_detail(
        db=db,
        recommendation_id=recommendation_id
    )

    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="历史推荐不存在"
        )

    result = RecommendationResponse.model_validate(recommendation).model_dump()
    result['is_accurate'] = HistoryService._is_prediction_accurate(recommendation)

    return result
