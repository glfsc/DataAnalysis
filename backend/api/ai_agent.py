"""
AI智能助手API路由
"""
import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database import get_db
from models.database_models import UploadedFile, AIConfig
from services.data_service import DataService
from services.ai_agent_service import AIAgentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI智能助手"])


class AIAskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500, description="用户问题")
    file_id: Optional[str] = Field(None, description="关联文件ID")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文")


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


@router.post("/query", summary="AI自然语言查询")
async def ai_query(
    request: AIAskRequest,
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(_get_current_user_id),
):
    """使用自然语言查询数据（优先使用用户配置的LLM）"""
    df = None
    if request.file_id:
        df = _load_df(request.file_id, db)
        if df is None and request.file_id:
            raise HTTPException(status_code=404, detail="文件不存在")

    try:
        # 检查用户是否有启用的AI配置
        ai_config = None
        if user_id:
            config_record = db.query(AIConfig).filter(
                AIConfig.user_id == user_id,
                AIConfig.is_enabled == True,
            ).first()
            if config_record:
                ai_config = {
                    "api_key": config_record.api_key,
                    "base_url": config_record.base_url,
                    "model_name": config_record.model_name,
                }

        if df is not None:
            if ai_config:
                # 使用用户配置的LLM
                result = await AIAgentService.process_query_with_llm(
                    query=request.question,
                    df=df,
                    ai_config=ai_config,
                    context=request.context,
                )
            else:
                # 使用内置规则引擎
                result = AIAgentService.process_query(
                    query=request.question,
                    df=df,
                    context=request.context,
                )
        else:
            # 无文件时返回通用回复
            result = {
                "reply": f"你好！关于「{request.question}」——请先上传数据文件，我就能帮你分析数据了。你可以上传 CSV 或 Excel 文件。",
                "suggested_action": "upload",
                "insights": [],
            }

        # 统一返回格式：包含 reply 字段
        return {
            "reply": result.get("reply") or result.get("answer", "分析完成"),
            "suggested_action": result.get("suggested_action"),
            "chart_data": result.get("chart_recommendation"),
            "insights": result.get("insights", []),
        }

    except Exception as e:
        logger.error(f"AI查询失败: {str(e)}", exc_info=True)
        return {"reply": f"抱歉，处理你的问题时出错了: {str(e)}", "insights": []}


@router.post("/insights", summary="自动洞察发现")
async def auto_insights(request: AIAskRequest, db: Session = Depends(get_db)):
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
