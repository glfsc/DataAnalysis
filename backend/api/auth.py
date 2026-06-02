"""
用户认证 API 路由
提供注册、登录、密码找回、用户信息管理接口
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models.schemas import (
    RegisterRequest,
    LoginRequest,
    RecoverRequest,
    UpdateUserRequest,
    AuthResponse,
    UserInfo,
    SuccessResponse,
)
from services.auth_service import (
    register_user,
    login_user,
    recover_password,
    get_user_info,
    update_user_info,
    logout_user,
    get_current_user,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["用户认证"])


def get_auth_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    认证依赖：从 Authorization 头提取令牌并返回当前用户
    未登录返回 None（不强制要求登录）
    """
    if not authorization:
        return None
    # 解析 Bearer token
    token = authorization.replace("Bearer ", "").strip()
    if not token:
        return None
    user = get_current_user(db, token)
    return user


@router.post("/register", response_model=AuthResponse, summary="用户注册")
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """
    注册新用户
    - 用户名长度 2-50 字符，支持字母、数字、下划线和中文
    - 密码长度 6-100 字符
    - 需要两次输入密码确认一致
    """
    try:
        result = register_user(db, req.username, req.password)
        return AuthResponse(
            token=result["token"],
            user=UserInfo(**result["user"]),
            message="注册成功",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=AuthResponse, summary="用户登录")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    """
    用户登录
    - 输入用户名和密码
    - remember=True 则令牌有效期 365 天（免登录）
    """
    try:
        result = login_user(db, req.username, req.password, req.remember)
        return AuthResponse(
            token=result["token"],
            user=UserInfo(**result["user"]),
            message="登录成功",
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/recover", summary="密码找回")
async def recover(req: RecoverRequest, db: Session = Depends(get_db)):
    """
    通过用户名找回密码
    - 返回重置后的新密码
    """
    try:
        result = recover_password(db, req.username)
        return {
            "message": "密码已重置",
            "username": result["username"],
            "new_password": result["password_hint"],
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/me", response_model=UserInfo, summary="获取当前用户信息")
async def get_me(user=Depends(get_auth_user)):
    """
    获取当前登录用户的信息
    - 需要在 Authorization 头中提供 Bearer token
    """
    if not user:
        raise HTTPException(status_code=401, detail="请先登录")
    return UserInfo(**get_user_info(user))


@router.put("/me", response_model=UserInfo, summary="更新用户信息")
async def update_me(
    req: UpdateUserRequest,
    user=Depends(get_auth_user),
    db: Session = Depends(get_db),
):
    """
    更新当前用户信息
    - 可更新: email, display_name, password
    """
    if not user:
        raise HTTPException(status_code=401, detail="请先登录")
    try:
        update_data = {}
        if req.email is not None:
            update_data["email"] = req.email
        if req.display_name is not None:
            update_data["display_name"] = req.display_name
        if req.password:
            update_data["password"] = req.password
        result = update_user_info(db, user, **update_data)
        return UserInfo(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/logout", summary="退出登录")
async def logout(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    退出登录，使当前令牌失效
    """
    if not authorization:
        raise HTTPException(status_code=400, detail="未提供认证令牌")
    token = authorization.replace("Bearer ", "").strip()
    try:
        logout_user(db, token)
        return {"message": "已退出登录"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check", summary="检查登录状态")
async def check_auth(user=Depends(get_auth_user)):
    """
    检查当前令牌是否有效
    - 有效返回用户信息
    - 无效返回 null
    """
    if not user:
        return {"logged_in": False, "user": None}
    return {
        "logged_in": True,
        "user": UserInfo(**get_user_info(user)).model_dump(),
    }
