"""
推荐服务
"""
import logging
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from app.models.recommendation import Recommendation, RecommendationStatus
from app.schemas.recommendation import RecommendationCreate, RecommendationUpdate

logger = logging.getLogger(__name__)


class RecommendationService:
    """推荐业务逻辑服务"""

    @staticmethod
    def get_active_recommendations(
        db: Session,
        prediction_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[List[Recommendation], int]:
        """
        获取活跃的推荐列表（分页）

        Args:
            db: 数据库会话
            prediction_type: 预测类型过滤（可选）
            page: 页码（从1开始）
            page_size: 每页数量（最大50）

        Returns:
            (推荐列表, 总数) 的元组
        """
        # 限制每页最大数量
        page_size = min(page_size, 50)
        offset = (page - 1) * page_size

        # 基础查询：活跃推荐（含已标结果但未归档的）
        query = db.query(Recommendation).filter(
            Recommendation.status == RecommendationStatus.ACTIVE
        )

        # 预测类型过滤
        if prediction_type:
            query = query.filter(Recommendation.prediction_type == prediction_type)

        # 按创建时间倒序排列
        query = query.order_by(Recommendation.created_at.desc())

        # 获取总数
        total = query.count()

        # 分页查询
        recommendations = query.offset(offset).limit(page_size).all()

        return recommendations, total

    @staticmethod
    def get_all_recommendations(
        db: Session,
        status: Optional[str] = None,
        prediction_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[List[Recommendation], int]:
        """
        获取所有推荐列表（管理员用，分页）

        Args:
            db: 数据库会话
            status: 状态过滤（可选：active/completed/inactive）
            prediction_type: 预测类型过滤（可选）
            page: 页码（从1开始）
            page_size: 每页数量（最大50）

        Returns:
            (推荐列表, 总数) 的元组
        """
        # 限制每页最大数量
        page_size = min(page_size, 50)
        offset = (page - 1) * page_size

        # 基础查询：未归档且未删除的推荐
        query = db.query(Recommendation).filter(
            Recommendation.archived_at.is_(None),
            Recommendation.status != RecommendationStatus.INACTIVE
        )

        # 状态过滤
        if status:
            if status == 'active':
                query = query.filter(Recommendation.status == RecommendationStatus.ACTIVE)
            elif status == 'completed':
                query = query.filter(Recommendation.status == RecommendationStatus.COMPLETED)
            elif status == 'inactive':
                # 如果明确要查询已删除的，则移除 inactive 过滤
                query = db.query(Recommendation).filter(
                    Recommendation.archived_at.is_(None),
                    Recommendation.status == RecommendationStatus.INACTIVE
                )

        # 预测类型过滤
        if prediction_type:
            query = query.filter(Recommendation.prediction_type == prediction_type)

        # 按创建时间倒序排列
        query = query.order_by(Recommendation.created_at.desc())

        # 获取总数
        total = query.count()

        # 分页查询
        recommendations = query.offset(offset).limit(page_size).all()

        return recommendations, total

    @staticmethod
    def get_recommendation_by_id(
        db: Session,
        recommendation_id: int
    ) -> Optional[Recommendation]:
        """
        根据ID获取推荐

        Args:
            db: 数据库会话
            recommendation_id: 推荐ID

        Returns:
            推荐对象或None
        """
        return db.query(Recommendation).filter(
            Recommendation.id == recommendation_id
        ).first()

    @staticmethod
    def create_recommendation(
        db: Session,
        recommendation_data: RecommendationCreate,
        created_by_id: int
    ) -> Recommendation:
        """
        创建新推荐（由管理员调用）

        Args:
            db: 数据库会话
            recommendation_data: 推荐数据
            created_by_id: 创建者ID（管理员）

        Returns:
            创建的推荐对象
        """
        # 将Pydantic模型转为字典，确保嵌套模型也被转换
        recommendation_dict = recommendation_data.model_dump()

        logger.info(f"Creating recommendation with data: {json.dumps(recommendation_dict, ensure_ascii=False, indent=2)}")
        logger.debug(f"prediction_data type: {type(recommendation_dict['prediction_data'])}")
        logger.debug(f"prediction_data content: {json.dumps(recommendation_dict['prediction_data'], ensure_ascii=False, indent=2)}")

        # 创建推荐对象
        recommendation = Recommendation(
            created_by_id=created_by_id,
            prediction_type=recommendation_dict['prediction_type'],
            title=recommendation_dict['title'],
            promotion_title=recommendation_dict.get('promotion_title'),
            prediction_data=recommendation_dict['prediction_data'],  # 这应该已经是字典了
            analysis_text=recommendation_dict['analysis_text'],
            status=RecommendationStatus.ACTIVE
        )

        db.add(recommendation)
        db.commit()
        db.refresh(recommendation)

        logger.info(f"Created recommendation with id: {recommendation.id}")
        logger.debug(f"Saved prediction_data: {json.dumps(recommendation.prediction_data, ensure_ascii=False, indent=2)}")

        return recommendation

    @staticmethod
    def update_recommendation(
        db: Session,
        recommendation_id: int,
        recommendation_data: RecommendationUpdate
    ) -> Optional[Recommendation]:
        """
        更新推荐

        Args:
            db: 数据库会话
            recommendation_id: 推荐ID
            recommendation_data: 更新数据

        Returns:
            更新后的推荐对象或None
        """
        recommendation = db.query(Recommendation).filter(
            Recommendation.id == recommendation_id
        ).first()

        if not recommendation:
            return None

        # 获取更新数据
        update_data = recommendation_data.model_dump(exclude_unset=True)

        # 更新字段
        for field, value in update_data.items():
            setattr(recommendation, field, value)

        db.commit()
        db.refresh(recommendation)

        return recommendation

    @staticmethod
    def delete_recommendation(
        db: Session,
        recommendation_id: int
    ) -> bool:
        """
        删除推荐（软删除：设置为inactive）

        Args:
            db: 数据库会话
            recommendation_id: 推荐ID

        Returns:
            是否成功删除
        """
        recommendation = db.query(Recommendation).filter(
            Recommendation.id == recommendation_id
        ).first()

        if not recommendation:
            return False

        # 硬删除
        db.delete(recommendation)
        db.commit()

        return True
