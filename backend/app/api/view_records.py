"""
浏览记录相关API端点
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from typing import Optional
from app.deps import require_admin, get_current_user, get_current_user_optional
from app.models.user import User
from app.schemas.view_record import (
    ViewRecordCreate,
    ViewRecordResponse,
    ViewRecordListResponse
)
from app.services.view_record_service import ViewRecordService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/view-records", tags=["view-records"])


@router.post("", response_model=ViewRecordResponse, status_code=status.HTTP_201_CREATED)
async def record_view(
    view_data: ViewRecordCreate,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    记录用户浏览推荐（仅登录用户）

    游客不记录浏览行为。
    """
    from app.models.recommendation import Recommendation

    # 校验推荐是否存在
    recommendation = db.query(Recommendation).filter(
        Recommendation.id == view_data.recommendation_id
    ).first()
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"推荐 {view_data.recommendation_id} 不存在"
        )

    # 游客不记录浏览
    if current_user is None:
        return ViewRecordResponse()

    user_id = current_user.id
    logger.info(f"user_id={user_id} 浏览推荐 {view_data.recommendation_id}")

    try:
        view_record = ViewRecordService.record_view(
            db=db,
            user_id=user_id,
            recommendation_id=view_data.recommendation_id
        )

        if view_record is None:
            return ViewRecordResponse()

        return ViewRecordResponse(
            id=view_record.id,
            user_id=view_record.user_id,
            recommendation_id=view_record.recommendation_id,
            viewed_at=view_record.viewed_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"记录浏览失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"记录浏览失败: {str(e)}"
        )


@router.get("/recommendation/{recommendation_id}", response_model=ViewRecordListResponse)
async def get_recommendation_viewers(
    recommendation_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    获取某个推荐的浏览记录（管理员）

    需要管理员权限。查看哪些用户浏览了指定推荐，包含浏览次数统计。
    """
    logger.info(f"管理员 {current_user.id} 查询推荐 {recommendation_id} 的浏览记录")

    try:
        records, total, unique_viewers, guest_view_count = ViewRecordService.get_recommendation_viewers(
            db=db,
            recommendation_id=recommendation_id,
            page=page,
            page_size=page_size
        )

        # 转换为响应格式
        record_responses = [
            ViewRecordResponse(
                user_id=r['user_id'],
                user_phone=r['user_phone'],
                user_nickname=r['user_nickname'],
                user_created_at=r['user_created_at'],
                view_count=r['view_count'],
                last_viewed_at=r['last_viewed_at'],
                first_viewed_at=r['first_viewed_at'],
                user_role=r['user_role'],
                user_is_paid=r['user_is_paid']
            )
            for r in records
        ]

        # 如果有游客浏览，在第1页头部插入一条游客汇总
        if guest_view_count > 0 and page == 1:
            guest_entry = ViewRecordResponse(
                user_id=0,
                user_phone="游客",
                user_nickname="未登录用户",
                view_count=guest_view_count,
                user_role="guest",
                user_is_paid=False
            )
            record_responses.insert(0, guest_entry)

        return ViewRecordListResponse(
            records=record_responses,
            total=total,
            unique_viewers=unique_viewers,
            guest_view_count=guest_view_count
        )

    except Exception as e:
        logger.error(f"查询浏览记录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询浏览记录失败: {str(e)}"
        )


@router.get("/my-history", response_model=dict)
async def get_my_view_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=50, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户的浏览历史（所有登录用户）

    返回当前用户的浏览记录列表。
    """
    logger.info(f"用户 {current_user.id} 查询个人浏览历史")

    try:
        records, total = ViewRecordService.get_user_view_history(
            db=db,
            user_id=current_user.id,
            page=page,
            page_size=page_size
        )

        return {
            "records": [
                ViewRecordResponse.model_validate(r) for r in records
            ],
            "total": total,
            "page": page,
            "page_size": page_size
        }

    except Exception as e:
        logger.error(f"查询浏览历史失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询浏览历史失败: {str(e)}"
        )
