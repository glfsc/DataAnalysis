"""
AI模型配置 API 路由
提供 AI 模型配置方案的增删改查和启用/停用
"""
import logging
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database import get_db
from models.database_models import AIConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai-config", tags=["AI配置"])


def _get_current_user_id(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> int:
    """认证依赖：必须登录"""
    if not authorization:
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization.replace("Bearer ", "").strip()
    if not token:
        raise HTTPException(status_code=401, detail="请先登录")
    from services.auth_service import get_current_user
    user = get_current_user(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    return user.id


class AIConfigCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="配置方案名称")
    api_key: str = Field(..., min_length=1, max_length=500, description="API Key")
    base_url: str = Field(..., min_length=1, max_length=500, description="API地址URL")
    model_name: str = Field(..., min_length=1, max_length=200, description="模型名称")


class AIConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    api_key: Optional[str] = Field(None, max_length=500)
    base_url: Optional[str] = Field(None, max_length=500)
    model_name: Optional[str] = Field(None, max_length=200)


@router.get("/list", summary="获取AI配置列表")
async def list_configs(
    db: Session = Depends(get_db),
    user_id: int = Depends(_get_current_user_id),
):
    """获取当前用户的所有AI配置方案"""
    configs = db.query(AIConfig).filter(
        AIConfig.user_id == user_id
    ).order_by(AIConfig.created_at.desc()).all()

    return {
        "configs": [
            {
                "id": c.id,
                "name": c.name,
                "api_key_masked": c.api_key[:8] + "****" + c.api_key[-4:] if len(c.api_key) > 12 else "****",
                "api_key_full": c.api_key,  # 完整key，前端默认隐藏
                "base_url": c.base_url,
                "model_name": c.model_name,
                "is_enabled": c.is_enabled,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in configs
        ]
    }


@router.post("/create", summary="创建AI配置")
async def create_config(
    req: AIConfigCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(_get_current_user_id),
):
    """创建新的AI配置方案"""
    config = AIConfig(
        user_id=user_id,
        name=req.name,
        api_key=req.api_key,
        base_url=req.base_url,
        model_name=req.model_name,
        is_enabled=False,
    )
    db.add(config)
    db.commit()
    db.refresh(config)

    logger.info(f"用户 {user_id} 创建了AI配置: {config.name}")
    return {
        "id": config.id,
        "name": config.name,
        "base_url": config.base_url,
        "model_name": config.model_name,
        "is_enabled": config.is_enabled,
        "message": "配置创建成功",
    }


@router.put("/{config_id}", summary="更新AI配置")
async def update_config(
    config_id: int,
    req: AIConfigUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(_get_current_user_id),
):
    """更新指定的AI配置方案"""
    config = db.query(AIConfig).filter(
        AIConfig.id == config_id,
        AIConfig.user_id == user_id,
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    if req.name is not None:
        config.name = req.name
    if req.api_key is not None:
        config.api_key = req.api_key
    if req.base_url is not None:
        config.base_url = req.base_url
    if req.model_name is not None:
        config.model_name = req.model_name

    db.commit()
    return {"message": "配置已更新"}


@router.delete("/{config_id}", summary="删除AI配置")
async def delete_config(
    config_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(_get_current_user_id),
):
    """删除指定的AI配置方案"""
    config = db.query(AIConfig).filter(
        AIConfig.id == config_id,
        AIConfig.user_id == user_id,
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    db.delete(config)
    db.commit()
    logger.info(f"用户 {user_id} 删除了AI配置: {config.name}")
    return {"message": "配置已删除"}


@router.post("/{config_id}/enable", summary="启用AI配置（含连接测试）")
async def enable_config(
    config_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(_get_current_user_id),
):
    """启用指定的AI配置方案（同时停用其他配置），并测试连接"""
    config = db.query(AIConfig).filter(
        AIConfig.id == config_id,
        AIConfig.user_id == user_id,
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    # 先测试连接
    from services.ai_agent_service import AIAgentService
    test_result = await AIAgentService.test_connection({
        "api_key": config.api_key,
        "base_url": config.base_url,
        "model_name": config.model_name,
    })

    if not test_result["success"]:
        raise HTTPException(
            status_code=400,
            detail=f"连接测试失败: {test_result['message']}",
        )

    # 停用该用户所有配置
    db.query(AIConfig).filter(AIConfig.user_id == user_id).update({"is_enabled": False})
    # 启用选中配置
    config.is_enabled = True
    db.commit()

    logger.info(f"用户 {user_id} 启用了AI配置: {config.name} (模型: {config.model_name})")
    return {
        "message": f"已启用配置: {config.name}",
        "connection_test": test_result["message"],
        "model": config.model_name,
    }


@router.post("/{config_id}/test", summary="测试AI配置连接")
async def test_config(
    config_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(_get_current_user_id),
):
    """测试指定AI配置的连接是否可用"""
    config = db.query(AIConfig).filter(
        AIConfig.id == config_id,
        AIConfig.user_id == user_id,
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    from services.ai_agent_service import AIAgentService
    result = await AIAgentService.test_connection({
        "api_key": config.api_key,
        "base_url": config.base_url,
        "model_name": config.model_name,
    })
    return result


@router.post("/{config_id}/disable", summary="停用AI配置")
async def disable_config(
    config_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(_get_current_user_id),
):
    """停用指定的AI配置方案"""
    config = db.query(AIConfig).filter(
        AIConfig.id == config_id,
        AIConfig.user_id == user_id,
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    config.is_enabled = False
    db.commit()
    return {"message": f"已停用配置: {config.name}"}


@router.get("/active", summary="获取当前启用的AI配置")
async def get_active_config(
    db: Session = Depends(get_db),
    user_id: int = Depends(_get_current_user_id),
):
    """获取当前用户启用的AI配置（AI助手使用）"""
    config = db.query(AIConfig).filter(
        AIConfig.user_id == user_id,
        AIConfig.is_enabled == True,
    ).first()

    if not config:
        return {"active": None, "message": "没有启用的AI配置"}

    return {
        "active": {
            "id": config.id,
            "name": config.name,
            "api_key": config.api_key,
            "base_url": config.base_url,
            "model_name": config.model_name,
        }
    }
