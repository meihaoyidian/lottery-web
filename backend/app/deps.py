"""
FastAPI 依赖注入
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User, UserRole
from app.services.auth import decode_access_token
from app.config import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# HTTP Bearer 认证方案
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


def get_user_flags(user: Optional[User]) -> dict:
    """
    返回用户身份标识字典，所有 API 层统一使用此函数判定用户权限。

    返回字段:
        is_admin:          管理员
        is_paid_valid:     付费期内 (paid_end_time 未过期)
        has_full_access:   admin | paid 任一满足
    """
    if user is None:
        return {
            'is_admin': False,
            'is_paid_valid': False,
            'has_full_access': False,
        }

    now = datetime.now()
    is_admin = user.role == UserRole.admin
    is_paid_valid = bool(user.paid_end_time and now < user.paid_end_time)
    has_full_access = is_admin or is_paid_valid

    return {
        'is_admin': is_admin,
        'is_paid_valid': is_paid_valid,
        'has_full_access': has_full_access,
    }


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前登录用户

    Args:
        credentials: HTTP认证凭据
        db: 数据库会话

    Returns:
        当前用户对象

    Raises:
        HTTPException: 如果token无效或用户不存在
    """
    # 获取token
    token = credentials.credentials
    logger.info(f"收到token: {token[:30]}...")

    # 解码token
    payload = decode_access_token(token)
    if payload is None:
        logger.error("Token解码失败")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"Token解码成功: {payload}")

    # 获取用户ID（从字符串转换为整数）
    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        logger.error("Token中没有用户ID")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        logger.error(f"用户ID格式错误: {user_id_str}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"查询用户ID: {user_id}")

    # 查询用户
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        logger.error(f"用户不存在: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证 token_version
    token_version = payload.get("ver")
    if token_version is None or token_version != user.token_version:
        logger.error(f"Token 版本不匹配: token_ver={token_version}, user_ver={user.token_version}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录已过期，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"用户验证成功: {user.nickname}")
    return user


async def require_paid_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    要求付费用户权限（管理员自动视为付费用户）

    Args:
        current_user: 当前用户

    Returns:
        当前用户对象

    Raises:
        HTTPException: 如果用户不是付费用户
    """
    # 管理员自动视为付费用户
    if current_user.role == UserRole.admin:
        return current_user

    # 检查付费用户是否有效（只检查 paid_end_time，不依赖 is_paid 标志）
    if current_user.paid_end_time:
        if datetime.now() < current_user.paid_end_time:
            return current_user

    logger.warning(f"用户 {current_user.id} 尝试访问付费内容但未付费")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="此功能仅限付费用户访问，请升级账户",
    )


async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    要求管理员权限

    Args:
        current_user: 当前用户

    Returns:
        当前用户对象

    Raises:
        HTTPException: 如果用户不是管理员
    """
    if current_user.role != UserRole.admin:
        logger.warning(f"用户 {current_user.id} 尝试访问管理员功能")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="此功能仅限管理员访问",
        )

    logger.info(f"管理员 {current_user.id} 访问管理功能")
    return current_user


async def require_history_access(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    要求推荐记录访问权限

    所有登录用户都可以访问。

    Args:
        current_user: 当前用户

    Returns:
        当前用户对象
    """
    return current_user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    可选的用户认证（审核模式和游客模式使用）

    在审核模式下，如果未提供 token 则返回 None
    在正常模式下，如果未提供 token 则返回 None（游客模式）
    如果提供了 token，则进行正常认证流程

    Args:
        credentials: 可选的HTTP认证凭据
        db: 数据库会话

    Returns:
        当前用户对象或 None（审核模式或游客模式下）

    Raises:
        HTTPException: 如果提供了无效的认证凭据
    """
    # 审核模式：允许匿名访问
    if settings.REVIEW_MODE:
        if credentials is None:
            logger.info("审核模式：允许匿名访问")
            return None

    # 游客模式：允许匿名访问（不强制要求认证）
    if credentials is None:
        logger.info("游客模式：允许匿名访问")
        return None

    # 有认证凭据，进行正常认证流程；失败则返回 None（不强制要求登录）
    token = credentials.credentials

    payload = decode_access_token(token)
    if payload is None:
        return None

    user_id_str = payload.get("sub")
    if user_id_str is None:
        return None

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        return None

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return None

    token_version = payload.get("ver")
    if token_version is None or token_version != user.token_version:
        return None

    return user
