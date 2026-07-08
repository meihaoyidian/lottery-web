"""
认证相关API路由
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel as PydanticBaseModel
from app.database import get_db
from app.models.user import User, TrialUsage
from app.schemas.user import UserRegister, UserLogin, TokenResponse, UserInfo, WeChatLoginRequest, WeChatLoginResponse, GuidePopupStatus
from app.services.auth import hash_password, verify_password, create_access_token
from app.config import settings
from app.deps import get_current_user, get_user_flags
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=UserInfo, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    用户注册

    Args:
        user_data: 用户注册信息
        db: 数据库会话

    Returns:
        新创建的用户信息

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
    db.commit()
    db.refresh(new_user)

    # 通过微信 code 获取 openid，用于防重复薅体验会员
    openid = None
    if user_data.code:
        try:
            wechat_url = "https://api.weixin.qq.com/sns/jscode2session"
            params = {
                "appid": settings.WECHAT_APPID,
                "secret": settings.WECHAT_SECRET,
                "js_code": user_data.code,
                "grant_type": "authorization_code"
            }
            resp = requests.get(wechat_url, params=params, timeout=10, verify=False)
            result = resp.json()
            if "openid" in result:
                openid = result["openid"]
                # 检查该 openid 是否已被其他用户占用，避免唯一键冲突
                existing_openid = db.query(User).filter(
                    User.openid == openid
                ).first()
                if not existing_openid:
                    new_user.openid = openid
                else:
                    logger.info(
                        f"用户 {new_user.id}({new_user.phone}) openid={openid} "
                        f"已被用户 {existing_openid.id}({existing_openid.phone}) 占用，跳过绑定"
                    )
        except Exception as e:
            logger.warning(f"获取 openid 失败: {e}")

    # 判断是否应该赠送体验会员（查 trial_usage 表，永久保留，删号不丢）
    should_grant_trial = True
    if openid:
        existing_usage = db.query(TrialUsage).filter(
            TrialUsage.openid == openid
        ).first()
        if existing_usage:
            should_grant_trial = False
            logger.info(
                f"用户 {new_user.id}({new_user.phone}) openid={openid} "
                f"已有体验记录（{existing_usage.created_at}），跳过赠送"
            )

    if should_grant_trial:
        now = datetime.now()
        new_user.is_trial_user = True
        new_user.has_used_trial = True
        new_user.trial_start_time = now
        new_user.trial_end_time = (now + timedelta(days=1)).replace(hour=13, minute=30, second=0, microsecond=0)

        # 永久记录 openid 已使用过体验（存 trial_usage，删号也不丢）
        if openid and not existing_usage:
            db.add(TrialUsage(openid=openid))

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
    用户登录

    Args:
        user_data: 用户登录信息
        db: 数据库会话

    Returns:
        访问令牌和用户信息

    Raises:
        HTTPException: 如果手机号或密码错误
    """
    # 查询用户
    user = db.query(User).filter(User.phone == user_data.phone).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手机号或密码错误"
        )

    # 验证密码
    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手机号或密码错误"
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


class SilentLoginRequest(PydanticBaseModel):
    code: str
    phone: Optional[str] = None      # 回退匹配：老用户可能没 openid
    user_id: Optional[int] = None    # 回退匹配：优先级高于 phone

@router.post("/silent-login", response_model=TokenResponse)
async def silent_login(
    req: SilentLoginRequest,
    db: Session = Depends(get_db)
):
    """
    静默登录：用微信 code 换 openid，自动查/建用户，返回 token。
    新用户自动赠送 1 天体验。
    """
    code = req.code
    if not code or not code.strip():
        raise HTTPException(status_code=400, detail="code 不能为空")

    # 1. code 换 openid
    openid = None
    try:
        wechat_url = "https://api.weixin.qq.com/sns/jscode2session"
        params = {
            "appid": settings.WECHAT_APPID,
            "secret": settings.WECHAT_SECRET,
            "js_code": code,
            "grant_type": "authorization_code"
        }
        resp = requests.get(wechat_url, params=params, timeout=10, verify=False)
        result = resp.json()
        openid = result.get("openid")
    except Exception as e:
        logger.error(f"静默登录获取 openid 失败: {e}")
        raise HTTPException(status_code=500, detail="微信授权失败")

    if not openid:
        raise HTTPException(status_code=400, detail="获取 openid 失败")

    # 2. 查已有用户（优先 openid）
    user = db.query(User).filter(User.openid == openid).first()

    # 3. openid 没查到？回退匹配：通过 user_id 或 phone 找老用户并补绑 openid
    if not user and (req.user_id or req.phone):
        query = db.query(User)
        if req.user_id:
            query = query.filter(User.id == req.user_id)
        elif req.phone:
            query = query.filter(User.phone == req.phone)
        fallback = query.first()
        if fallback and not fallback.openid:
            fallback.openid = openid
            db.commit()
            db.refresh(fallback)
            user = fallback
            logger.info(f"静默登录回退匹配: user_id={req.user_id} phone={req.phone} → 老用户 id={user.id}，已补绑 openid")

    is_new = user is None

    if is_new:
        # 4. 新用户：创建账户
        phone = f"wx_{openid[:10]}"
        # 如果有同 phone 的旧记录（极小概率），加随机后缀
        if db.query(User).filter(User.phone == phone).first():
            import random
            phone = f"wx_{openid[:8]}{random.randint(100,999)}"

        user = User(
            phone=phone,
            password_hash=hash_password(openid[-12:]),  # openid 尾部当密码
            nickname=f"用户{phone[-4:]}",
            openid=openid
        )
        db.add(user)
        db.flush()

        # 新用户送 1 天体验（同微信号只送一次）
        existing_usage = db.query(TrialUsage).filter(TrialUsage.openid == openid).first()
        if not existing_usage:
            now = datetime.now()
            user.is_trial_user = True
            user.has_used_trial = True
            user.trial_start_time = now
            user.trial_end_time = (now + timedelta(days=1)).replace(hour=13, minute=30, second=0, microsecond=0)
            # TrialUsage 和用户写在同一个事务，防止用户已创建但 TrialUsage 写入失败
            db.add(TrialUsage(openid=openid))

        db.commit()
        db.refresh(user)
        logger.info(f"静默登录创建新用户: id={user.id} phone={user.phone} openid={openid}")
    else:
        logger.info(f"静默登录已有用户: id={user.id} phone={user.phone}")

    # 4. 发 token
    user.token_version += 1
    db.commit()
    db.refresh(user)

    access_token = create_access_token(data={"sub": str(user.id), "ver": user.token_version})
    return {"access_token": access_token, "token_type": "bearer", "user": user}


@router.post("/bind-openid", response_model=dict)
class BindOpenidRequest(PydanticBaseModel):
    code: str

async def bind_openid(
    req: BindOpenidRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """绑定 openid 到当前用户（已有 token 的老用户补 openid）"""
    code = req.code
    openid = None
    try:
        params = {"appid": settings.WECHAT_APPID, "secret": settings.WECHAT_SECRET,
                  "js_code": code, "grant_type": "authorization_code"}
        resp = requests.get("https://api.weixin.qq.com/sns/jscode2session", params=params, timeout=10)
        result = resp.json()
        openid = result.get("openid")
    except Exception as e:
        logger.error(f"绑定 openid 失败: {e}")
        raise HTTPException(status_code=500, detail="微信授权失败")

    if not openid:
        raise HTTPException(status_code=400, detail="获取 openid 失败")

    # 检查当前用户是否已有 openid
    if current_user.openid:
        return {"message": "已绑定", "openid": current_user.openid}

    # 检查 openid 是否已被其他人占用
    conflict = db.query(User).filter(User.openid == openid, User.id != current_user.id).first()
    if conflict:
        logger.warning(f"openid={openid} 已被用户 {conflict.id} 占用")
        raise HTTPException(status_code=409, detail="该微信已绑定其他账户")

    current_user.openid = openid
    db.commit()
    logger.info(f"用户 {current_user.id} 绑定 openid={openid}")
    return {"message": "绑定成功", "openid": openid}


@router.post("/wechat-login", response_model=WeChatLoginResponse)
async def wechat_login(
    login_data: WeChatLoginRequest,
    db: Session = Depends(get_db)
):
    """
    微信登录

    Args:
        login_data: 微信登录信息（code 和 phone）
        db: 数据库会话

    Returns:
        openid 和用户信息（如果用户已注册）

    Raises:
        HTTPException: 如果微信登录失败
    """
    # 调用微信 API 获取 openid
    wechat_url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": settings.WECHAT_APPID,
        "secret": settings.WECHAT_SECRET,
        "js_code": login_data.code,
        "grant_type": "authorization_code"
    }

    try:
        response = requests.get(wechat_url, params=params, timeout=10)
        result = response.json()

        if "errcode" in result and result["errcode"] != 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"微信登录失败: {result.get('errmsg', '未知错误')}"
            )

        openid = result.get("openid")
        if not openid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="获取 openid 失败"
            )

    except requests.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"微信 API 请求失败: {str(e)}"
        )

    # 查找用户（通过手机号）
    user = db.query(User).filter(User.phone == login_data.phone).first()

    if user:
        # 更新用户的 openid
        user.openid = openid
        # 递增 token_version，使旧 token 失效
        user.token_version += 1
        db.commit()
        db.refresh(user)

        # 创建访问令牌
        access_token = create_access_token(data={"sub": str(user.id), "ver": user.token_version})

        return {
            "openid": openid,
            "user": user,
            "access_token": access_token,
            "token_type": "bearer"
        }
    else:
        # 用户未注册,仅返回 openid
        return {
            "openid": openid,
            "user": None,
            "access_token": None
        }


# ===== Web 端登录 =====

class WebSendCodeRequest(PydanticBaseModel):
    phone: str

@router.post("/web/send-code")
async def web_send_code(req: WebSendCodeRequest):
    """
    Web 端发送短信验证码。
    当前为开发模式，固定验证码 0000。
    """
    logger.info(f"Web 端发送验证码: phone={req.phone}")
    return {"message": "验证码已发送（开发模式：0000）", "dev_code": "0000"}


class WebLoginRequest(PydanticBaseModel):
    phone: str
    code: str

@router.post("/web/login", response_model=TokenResponse)
async def web_login(
    req: WebLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Web 端登录：手机号 + 验证码。
    已有用户直接登录，新用户自动创建并赠送 1 天体验。
    """
    # 验证码校验（开发模式固定 0000）
    if req.code != "0000":
        raise HTTPException(status_code=400, detail="验证码错误")

    # 查用户
    user = db.query(User).filter(User.phone == req.phone).first()

    if user:
        logger.info(f"Web 登录已有用户: id={user.id} phone={user.phone}")
    else:
        # 新用户创建
        user = User(
            phone=req.phone,
            password_hash=hash_password(req.phone[-8:]),
            nickname=f"用户{req.phone[-4:]}"
        )
        db.add(user)
        db.flush()

        # 新用户赠送 1 天体验
        now = datetime.now()
        user.is_trial_user = True
        user.has_used_trial = True
        user.trial_start_time = now
        user.trial_end_time = (now + timedelta(days=1)).replace(hour=13, minute=30, second=0, microsecond=0)

        db.commit()
        db.refresh(user)
        logger.info(f"Web 登录创建新用户: id={user.id} phone={user.phone}")

    # 发 token
    user.token_version += 1
    db.commit()
    db.refresh(user)

    access_token = create_access_token(data={"sub": str(user.id), "ver": user.token_version})
    return {"access_token": access_token, "token_type": "bearer", "user": user}


@router.get("/guide-popup-status", response_model=GuidePopupStatus)
async def get_guide_popup_status(
    current_user: User = Depends(get_current_user)
):
    """
    获取引导弹窗状态

    判断逻辑：
    1. 付费用户（is_paid=1）不弹窗
    2. 体验用户（trial_end_time 存在且未过期）不弹窗
    3. 其他普通用户每次登录都弹窗
    """
    flags = get_user_flags(current_user)
    is_trial_valid = flags['is_trial_valid']
    should_show_popup = not current_user.is_paid and not is_trial_valid

    return {
        "should_show_popup": should_show_popup,
        "is_paid_user": current_user.is_paid,
        "is_trial_user": current_user.is_trial_user,
    }

