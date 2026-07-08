"""
订阅消息API端点
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.deps import get_current_user, require_paid_user
from app.models.user import User
from app.schemas.subscription import (
    SubscribeRequest,
    SubscriptionResponse,
    SubscriptionStatusResponse
)
from app.services.subscription_service import SubscriptionService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/subscribe", response_model=SubscriptionResponse)
async def subscribe_recommendation_updates(
    subscribe_data: SubscribeRequest,
    current_user: User = Depends(require_paid_user),
    db: Session = Depends(get_db)
):
    """
    订阅推荐更新消息（付费用户和管理员）

    需要付费用户权限。订阅后，当管理员发布或更新推荐时，会收到订阅消息推送。
    """
    logger.info(f"用户 {current_user.id} 订阅推荐更新")

    try:
        subscription = SubscriptionService.subscribe(
            db=db,
            user_id=current_user.id,
            openid=subscribe_data.openid,
            template_id=subscribe_data.template_id
        )

        return SubscriptionResponse.model_validate(subscription)

    except Exception as e:
        logger.error(f"订阅失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"订阅失败: {str(e)}"
        )


@router.post("/unsubscribe", status_code=status.HTTP_204_NO_CONTENT)
async def unsubscribe_recommendation_updates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    取消订阅推荐更新消息

    所有登录用户都可以取消订阅。
    """
    logger.info(f"用户 {current_user.id} 取消订阅")

    success = SubscriptionService.unsubscribe(
        db=db,
        user_id=current_user.id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到订阅记录"
        )

    return None


@router.get("/status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取订阅状态

    所有登录用户都可以查询自己的订阅状态。
    """
    is_subscribed = SubscriptionService.get_subscription_status(
        db=db,
        user_id=current_user.id
    )

    return SubscriptionStatusResponse(is_subscribed=is_subscribed)
