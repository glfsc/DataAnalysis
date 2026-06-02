"""
用户认证服务模块
提供注册、登录、密码找回、用户信息管理等功能
使用 PBKDF2-HMAC-SHA256 进行密码哈希，内置盐值管理
"""
import hashlib
import secrets
import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from models.database_models import User, UserSession

logger = logging.getLogger(__name__)

# 会话过期时间
SESSION_EXPIRE_DAYS = 30  # 普通登录30天过期
SESSION_EXPIRE_DAYS_REMEMBER = 365  # 记住登录365天过期


def _hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """
    使用 PBKDF2-HMAC-SHA256 对密码进行哈希
    返回 (hash_hex, salt_hex)
    """
    if salt is None:
        salt = secrets.token_hex(32)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=100_000,
    )
    return dk.hex(), salt


def _generate_token() -> str:
    """生成安全的会话令牌"""
    return secrets.token_urlsafe(48)


def _get_user_by_token(db: Session, token: str) -> User | None:
    """根据令牌获取用户（验证会话有效期）"""
    session = db.query(UserSession).filter(
        UserSession.token == token,
        UserSession.expires_at > datetime.utcnow(),
    ).first()
    if not session:
        return None
    return db.query(User).filter(User.id == session.user_id).first()


def register_user(db: Session, username: str, password: str) -> dict:
    """
    注册新用户
    返回 {"token": str, "user": dict}

    Raises:
        ValueError: 用户名已存在
    """
    # 检查用户名是否已存在
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise ValueError(f"用户名 '{username}' 已被注册")

    # 哈希密码
    password_hash, salt = _hash_password(password)

    # 创建用户
    user = User(
        username=username,
        password_hash=password_hash,
        salt=salt,
        display_name=username,
    )
    db.add(user)
    db.flush()  # 获取 user.id

    # 创建会话
    token = _generate_token()
    session = UserSession(
        user_id=user.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(days=SESSION_EXPIRE_DAYS),
    )
    db.add(session)
    db.commit()
    db.refresh(user)

    logger.info(f"新用户注册: {username} (ID: {user.id})")
    return {
        "token": token,
        "user": _user_to_dict(user),
    }


def login_user(db: Session, username: str, password: str, remember: bool = False) -> dict:
    """
    用户登录
    返回 {"token": str, "user": dict}

    Raises:
        ValueError: 用户名或密码错误
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise ValueError("用户名或密码错误")

    # 验证密码
    expected_hash, _ = _hash_password(password, user.salt)
    if expected_hash != user.password_hash:
        raise ValueError("用户名或密码错误")

    # 创建新会话
    token = _generate_token()
    expire_days = SESSION_EXPIRE_DAYS_REMEMBER if remember else SESSION_EXPIRE_DAYS
    session = UserSession(
        user_id=user.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(days=expire_days),
    )
    db.add(session)
    db.commit()

    logger.info(f"用户登录: {username} (ID: {user.id}, remember={remember})")
    return {
        "token": token,
        "user": _user_to_dict(user),
    }


def recover_password(db: Session, username: str) -> dict:
    """
    通过用户名找回密码
    返回 {"username": str, "password_hint": str}

    Raises:
        ValueError: 用户不存在
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise ValueError(f"用户 '{username}' 不存在")

    # 生成一个新密码（取用户名前2字符 + 随机6位）
    new_password = user.username[:2] + secrets.token_hex(3)

    # 更新密码哈希
    password_hash, salt = _hash_password(new_password)
    user.password_hash = password_hash
    user.salt = salt
    db.commit()

    logger.info(f"密码重置: {username} (ID: {user.id})")
    return {
        "username": username,
        "password_hint": new_password,
    }


def get_user_info(user: User) -> dict:
    """获取用户信息"""
    return _user_to_dict(user)


def update_user_info(db: Session, user: User, **kwargs) -> dict:
    """
    更新用户信息
    可更新字段: email, display_name, password
    """
    if "email" in kwargs and kwargs["email"] is not None:
        user.email = kwargs["email"]
    if "display_name" in kwargs and kwargs["display_name"] is not None:
        user.display_name = kwargs["display_name"]
    if "password" in kwargs and kwargs["password"]:
        password_hash, salt = _hash_password(kwargs["password"])
        user.password_hash = password_hash
        user.salt = salt

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    logger.info(f"用户信息更新: {user.username} (ID: {user.id})")
    return _user_to_dict(user)


def logout_user(db: Session, token: str) -> None:
    """退出登录，删除会话"""
    db.query(UserSession).filter(UserSession.token == token).delete()
    db.commit()
    logger.info(f"会话已删除: token={token[:12]}...")


def get_current_user(db: Session, token: str) -> User | None:
    """获取当前登录用户（从令牌）"""
    return _get_user_by_token(db, token)


def _user_to_dict(user: User) -> dict:
    """User ORM 对象转字典"""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email or "",
        "display_name": user.display_name or user.username,
        "avatar_url": user.avatar_url or "",
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
