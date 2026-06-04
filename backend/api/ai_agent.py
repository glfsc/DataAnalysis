"""
AI智能助手API路由 v2
纯 LLM 驱动 · 流式输出 · 上下文感知
"""
import json
import logging
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database import get_db
from models.database_models import UploadedFile, AIConfig
from services.data_service import DataService
from services.ai_agent_service import AIAgentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI智能助手"])


class AIChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="用户问题")
    file_id: Optional[str] = Field(None, description="关联文件ID")
    history: Optional[List[Dict[str, str]]] = Field(None, description="对话历史")


def _get_current_user_id(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Optional[int]:
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "").strip()
    if not token:
        return None
    from services.auth_service import get_current_user
    user = get_current_user(db, token)
    return user.id if user else None


def _load_df(file_id: str, db: Session):
    df = DataService.get_dataframe(file_id)
    if df is None:
        record = db.query(UploadedFile).filter(UploadedFile.file_id == file_id).first()
        if record is None:
            return None
        import pandas as pd
        file_path = record.cleaned_path or record.file_path
        df = pd.read_csv(file_path, encoding="utf-8-sig")
        DataService.set_dataframe(file_id, df)
    return df


@router.post("/chat", summary="AI 流式对话（SSE）")
async def ai_chat_stream(
    request: AIChatRequest,
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(_get_current_user_id),
):
    """
    AI 流式对话接口 — 使用 Server-Sent Events 实时返回 AI 生成的内容

    需要用户配置并启用 AI 模型。
    返回格式: text/event-stream
    """
    # 检查是否有启用的AI配置
    if not user_id:
        raise HTTPException(status_code=401, detail="请先登录")

    config_record = db.query(AIConfig).filter(
        AIConfig.user_id == user_id,
        AIConfig.is_enabled == True,
    ).first()

    if not config_record:
        raise HTTPException(
            status_code=400,
            detail="请先在 AI 助手中配置并启用一个 AI 模型。点击 AI 助手页面的「⚙️ 配置」按钮进行设置。",
        )

    ai_config = {
        "api_key": config_record.api_key,
        "base_url": config_record.base_url,
        "model_name": config_record.model_name,
    }

    # 加载数据
    df = None
    if request.file_id:
        df = _load_df(request.file_id, db)
        if df is None:
            raise HTTPException(status_code=404, detail="文件不存在")

    if df is None:
        raise HTTPException(status_code=400, detail="请先上传并选择一个数据文件")

    async def event_stream():
        async for event in AIAgentService.chat_stream(
            query=request.question,
            df=df,
            ai_config=ai_config,
            chat_history=request.history,
        ):
            yield event

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲
        },
    )


@router.post("/query", summary="AI 对话（非流式，兼容旧版）")
async def ai_query(
    request: AIChatRequest,
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(_get_current_user_id),
):
    """
    AI 对话接口（非流式）— 返回完整回答
    需要用户配置并启用 AI 模型
    """
    # 检查是否有启用的AI配置
    if not user_id:
        return {"reply": "请先登录后再使用 AI 助手。", "model": None, "success": False}

    config_record = db.query(AIConfig).filter(
        AIConfig.user_id == user_id,
        AIConfig.is_enabled == True,
    ).first()

    if not config_record:
        return {
            "reply": "⚠️ 尚未配置 AI 模型。\n\n请点击 AI 助手页面下方的 **「⚙️ 配置」** 按钮，添加并启用一个 AI 模型配置。\n\n支持的配置：\n- OpenAI 官方 API\n- 任何 OpenAI 兼容接口（如 Azure OpenAI、Ollama、vLLM、DeepSeek 等）\n\n需要提供：名称、API Key、API 地址 URL、模型名称。",
            "model": None,
            "success": False,
        }

    ai_config = {
        "api_key": config_record.api_key,
        "base_url": config_record.base_url,
        "model_name": config_record.model_name,
    }

    # 加载数据
    df = None
    if request.file_id:
        df = _load_df(request.file_id, db)

    if df is None:
        return {"reply": "请先上传并选择一个数据文件，我才能帮你分析。", "model": config_record.model_name, "success": True}

    result = await AIAgentService.chat(
        query=request.question,
        df=df,
        ai_config=ai_config,
        chat_history=request.history,
    )

    return result


@router.post("/insights", summary="自动洞察发现")
async def auto_insights(request: AIChatRequest, db: Session = Depends(get_db)):
    """自动分析数据，发现关键洞察"""
    if not request.file_id:
        raise HTTPException(status_code=400, detail="需要提供 file_id")

    df = _load_df(request.file_id, db)
    if df is None:
        raise HTTPException(status_code=404, detail="文件不存在")

    try:
        insights = AIAgentService.auto_discover_insights(df)
        return {"file_id": request.file_id, "total_insights": len(insights), "insights": insights}
    except Exception as e:
        logger.error(f"洞察发现失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"洞察发现失败: {str(e)}")
