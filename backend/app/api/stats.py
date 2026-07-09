from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date
import random
import logging

logger = logging.getLogger(__name__)

from ..database import get_db
from ..deps import get_current_user, get_user_flags
from ..models.user import User

router = APIRouter()


# ===== 社会证明（营销展示）配置 =====
# 目的：突出"用的人多、会员多"。均为展示用造数，非真实统计。
_LAUNCH_DATE = date(2026, 1, 1)   # 上线基准日（累计会员从此日起算）
_MEMBER_BASE = 3200               # 会员基数
_MEMBER_PER_DAY = 8               # 每日净增会员（用于连续累加，保证只增不减）
_VIEW_BASE = 600                  # 今日分析次数基数
_VIEW_PER_MIN = 0.7               # 今日分析每分钟增量


@router.get("/social-proof")
async def get_social_proof(db: Session = Depends(get_db)):
    """
    实时热度（社会证明，营销展示用，非真实统计）。

    - today_views  今日分析次数：当天内随时间增长，午夜归零（"今日"语义正确）
    - total_users  累计会员数：基于上线基准日连续累加，跨天只增不减
    """
    try:
        now = datetime.now()
        minutes_today = now.hour * 60 + now.minute

        # 今日分析次数：当天增长 + 轻微抖动（按分钟播种，同一分钟内刷新稳定）
        rng = random.Random(now.year * 1000 + now.timetuple().tm_yday * 24 * 60 + minutes_today)
        today_views = _VIEW_BASE + int(minutes_today * _VIEW_PER_MIN) + rng.randint(0, 8)

        # 累计会员：上线天数 + 当天进度，乘以日增 → 连续单调增长，午夜不回落
        days_elapsed = max(0, (now.date() - _LAUNCH_DATE).days)
        progress = days_elapsed + minutes_today / 1440.0
        total_users = _MEMBER_BASE + int(progress * _MEMBER_PER_DAY)

        return {
            "today_views": today_views,
            "total_users": total_users
        }
    except Exception as e:
        logger.error(f"获取热度数据失败: {e}")
        return {
            "today_views": 0,
            "total_users": 0
        }


@router.get("/user-stats")
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户统计数据(需要认证)
    """
    try:
        # 统一使用 get_user_flags 获取权限
        flags = get_user_flags(current_user)
        is_paid = flags['is_paid_valid']

        # 计算剩余天数
        remaining_days = 0
        if current_user.paid_end_time:
            delta = current_user.paid_end_time - datetime.now()
            remaining_days = max(0, delta.days)

        # 获取用户查看的推荐数量
        from ..models.view_record import ViewRecord
        view_count = db.query(ViewRecord).filter(
            ViewRecord.user_id == current_user.id
        ).count()

        return {
            "is_paid": is_paid,
            "remaining_days": remaining_days,
            "view_count": view_count,
            "paid_end_time": current_user.paid_end_time.isoformat() if current_user.paid_end_time else None
        }
    except Exception as e:
        logger.error(f"获取用户统计数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取用户统计数据失败: {str(e)}")