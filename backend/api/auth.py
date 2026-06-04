"""
用户认证 API 路由
提供注册、登录、密码找回、用户信息管理接口
"""
import os
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from config import AVATAR_DIR, MAX_AVATAR_SIZE, ALLOWED_AVATAR_EXTENSIONS
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
    save_avatar,
    admin_list_users,
    admin_delete_user,
    admin_reset_user_password,
    admin_toggle_admin,
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
    - 可选提供 new_password 自定义新密码
    - 不提供则随机生成密码
    """
    try:
        result = recover_password(db, req.username, req.new_password)
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
        if req.avatar_url is not None:
            update_data["avatar_url"] = req.avatar_url
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


@router.post("/avatar", summary="上传用户头像")
async def upload_avatar(
    file: UploadFile = File(...),
    user=Depends(get_auth_user),
    db: Session = Depends(get_db),
):
    """
    上传用户头像图片
    - 支持 PNG、JPG、GIF、WebP 格式
    - 最大 2MB
    - 自动裁剪为正方形并缩放至 200x200
    """
    if not user:
        raise HTTPException(status_code=401, detail="请先登录")

    # 验证文件扩展名
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_AVATAR_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的图片格式，允许: {', '.join(ALLOWED_AVATAR_EXTENSIONS)}",
        )

    # 读取文件内容
    contents = await file.read()
    if len(contents) > MAX_AVATAR_SIZE:
        raise HTTPException(status_code=400, detail="图片大小不能超过 2MB")

    # 生成唯一文件名
    avatar_filename = f"{user.id}_{uuid.uuid4().hex[:8]}{ext}"
    avatar_path = AVATAR_DIR / avatar_filename

    # 保存原始图片
    with open(avatar_path, "wb") as f:
        f.write(contents)

    # 尝试用 PIL 处理图片（如果可用），否则直接用原图
    try:
        from PIL import Image
        img = Image.open(avatar_path)
        # 转换为 RGB（处理 RGBA/GIF）
        if img.mode in ("RGBA", "P", "LA"):
            rgb_img = Image.new("RGB", img.size, (30, 30, 50))
            if img.mode == "P":
                img = img.convert("RGBA")
            if img.mode in ("RGBA", "LA"):
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            else:
                rgb_img.paste(img)
            img = rgb_img
        elif img.mode != "RGB":
            img = img.convert("RGB")
        # 裁剪为正方形（取中心）
        w, h = img.size
        size = min(w, h)
        left = (w - size) // 2
        top = (h - size) // 2
        img = img.crop((left, top, left + size, top + size))
        # 缩放到 200x200
        img = img.resize((200, 200), Image.LANCZOS)
        # 保存为 PNG
        png_filename = f"{user.id}_{uuid.uuid4().hex[:8]}.png"
        png_path = AVATAR_DIR / png_filename
        img.save(png_path, "PNG")
        # 删除原始文件
        if avatar_path != png_path:
            os.remove(avatar_path)
        avatar_filename = png_filename
        avatar_path = png_path
    except ImportError:
        logger.warning("Pillow 未安装，头像将不做裁剪处理")
    except Exception as e:
        logger.warning(f"头像处理失败（使用原图）: {e}")

    # 更新用户头像 URL
    avatar_url = f"/uploads/avatars/{avatar_filename}"
    save_avatar(db, user, avatar_url)

    logger.info(f"用户 {user.username} 更新了头像: {avatar_url}")
    return {
        "message": "头像上传成功",
        "avatar_url": avatar_url,
    }


# ============ 管理员用户管理 API ============

def require_admin(user=Depends(get_auth_user)):
    """管理员权限依赖"""
    if not user:
        raise HTTPException(status_code=401, detail="请先登录")
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


@router.get("/admin/users", summary="管理员 — 获取所有用户列表")
async def list_users(
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """管理员获取所有注册用户列表"""
    users = admin_list_users(db)
    return {"users": users, "total": len(users)}


@router.delete("/admin/users/{user_id}", summary="管理员 — 删除用户")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """管理员删除指定用户"""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    try:
        admin_delete_user(db, user_id)
        return {"message": "用户已删除"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/admin/users/{user_id}/reset-password", summary="管理员 — 重置用户密码")
async def reset_user_password(
    user_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """管理员重置指定用户的密码"""
    try:
        result = admin_reset_user_password(db, user_id)
        return {
            "message": "密码已重置",
            "username": result["username"],
            "new_password": result["new_password"],
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/admin/users/{user_id}/toggle-admin", summary="管理员 — 切换管理员权限")
async def toggle_user_admin(
    user_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """管理员切换指定用户的管理员权限"""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="不能修改自己的管理员权限")
    try:
        result = admin_toggle_admin(db, user_id)
        return {"message": "管理员权限已更新", "user": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
