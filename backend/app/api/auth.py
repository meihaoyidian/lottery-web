"""
认证相关API路由（Web 端）
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, TokenResponse, UserInfo, GuidePopupStatus
from app.services.auth import hash_password, verify_password, create_access_token
from app.deps import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=UserInfo, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    用户注册（手机号 + 密码）

    Raises:
        HTTPException: 如果手机号已被注册
    """
    # 检查手机号是否已存在
    existing_user = db.query(User).filter(User.phone == user_data.phone).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该手机号已被注册"
        )

    # 创建新用户
    new_user = User(
        phone=user_data.phone,
        password_hash=hash_password(user_data.password),
        nickname=user_data.nickname or f"用户{user_data.phone[-4:]}"
    )

    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        logger.error(f"注册提交失败: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")

    return new_user


@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    用户登录（手机号 + 密码）

    Raises:
        HTTPException: 如果手机号或密码错误
    """
    # 查询用户
    user = db.query(User).filter(User.phone == user_data.phone).first()
    if not user:
        # 手机号未注册：返回专用错误码，前端可引导去注册
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该手机号未注册，请先注册"
        )

    # 验证密码
    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="密码错误，请重新输入"
        )

    # 递增 token_version，使旧 token 失效
    user.token_version += 1
    db.commit()
    db.refresh(user)

    # 创建访问令牌（sub 必须是字符串，ver 为 token 版本）
    access_token = create_access_token(data={"sub": str(user.id), "ver": user.token_version})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/guide-popup-status", response_model=GuidePopupStatus)
async def get_guide_popup_status(
    current_user: User = Depends(get_current_user)
):
    """
    获取引导弹窗状态

    判断逻辑：付费用户不弹窗，非付费用户每次登录都弹窗
    """
    return {
        "should_show_popup": not current_user.is_paid,
        "is_paid_user": current_user.is_paid,
    }
