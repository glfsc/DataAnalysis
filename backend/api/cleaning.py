"""
数据清洗API路由
"""
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database import get_db
from models.database_models import UploadedFile
from models.schemas import CleaningParams
from services.data_service import DataService
from services.cleaning_service import CleaningService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["数据清洗"])


# 前端期望的请求格式
class CleanRequest(BaseModel):
    file_id: str
    missing_method: str = Field("none", description="缺失值处理方式")
    drop_duplicates: bool = Field(False, description="是否删除重复行")
    outlier_method: Optional[str] = Field(None, description="异常值检测方法")


def _load_df(file_id: str, db: Session):
    df = DataService.get_dataframe(file_id)
    if df is None:
        record = db.query(UploadedFile).filter(UploadedFile.file_id == file_id).first()
        if record is None:
            raise HTTPException(status_code=404, detail="文件不存在")
        import pandas as pd
        file_path = record.cleaned_path or record.file_path
        df = pd.read_csv(file_path, encoding="utf-8-sig")
        DataService.set_dataframe(file_id, df)
    return df


@router.post("/cleaning/clean", summary="清洗数据")
async def clean_data(request: CleanRequest, db: Session = Depends(get_db)):
    """对上传的数据执行清洗操作（前端接口）"""
    df = _load_df(request.file_id, db)

    # 映射前端参数到后端 CleaningParams
    params = CleaningParams(
        handle_missing=request.missing_method,
        drop_duplicates=request.drop_duplicates,
        outlier_method=request.outlier_method,
    )

    try:
        original_rows = len(df)
        original_missing = int(df.isnull().sum().sum())
        original_duplicates = int(df.duplicated().sum())

        df_cleaned, summary = CleaningService.clean_data(df, params)

        cleaned_file_id = f"{request.file_id}_cleaned"
        cleaned_path = DataService.save_dataframe(df_cleaned, cleaned_file_id, cleaned=True)
        DataService.set_dataframe(cleaned_file_id, df_cleaned)

        # 更新数据库
        file_record = db.query(UploadedFile).filter(
            UploadedFile.file_id == request.file_id
        ).first()
        if file_record:
            file_record.is_cleaned = True
            file_record.cleaned_path = cleaned_path

        cleaned_missing = int(df_cleaned.isnull().sum().sum())
        cleaned_duplicates = int(df_cleaned.duplicated().sum())

        logger.info(f"数据清洗完成: {request.file_id}")

        return {
            "file_id": request.file_id,
            "cleaned_file_id": cleaned_file_id,
            "original_shape": [original_rows, len(df.columns)],
            "original_missing": original_missing,
            "original_duplicates": original_duplicates,
            "cleaned_shape": [len(df_cleaned), len(df_cleaned.columns)],
            "cleaned_missing": cleaned_missing,
            "cleaned_duplicates": cleaned_duplicates,
            "summary": summary.dict(),
        }

    except Exception as e:
        logger.error(f"数据清洗失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"清洗失败: {str(e)}")
