"""
昨日战绩相关API端点
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from app.database import get_db
from app.deps import require_admin, get_current_user, get_current_user_optional
from app.models.user import User
from app.models.daily_achievement import DailyAchievement
from app.schemas.daily_achievement import (
    DailyAchievementCreate,
    DailyAchievementResponse
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/daily-achievements", tags=["daily-achievements"])


@router.get("/latest", response_model=Optional[DailyAchievementResponse])
async def get_latest_achievement(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    获取最新的昨日战绩（用于首页banner显示，游客也可访问）

    返回最近一条 is_active=true 的战绩
    """
    achievement = db.query(DailyAchievement).filter(
        DailyAchievement.is_active == True
    ).order_by(
        DailyAchievement.date.desc()
    ).first()

    return achievement


@router.get("", response_model=List[DailyAchievementResponse])
async def get_achievements(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(10, ge=1, le=50, description="返回记录数"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取昨日战绩列表（管理员可查看所有，普通用户只能查看激活的）
    """
    query = db.query(DailyAchievement)

    # 非管理员只能看激活的
    if current_user.role.value != 'admin':
        query = query.filter(DailyAchievement.is_active == True)

    achievements = query.order_by(
        DailyAchievement.date.desc()
    ).offset(skip).limit(limit).all()

    return achievements


@router.get("/{achievement_id}", response_model=DailyAchievementResponse)
async def get_achievement(
    achievement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定的昨日战绩详情
    """
    achievement = db.query(DailyAchievement).filter(
        DailyAchievement.id == achievement_id
    ).first()

    if not achievement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="战绩不存在"
        )

    # 非管理员只能查看激活的战绩
    if current_user.role.value != 'admin' and not achievement.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看此战绩"
        )

    return achievement


@router.post("", response_model=DailyAchievementResponse, status_code=status.HTTP_201_CREATED)
async def create_achievement(
    achievement_data: DailyAchievementCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    创建昨日战绩（仅管理员）
    """
    logger.info(f"管理员 {current_user.id} 创建昨日战绩: {achievement_data.date}")

    # 检查日期是否已存在
    existing = db.query(DailyAchievement).filter(
        DailyAchievement.date == achievement_data.date
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"日期 {achievement_data.date} 的战绩已存在，请使用更新接口"
        )

    # 计算准确率
    if achievement_data.total_count > 0:
        accuracy_rate = (achievement_data.win_count / achievement_data.total_count) * 100
    else:
        accuracy_rate = 0.0

    # 转换 highlights 为 JSON
    highlights_json = None
    if achievement_data.highlights:
        highlights_json = achievement_data.highlights

    # 创建战绩
    achievement = DailyAchievement(
        date=achievement_data.date,
        title=achievement_data.title,
        subtitle=achievement_data.subtitle,
        total_count=achievement_data.total_count,
        win_count=achievement_data.win_count,
        accuracy_rate=Decimal(str(round(accuracy_rate))),  # 四舍五入取整
        highlights=highlights_json,
        description=achievement_data.description,
        banner_image=achievement_data.banner_image,
        is_active=achievement_data.is_active,
        created_by_id=current_user.id
    )

    db.add(achievement)
    db.commit()
    db.refresh(achievement)

    logger.info(f"昨日战绩创建成功: ID={achievement.id}, 日期={achievement.date}")
    return achievement


@router.put("/{achievement_id}", response_model=DailyAchievementResponse)
async def update_achievement(
    achievement_id: int,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    更新昨日战绩（仅管理员）
    """
    logger.info(f"管理员 {current_user.id} 更新昨日战绩: ID={achievement_id}")

    body = await request.json()
    logger.info(f"接收到的原始数据: {body}")

    achievement = db.query(DailyAchievement).filter(
        DailyAchievement.id == achievement_id
    ).first()

    if not achievement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="战绩不存在"
        )

    update_data = {}

    if 'date' in body and body['date'] is not None:
        try:
            if isinstance(body['date'], str):
                update_data['date'] = datetime.strptime(body['date'], '%Y-%m-%d').date()
            else:
                update_data['date'] = body['date']
        except Exception as e:
            logger.error(f"日期解析失败: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="日期格式错误，应为 YYYY-MM-DD")

    if 'title' in body and body['title'] is not None:
        update_data['title'] = body['title']

    if 'subtitle' in body:
        update_data['subtitle'] = body['subtitle']

    if 'total_count' in body and body['total_count'] is not None:
        update_data['total_count'] = int(body['total_count'])

    if 'win_count' in body and body['win_count'] is not None:
        update_data['win_count'] = int(body['win_count'])

    if 'highlights' in body:
        update_data['highlights'] = body['highlights']

    if 'description' in body:
        update_data['description'] = body['description']

    if 'banner_image' in body:
        update_data['banner_image'] = body['banner_image']

    if 'is_active' in body and body['is_active'] is not None:
        update_data['is_active'] = bool(body['is_active'])

    logger.info(f"处理后的更新数据: {update_data}")

    if 'date' in update_data and update_data['date'] != achievement.date:
        existing = db.query(DailyAchievement).filter(
            DailyAchievement.date == update_data['date'],
            DailyAchievement.id != achievement_id
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"日期 {update_data['date']} 已被其他战绩使用")

    if 'total_count' in update_data or 'win_count' in update_data:
        total = update_data.get('total_count', achievement.total_count)
        wins = update_data.get('win_count', achievement.win_count)
        update_data['accuracy_rate'] = Decimal(str(round((wins / total) * 100))) if total > 0 else Decimal('0')

    for key, value in update_data.items():
        setattr(achievement, key, value)

    db.commit()
    db.refresh(achievement)

    logger.info(f"昨日战绩更新成功: ID={achievement.id}")
    return achievement


@router.delete("/{achievement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_achievement(
    achievement_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    删除昨日战绩（仅管理员）
    """
    logger.info(f"管理员 {current_user.id} 删除昨日战绩: ID={achievement_id}")

    achievement = db.query(DailyAchievement).filter(
        DailyAchievement.id == achievement_id
    ).first()

    if not achievement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="战绩不存在"
        )

    db.delete(achievement)
    db.commit()

    logger.info(f"昨日战绩删除成功: ID={achievement_id}")
    return None
