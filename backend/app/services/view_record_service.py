"""
浏览记录服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models.view_record import ViewRecord
from app.models.user import User
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ViewRecordService:
    """浏览记录服务类"""

    @staticmethod
    def record_view(
        db: Session,
        user_id: Optional[int],
        recommendation_id: int
    ) -> ViewRecord:
        """
        记录用户浏览推荐（仅登录用户，游客不记录）

        Args:
            db: 数据库会话
            user_id: 用户ID
            recommendation_id: 推荐ID

        Returns:
            ViewRecord: 浏览记录对象
        """
        if user_id is None:
            logger.info("游客浏览不记录")
            return None
        try:
            view_record = ViewRecord(
                user_id=user_id,
                recommendation_id=recommendation_id
            )
            db.add(view_record)
            db.commit()
            db.refresh(view_record)

            label = f"user_id={user_id}" if user_id else "游客"
            logger.info(f"创建浏览记录: {label}, recommendation_id={recommendation_id}")
            return view_record

        except Exception as e:
            db.rollback()
            logger.error(f"记录浏览失败: {str(e)}")
            raise

    @staticmethod
    def get_recommendation_viewers(
        db: Session,
        recommendation_id: int,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[dict], int, int, int]:
        """
        获取查看某个推荐的用户列表（按用户分组，统计浏览次数）

        Returns:
            Tuple[List[dict], int, int, int]: (浏览用户列表, 总浏览次数, 登录用户浏览人数, 游客浏览次数)
        """
        try:
            # 总浏览次数（所有记录，含游客）
            total_views = db.query(func.count(ViewRecord.id)).filter(
                ViewRecord.recommendation_id == recommendation_id
            ).scalar()

            # 游客浏览次数
            guest_view_count = db.query(func.count(ViewRecord.id)).filter(
                ViewRecord.recommendation_id == recommendation_id,
                ViewRecord.user_id.is_(None)
            ).scalar() or 0

            # 登录用户浏览人数（distinct user_id，排除 NULL）
            unique_viewers = db.query(func.count(func.distinct(ViewRecord.user_id))).filter(
                ViewRecord.recommendation_id == recommendation_id,
                ViewRecord.user_id.isnot(None)
            ).scalar()

            # 按用户分组统计每个用户的浏览次数，获取最后浏览时间（仅登录用户）
            subquery = db.query(
                ViewRecord.user_id,
                func.count(ViewRecord.id).label('view_count'),
                func.max(ViewRecord.viewed_at).label('last_viewed_at'),
                func.min(ViewRecord.viewed_at).label('first_viewed_at')
            ).filter(
                ViewRecord.recommendation_id == recommendation_id,
                ViewRecord.user_id.isnot(None)
            ).group_by(
                ViewRecord.user_id
            ).subquery()

            # 关联用户信息
            query = db.query(
                subquery.c.user_id,
                subquery.c.view_count,
                subquery.c.last_viewed_at,
                subquery.c.first_viewed_at,
                User.phone.label('user_phone'),
                User.nickname.label('user_nickname'),
                User.created_at.label('user_created_at'),
                User.role.label('user_role'),
                User.is_paid.label('user_is_paid')
            ).join(
                User,
                subquery.c.user_id == User.id
            )

            # 按最后浏览时间倒序排列
            query = query.order_by(desc(subquery.c.last_viewed_at))

            # 分页
            records = query.offset(
                (page - 1) * page_size
            ).limit(page_size).all()

            # 转换为字典列表
            result = [
                {
                    'user_id': r.user_id,
                    'user_phone': r.user_phone,
                    'user_nickname': r.user_nickname,
                    'user_created_at': r.user_created_at,
                    'view_count': r.view_count,
                    'last_viewed_at': r.last_viewed_at,
                    'first_viewed_at': r.first_viewed_at,
                    'user_role': r.user_role,
                    'user_is_paid': r.user_is_paid
                }
                for r in records
            ]

            if result:
                logger.info(f"查询推荐 {recommendation_id} 的浏览统计: 总浏览次数={total_views}, 登录用户浏览人数={unique_viewers}, 游客浏览次数={guest_view_count}")

            return result, total_views, unique_viewers, guest_view_count

        except Exception as e:
            logger.error(f"查询浏览记录失败: {str(e)}")
            raise

    @staticmethod
    def get_user_view_history(
        db: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[ViewRecord], int]:
        """
        获取用户的浏览历史

        Args:
            db: 数据库会话
            user_id: 用户ID
            page: 页码
            page_size: 每页数量

        Returns:
            Tuple[List[ViewRecord], int]: (浏览记录列表, 总记录数)
        """
        try:
            query = db.query(ViewRecord).filter(
                ViewRecord.user_id == user_id
            )

            total = query.count()

            records = query.order_by(
                desc(ViewRecord.viewed_at)
            ).offset(
                (page - 1) * page_size
            ).limit(page_size).all()

            logger.info(f"查询用户 {user_id} 的浏览历史: 总数={total}")
            return records, total

        except Exception as e:
            logger.error(f"查询用户浏览历史失败: {str(e)}")
            raise
