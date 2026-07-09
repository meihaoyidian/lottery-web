"""
推荐相关API端点
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
import json
from app.database import get_db
from app.deps import require_paid_user, require_admin, get_current_user, get_current_user_optional, get_user_flags
from app.models.user import User
from app.models.recommendation import Recommendation
from app.config import settings
from app.schemas.recommendation import (
    RecommendationResponse,
    RecommendationCreate,
    RecommendationUpdate,
    RecommendationComplete,
    PredictionTypeLiteral
)
from app.services.recommendation_service import RecommendationService
from app.services.history_service import HistoryService
import logging

logger = logging.getLogger(__name__)

from datetime import date

router = APIRouter(prefix="/recommendations", tags=["recommendations"])



@router.get("/today-status", response_model=dict)
async def get_today_status(db: Session = Depends(get_db)):
    """
    今日流程进度状态。

    每日节奏：下午 2 点前更新场次 → 下午 4-6 点更新推荐数据 → 晚 7-8 点确认方案。
    数据状态优先，时间仅用于空态措辞（提前完成也如实反映）。
    """
    from sqlalchemy import text
    now = datetime.now()
    today = now.date()

    # 统一用 Python 时钟（避免混用 MySQL CURDATE 的时区问题）
    result = db.execute(
        text(
            "SELECT prediction_data, is_confirmed, updated_at FROM recommendations "
            "WHERE DATE(created_at) = :today AND status = 'active' "
            "ORDER BY updated_at DESC"
        ),
        {"today": today.isoformat()}
    ).fetchall()

    total = len(result)

    # 空态：今日还没场次
    if total == 0:
        status = "pending" if now.hour < 14 else "delayed"
        return {"status": status, "count": 0, "analyzed": 0, "confirmed": 0, "last_updated": None}

    # 统计：已分析场次数、已确认场次数
    def _row_has_analysis(pd_raw):
        try:
            data = json.loads(pd_raw) if isinstance(pd_raw, str) else (pd_raw or {})
            return any(
                m.get('total_points') is not None or m.get('handicap') is not None
                for m in data.get('single_matches', [])
            )
        except Exception:
            return False

    analyzed = sum(1 for row in result if _row_has_analysis(row[0]))
    confirmed = sum(1 for row in result if row[1])
    last_updated = result[0][2]

    # 数据状态优先的进度判定
    if confirmed >= total:
        status = "confirmed"      # 全部已确认
    elif confirmed > 0:
        status = "confirming"     # 部分确认中
    elif analyzed >= total:
        status = "analyzed"       # 全部已分析，待确认
    elif analyzed > 0:
        status = "analyzing"      # 部分分析中
    else:
        status = "created"        # 场次已出，待分析

    return {
        "status": status,
        "count": total,
        "analyzed": analyzed,
        "confirmed": confirmed,
        "last_updated": last_updated.isoformat() if last_updated else None
    }


@router.post("/{recommendation_id}/toggle-confirm")
async def toggle_confirm(
    recommendation_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """管理员逐张确认/取消确认推荐"""
    recommendation = db.query(Recommendation).filter(
        Recommendation.id == recommendation_id,
        Recommendation.status == 'active'
    ).first()
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="推荐不存在"
        )
    recommendation.is_confirmed = not recommendation.is_confirmed
    db.commit()
    db.refresh(recommendation)

    logger.info(f"管理员 {current_user.id} {'确认' if recommendation.is_confirmed else '取消确认'} 推荐 {recommendation_id}")
    return recommendation


@router.get("/admin/all", response_model=dict)
async def get_all_recommendations_admin(
    status: Optional[str] = Query(None, description="状态过滤（active/completed/inactive）"),
    prediction_type: Optional[PredictionTypeLiteral] = Query(None, description="预测类型过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=50, description="每页数量"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    获取所有推荐列表（管理员）

    - **status**: 可选的状态过滤（active/completed/inactive）
    - **prediction_type**: 可选的预测类型过滤（football/basketball）
    - **page**: 页码，从1开始
    - **page_size**: 每页数量，最大50

    需要管理员权限。返回所有状态的推荐，包括已删除的。
    """
    logger.info(f"管理员 {current_user.id} 请求推荐列表，状态: {status}")

    recommendations, total = RecommendationService.get_all_recommendations(
        db=db,
        status=status,
        prediction_type=prediction_type,
        page=page,
        page_size=page_size
    )

    return {
        "items": [
            RecommendationResponse.model_validate(rec) for rec in recommendations
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_more": page * page_size < total
    }


@router.get("", response_model=dict)
async def get_recommendations(
    prediction_type: Optional[PredictionTypeLiteral] = Query(None, description="预测类型过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=50, description="每页数量"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    获取活跃推荐列表（所有登录用户 + 审核模式下的匿名访问）

    - **prediction_type**: 可选的预测类型过滤（football/basketball）
    - **page**: 页码，从1开始
    - **page_size**: 每页数量，最大50

    付费用户和体验用户可以查看完整内容。
    普通用户可以看到列表，但只能查看标题和公开的单场分析。
    审核模式下允许匿名访问。
    """
    # 审核模式下的匿名访问
    if current_user is None:
        logger.info("审核模式：匿名用户请求推荐列表")
    else:
        logger.info(f"用户 {current_user.id} 请求推荐列表")

    # 审核模式下返回2条示例假数据（符合规范要求）
    if settings.REVIEW_MODE and current_user is None:
        now = datetime.now().isoformat()
        return {
            "recommendations": [
                {
                    "id": 1, "created_by_id": 0, "prediction_type": "football",
                    "title": "英超赛事数据", "promotion_title": None,
                    "prediction_data": {
                        "prediction_type": "football",
                        "single_matches": [
                            {"match_id": "#101", "home_team": "曼联", "away_team": "利物浦", "is_public": True, "is_key_match": False, "is_featured": False},
                            {"match_id": "#102", "home_team": "阿森纳", "away_team": "切尔西", "is_public": True, "is_key_match": False, "is_featured": False},
                        ],
                    },
                    "analysis_text": "基于近期球队状态、伤病情况及历史交锋数据综合分析。所有数据仅供学习交流使用。",
                    "status": "active", "actual_outcome": None, "archived_at": None,
                    "created_at": now, "updated_at": now,
                    "has_key_match": False, "is_user_bound_key_match": False,
                },
                {
                    "id": 2, "created_by_id": 0, "prediction_type": "basketball",
                    "title": "NBA赛事数据", "promotion_title": None,
                    "prediction_data": {
                        "prediction_type": "basketball",
                        "single_matches": [
                            {"match_id": "#201", "home_team": "湖人", "away_team": "勇士", "is_public": True, "is_key_match": False, "is_featured": False},
                        ],
                    },
                    "analysis_text": "综合球队近期战绩、主客场表现及阵容变化分析。所有数据仅供学习交流使用。",
                    "status": "active", "actual_outcome": None, "archived_at": None,
                    "created_at": now, "updated_at": now,
                    "has_key_match": False, "is_user_bound_key_match": False,
                },
            ],
            "total": 2,
            "page": 1,
            "page_size": page_size,
            "total_pages": 1,
        }

    recommendations, total = RecommendationService.get_active_recommendations(
        db=db,
        prediction_type=prediction_type,
        page=page,
        page_size=page_size
    )

    # 统一获取用户身份标识
    flags = get_user_flags(current_user)
    is_paid_user = flags['is_paid_valid']

    # 管理员、付费用户可以查看完整内容
    can_view_full_content = flags['is_admin'] or is_paid_user

    if current_user:
        logger.info(f"用户 {current_user.id} 权限检查: is_paid_user={is_paid_user}, can_view_full_content={can_view_full_content}")
    else:
        logger.info(f"匿名用户权限检查: can_view_full_content={can_view_full_content}")

    # 为所有用户处理推荐数据
    processed_recommendations = []
    for rec in recommendations:
        rec_data = RecommendationResponse.model_validate(rec).model_dump()

        # 检查原始数据中是否包含重心场次
        has_key_match = False

        if rec_data.get('prediction_data'):
            prediction_data = rec_data['prediction_data']
            if 'single_matches' in prediction_data:
                original_count = len(prediction_data['single_matches'])
                # 检查是否有重心场次
                has_key_match = any(match.get('is_key_match', False) for match in prediction_data['single_matches'])

                # 非付费非管理员：真正剥离敏感预测数据（不能只发标记，否则前端可直接读取）
                if not can_view_full_content:
                    masked_matches = []
                    masked_count = 0
                    for match in prediction_data['single_matches']:
                        # 公开场次 或 已出结果的场次 → 保留完整（引流钩子/战绩展示）
                        is_resulted = match.get('hit_status') and match.get('hit_status') != 'pending'
                        if match.get('is_public', False) or is_resulted:
                            masked_matches.append(match)
                            continue
                        # 其余场次：删除核心预测字段，标记 _blur 供前端展示锁态
                        m = {**match}
                        m.pop('total_points', None)
                        m.pop('handicap', None)
                        m.pop('prediction_basis', None)
                        m['_blur'] = True
                        masked_matches.append(m)
                        masked_count += 1
                    prediction_data['single_matches'] = masked_matches
                    logger.info(f"免费用户内容遮罩: 推荐 {rec_data['id']}, 总共 {original_count} 场，锁定 {masked_count} 场")

            # 组合方案：非会员一律剥离内容并标记
            if not can_view_full_content and prediction_data.get('parlays'):
                prediction_data['parlays'] = [
                    {**p, 'bet_types': []} for p in prediction_data['parlays']
                ]
                rec_data['_blur_parlay'] = True

        # 添加 has_key_match 和 is_user_bound_key_match 字段到推荐数据中
        rec_data['has_key_match'] = has_key_match
        rec_data['is_user_bound_key_match'] = False
        processed_recommendations.append(rec_data)

    return {
        "recommendations": processed_recommendations,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.get("/{recommendation_id}", response_model=RecommendationResponse)
async def get_recommendation_detail(
    recommendation_id: int,
    current_user: User = Depends(require_paid_user),
    db: Session = Depends(get_db)
):
    """
    获取推荐详情（付费用户）

    - **recommendation_id**: 推荐ID

    需要付费用户权限。浏览时会自动记录浏览行为。
    """
    logger.info(f"用户 {current_user.id} 请求推荐详情 {recommendation_id}")

    recommendation = RecommendationService.get_recommendation_by_id(
        db=db,
        recommendation_id=recommendation_id
    )

    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="推荐不存在"
        )

    # 检查推荐是否可访问（未归档且状态为active）
    if recommendation.archived_at is not None or recommendation.status != "active":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="推荐不存在或已归档"
        )

    return RecommendationResponse.model_validate(recommendation)


@router.post("", response_model=RecommendationResponse, status_code=status.HTTP_201_CREATED)
async def create_recommendation(
    recommendation_data: RecommendationCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    创建新推荐（管理员）
    """
    import json

    logger.info(f"管理员 {current_user.id} 创建推荐")
    logger.info(f"接收到的数据: {json.dumps(recommendation_data.model_dump(), ensure_ascii=False, indent=2)}")
    logger.debug(f"prediction_data 类型: {type(recommendation_data.prediction_data)}")
    logger.debug(f"prediction_data 内容: {json.dumps(recommendation_data.prediction_data, ensure_ascii=False, indent=2)}")

    # 审核模式：禁止创建推荐
    if settings.REVIEW_MODE:
        logger.info("审核模式开启，禁止创建推荐")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无法创建推荐"
        )

    try:
        recommendation = RecommendationService.create_recommendation(
            db=db,
            recommendation_data=recommendation_data,
            created_by_id=current_user.id
        )


        return RecommendationResponse.model_validate(recommendation)

    except HTTPException:
        # 重新抛出HTTP异常（如409重复冲突）
        raise
    except Exception as e:
        logger.error(f"创建推荐失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建推荐失败: {str(e)}"
        )


@router.put("/{recommendation_id}", response_model=RecommendationResponse)
async def update_recommendation(
    recommendation_id: int,
    recommendation_data: RecommendationUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    更新推荐（管理员）
    """
    logger.info(f"管理员 {current_user.id} 更新推荐 {recommendation_id}")

    try:
        recommendation = RecommendationService.update_recommendation(
            db=db,
            recommendation_id=recommendation_id,
            recommendation_data=recommendation_data
        )

        if not recommendation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="推荐不存在"
            )

        return RecommendationResponse.model_validate(recommendation)

    except HTTPException:
        # 重新抛出HTTP异常（如409重复冲突、404未找到）
        raise
    except Exception as e:
        logger.error(f"更新推荐失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"更新推荐失败: {str(e)}"
        )


@router.delete("/{recommendation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recommendation(
    recommendation_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    删除推荐（管理员）

    软删除：将状态设置为inactive
    需要管理员权限。
    """
    logger.info(f"管理员 {current_user.id} 删除推荐 {recommendation_id}")

    success = RecommendationService.delete_recommendation(
        db=db,
        recommendation_id=recommendation_id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="推荐不存在"
        )

    return None


@router.post("/{recommendation_id}/complete", response_model=RecommendationResponse)
async def complete_recommendation(
    recommendation_id: int,
    completion_data: RecommendationComplete,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    标记推荐为完成并录入实际结果（管理员）

    需要管理员权限。用于历史记录和准确率统计。
    """
    logger.info(f"管理员 {current_user.id} 完成推荐 {recommendation_id}")

    try:
        recommendation = HistoryService.complete_recommendation(
            db=db,
            recommendation_id=recommendation_id,
            actual_outcome=completion_data.actual_outcome.model_dump()
        )
        return RecommendationResponse.model_validate(recommendation)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"完成推荐失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"完成推荐失败: {str(e)}"
        )
