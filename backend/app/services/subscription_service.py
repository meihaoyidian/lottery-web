"""
微信订阅消息服务
"""
import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.config import settings
from app.models.subscription import (
    RecommendationSubscription,
    SubscriptionMessage,
    MessageStatus
)

logger = logging.getLogger(__name__)


class WeChatService:
    """微信服务类"""

    # 微信API基础URL
    WECHAT_API_BASE = "https://api.weixin.qq.com"

    # Access Token 缓存（生产环境应使用Redis等缓存）
    _access_token: Optional[str] = None
    _token_expires_at: Optional[datetime] = None

    @classmethod
    def get_access_token(cls) -> str:
        """
        获取微信 Access Token

        Returns:
            str: Access Token

        Raises:
            Exception: 获取失败时抛出异常
        """
        # 检查缓存的token是否有效
        if cls._access_token and cls._token_expires_at:
            if datetime.now() < cls._token_expires_at:
                return cls._access_token

        # 获取新的 Access Token
        url = f"{cls.WECHAT_API_BASE}/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": settings.WECHAT_APPID,
            "secret": settings.WECHAT_SECRET
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "access_token" in data:
                cls._access_token = data["access_token"]
                # Token有效期为7200秒，提前5分钟过期
                from datetime import timedelta
                cls._token_expires_at = datetime.now() + timedelta(seconds=data.get("expires_in", 7200) - 300)
                logger.info("成功获取微信 Access Token")
                return cls._access_token
            else:
                error_msg = f"获取Access Token失败: {data.get('errmsg', '未知错误')}"
                logger.error(error_msg)
                raise Exception(error_msg)

        except requests.RequestException as e:
            logger.error(f"请求微信API失败: {str(e)}")
            raise Exception(f"请求微信API失败: {str(e)}")

    @classmethod
    def send_subscription_message(
        cls,
        openid: str,
        template_id: str,
        page: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        发送订阅消息

        Args:
            openid: 用户OpenID
            template_id: 模板ID
            page: 跳转页面路径
            data: 消息内容

        Returns:
            bool: 发送是否成功
        """
        try:
            access_token = cls.get_access_token()
            url = f"{cls.WECHAT_API_BASE}/cgi-bin/message/subscribe/send?access_token={access_token}"

            # 构建消息体
            message = {
                "touser": openid,
                "template_id": template_id,
                "page": page,
                "data": data,
                "miniprogram_state": "formal"  # 正式版
            }

            response = requests.post(url, json=message, timeout=10)
            response.raise_for_status()
            result = response.json()

            if result.get("errcode") == 0:
                logger.info(f"订阅消息发送成功: openid={openid}")
                return True
            else:
                logger.error(f"订阅消息发送失败: {result.get('errmsg')}, openid={openid}")
                return False

        except Exception as e:
            logger.error(f"发送订阅消息异常: {str(e)}, openid={openid}")
            return False


class SubscriptionService:
    """订阅服务类"""

    @staticmethod
    def subscribe(
        db: Session,
        user_id: int,
        openid: str,
        template_id: str = None
    ) -> RecommendationSubscription:
        """
        订阅推荐更新消息

        Args:
            db: 数据库会话
            user_id: 用户ID
            openid: 微信OpenID
            template_id: 模板ID（可选，默认使用配置中的模板ID）

        Returns:
            RecommendationSubscription: 订阅记录
        """
        if not template_id:
            template_id = settings.WECHAT_SUBSCRIPTION_TEMPLATE_ID

        # 检查是否已存在订阅
        existing = db.query(RecommendationSubscription).filter(
            RecommendationSubscription.user_id == user_id,
            RecommendationSubscription.template_id == template_id
        ).first()

        if existing:
            # 如果已存在但未激活，则激活
            if not existing.is_active:
                existing.is_active = True
                db.commit()
                db.refresh(existing)
                logger.info(f"重新激活订阅: user_id={user_id}")
            return existing

        # 创建新订阅
        subscription = RecommendationSubscription(
            user_id=user_id,
            openid=openid,
            template_id=template_id,
            is_active=True
        )

        db.add(subscription)
        db.commit()
        db.refresh(subscription)

        logger.info(f"创建订阅成功: user_id={user_id}")
        return subscription

    @staticmethod
    def unsubscribe(
        db: Session,
        user_id: int,
        template_id: str = None
    ) -> bool:
        """
        取消订阅

        Args:
            db: 数据库会话
            user_id: 用户ID
            template_id: 模板ID（可选）

        Returns:
            bool: 是否成功
        """
        if not template_id:
            template_id = settings.WECHAT_SUBSCRIPTION_TEMPLATE_ID

        subscription = db.query(RecommendationSubscription).filter(
            RecommendationSubscription.user_id == user_id,
            RecommendationSubscription.template_id == template_id
        ).first()

        if subscription:
            subscription.is_active = False
            db.commit()
            logger.info(f"取消订阅成功: user_id={user_id}")
            return True

        return False

    @staticmethod
    def get_subscription_status(
        db: Session,
        user_id: int,
        template_id: str = None
    ) -> bool:
        """
        获取订阅状态

        Args:
            db: 数据库会话
            user_id: 用户ID
            template_id: 模板ID（可选）

        Returns:
            bool: 是否已订阅
        """
        if not template_id:
            template_id = settings.WECHAT_SUBSCRIPTION_TEMPLATE_ID

        subscription = db.query(RecommendationSubscription).filter(
            RecommendationSubscription.user_id == user_id,
            RecommendationSubscription.template_id == template_id,
            RecommendationSubscription.is_active == True
        ).first()

        return subscription is not None

    @staticmethod
    def send_recommendation_update(
        db: Session,
        recommendation_id: int,
        title: str,
        update_content: str
    ) -> int:
        """
        发送推荐更新消息给所有订阅用户

        Args:
            db: 数据库会话
            recommendation_id: 推荐ID
            title: 推荐标题
            update_content: 更新内容

        Returns:
            int: 成功发送的数量
        """
        # 获取推荐详情
        from app.models.recommendation import Recommendation
        recommendation = db.query(Recommendation).filter(
            Recommendation.id == recommendation_id
        ).first()

        if not recommendation:
            logger.error(f"推荐不存在: recommendation_id={recommendation_id}")
            return 0

        # 获取所有活跃订阅
        subscriptions = db.query(RecommendationSubscription).filter(
            RecommendationSubscription.is_active == True
        ).all()

        if not subscriptions:
            logger.info("没有活跃订阅，跳过发送")
            return 0

        success_count = 0
        template_id = settings.WECHAT_SUBSCRIPTION_TEMPLATE_ID

        # 根据预测类型确定比赛类型显示文本
        sport_type_map = {
            "football": "足球",
            "basketball": "篮球"
        }
        sport_type = sport_type_map.get(recommendation.prediction_type, "比赛")

        for subscription in subscriptions:
            try:
                # 构建消息数据（字段 key 必须和微信公众平台模板一致）
                # thing1:      类型（最多20字）
                # short_thing4: 标签（最多5字）
                # thing5:      内容摘要（最多20字）
                tag = "推荐"
                if recommendation.prediction_data:
                    matches = recommendation.prediction_data.get('single_matches', [])
                    has_key = any(m.get('is_key_match') for m in matches)
                    has_feat = any(m.get('is_featured') for m in matches)
                    if has_key:
                        tag = "重心"
                    elif has_feat:
                        tag = "精选"
                tag = tag[:5]
                title_short = recommendation.title[:20]
                message_data = {
                    "thing1": {"value": "今日场次已确认发布"},
                    "short_thing4": {"value": tag},
                    "thing5": {"value": title_short}
                }

                # 跳转到推荐列表页
                page = "pages/recommendations/recommendations"

                # 发送消息
                success = WeChatService.send_subscription_message(
                    openid=subscription.openid,
                    template_id=template_id,
                    page=page,
                    data=message_data
                )

                # 记录发送结果
                message_record = SubscriptionMessage(
                    subscription_id=subscription.id,
                    recommendation_id=recommendation_id,
                    openid=subscription.openid,
                    template_id=template_id,
                    page=page,
                    data=message_data,
                    status=MessageStatus.sent if success else MessageStatus.failed,
                    sent_at=datetime.now() if success else None,
                    error_msg=None if success else "发送失败"
                )

                db.add(message_record)

                if success:
                    success_count += 1

            except Exception as e:
                logger.error(f"发送订阅消息异常: subscription_id={subscription.id}, error={str(e)}")
                # 记录失败
                message_record = SubscriptionMessage(
                    subscription_id=subscription.id,
                    recommendation_id=recommendation_id,
                    openid=subscription.openid,
                    template_id=template_id,
                    page="pages/recommendations/recommendations",
                    data={},
                    status=MessageStatus.failed,
                    error_msg=str(e)
                )
                db.add(message_record)

        db.commit()
        logger.info(f"订阅消息发送完成: 总数={len(subscriptions)}, 成功={success_count}")
        return success_count
