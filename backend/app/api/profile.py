"""
用户个人资料API端点
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.deps import get_current_user, get_user_flags, require_admin
from app.models.user import User, UserRole
from app.schemas.user import UserInfo, SubscriptionStatus
from app.services.auth import hash_password
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户信息

    返回当前登录用户的详细信息，包括付费状态和角色。
    """
    logger.info(f"用户 {current_user.id} 请求个人信息")

    return UserInfo.model_validate(current_user)


@router.get("/me/subscription", response_model=SubscriptionStatus)
async def get_subscription_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户的订阅状态

    返回用户的付费状态、角色和访问权限信息。
    用于前端判断是否显示升级提示。
    """
    logger.info(f"用户 {current_user.id} 请求订阅状态")

    flags = get_user_flags(current_user)
    is_paid_valid = flags['is_paid_valid']

    # 检查付费用户是否有效（同步 is_paid 标志）
    if is_paid_valid and not current_user.is_paid:
        logger.info(f"用户 {current_user.id} 付费期未过期，恢复 is_paid 标志")
        current_user.is_paid = True
        db.commit()
    elif not is_paid_valid and current_user.is_paid and current_user.paid_end_time:
        logger.info(f"用户 {current_user.id} 付费期已过期，清除付费用户标记")
        current_user.is_paid = False
        db.commit()

    # 管理员或有效付费用户可以查看推荐内容
    can_view_recommendations = flags['has_full_access']

    # 管理员或有效付费用户不显示升级提示
    should_show_upgrade_prompt = not flags['has_full_access']

    return SubscriptionStatus(
        is_paid=current_user.is_paid,
        paid_start_time=current_user.paid_start_time,
        paid_end_time=current_user.paid_end_time,
        role=current_user.role,
        can_view_recommendations=can_view_recommendations,
        should_show_upgrade_prompt=should_show_upgrade_prompt
    )


class SearchUserRequest(BaseModel):
    """搜索用户请求"""
    phone: str


class SetMembershipRequest(BaseModel):
    """设置会员请求"""
    user_id: int
    days: int = 30  # 默认30天
    is_paid: bool = True


@router.post("/search")
async def search_user(
    request: SearchUserRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """管理员：按手机号搜索用户"""
    user = db.query(User).filter(User.phone == request.phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {
        "id": user.id,
        "phone": user.phone,
        "role": user.role,
        "is_paid": user.is_paid,
        "paid_start_time": user.paid_start_time.isoformat() if user.paid_start_time else None,
        "paid_end_time": user.paid_end_time.isoformat() if user.paid_end_time else None,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }


@router.post("/membership")
async def set_membership(
    request: SetMembershipRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """管理员：开通/修改会员"""
    target_user = db.query(User).filter(User.id == request.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    now = datetime.now()
    if request.is_paid:
        # 未到期续费：从到期日延后；已到期/新开通：从今天开始
        if target_user.paid_end_time and target_user.paid_end_time > now:
            start = target_user.paid_end_time
            remaining_days = (target_user.paid_end_time - now).days
            msg = f"续费成功！原有剩余{remaining_days}天 + 新增{request.days}天，到期 {start + timedelta(days=request.days):%Y-%m-%d}"
        else:
            start = now
            target_user.paid_start_time = now
            msg = f"会员已开通，到期 {start + timedelta(days=request.days):%Y-%m-%d}"
        target_user.is_paid = True
        target_user.paid_end_time = start + timedelta(days=request.days)
    else:
        # 取消会员
        target_user.is_paid = False
        target_user.paid_start_time = None
        target_user.paid_end_time = None
        msg = "会员已取消"

    db.commit()
    logger.info(f"管理员 {current_user.id} 为 {target_user.phone} 设置会员: {msg}")

    return {
        "success": True,
        "message": msg,
        "user_id": target_user.id,
        "phone": target_user.phone,
        "is_paid": target_user.is_paid,
        "paid_start_time": target_user.paid_start_time.isoformat() if target_user.paid_start_time else None,
        "paid_end_time": target_user.paid_end_time.isoformat() if target_user.paid_end_time else None
    }


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    user_id: int


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """管理员：重置用户密码为默认密码 123qwe（请提示用户登录后自行修改）"""
    target_user = db.query(User).filter(User.id == request.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    new_pwd = "123qwe"  # 固定默认密码（含字母+数字，符合登录校验规则）
    target_user.password_hash = hash_password(new_pwd)
    target_user.token_version += 1
    db.commit()
    logger.info(f"管理员 {current_user.id} 重置用户 {target_user.phone} 的密码")

    return {
        "success": True,
        "message": f"密码已重置为默认密码：{new_pwd}（请提示用户登录后自行修改）",
        "phone": target_user.phone,
        "new_password": new_pwd
    }


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    new_password: str


class UpdateNicknameRequest(BaseModel):
    """修改昵称请求"""
    nickname: str


@router.put("/me/nickname")
async def update_nickname(
    request: UpdateNicknameRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """用户修改自己的昵称"""
    nickname = request.nickname.strip()
    if not nickname:
        raise HTTPException(status_code=400, detail="昵称不能为空")
    if len(nickname) > 20:
        raise HTTPException(status_code=400, detail="昵称最多20个字")

    current_user.nickname = nickname
    db.commit()
    logger.info(f"用户 {current_user.phone} 修改昵称为: {nickname}")

    return {"success": True, "nickname": nickname}


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """用户修改自己的密码（已登录，无需旧密码）"""
    import re
    pwd = request.new_password
    if len(pwd) < 6 or len(pwd) > 20:
        raise HTTPException(status_code=400, detail="密码长度为 6-20 位")
    if not re.search(r'[a-zA-Z]', pwd) or not re.search(r'\d', pwd):
        raise HTTPException(status_code=400, detail="密码需同时包含字母和数字")

    current_user.password_hash = hash_password(pwd)
    current_user.token_version += 1
    db.commit()
    logger.info(f"用户 {current_user.phone} 修改了密码")

    return {"success": True, "message": "密码修改成功，请重新登录"}
