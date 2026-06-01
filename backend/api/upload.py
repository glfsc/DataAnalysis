"""
数据上传API路由
"""
import math
import uuid
import logging
from typing import Dict, Any

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.database_models import UploadedFile
from services.data_service import DataService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["数据上传"])


def _sanitize(obj):
    """递归转换 numpy 类型和 NaN/Inf 为 JSON 安全值"""
    import numpy as np
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        val = float(obj)
        if math.isnan(val) or math.isinf(val):
            return None
        return val
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, np.ndarray):
        return _sanitize(obj.tolist())
    return obj


# 辅助：从数据库加载 DataFrame
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


@router.post("/upload", summary="上传数据文件")
async def upload_file(
    file: UploadFile = File(..., description="CSV或Excel文件（最大10MB）"),
    db: Session = Depends(get_db),
):
    """上传CSV或Excel文件进行数据分析"""
    try:
        content = await file.read()

        is_valid, error_msg = DataService.validate_file(file.filename, len(content))
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        file_id = str(uuid.uuid4())
        df = DataService.load_file(content, file.filename)
        file_path = DataService.save_dataframe(df, file_id, cleaned=False)
        DataService.set_dataframe(file_id, df)

        preview = DataService.get_preview(df)
        info_data = DataService.get_info(df)

        # 保存到数据库
        db_record = UploadedFile(
            file_id=file_id,
            filename=file.filename,
            file_path=file_path,
            file_type=file.filename.rsplit(".", 1)[-1].lower(),
            file_size=len(content),
            rows=info_data["rows"],
            columns=info_data["columns"],
            column_info=info_data["column_types"],
        )
        db.add(db_record)

        logger.info(f"文件上传成功: {file.filename} (ID: {file_id})")

        return _sanitize({
            "file_id": file_id,
            "file_name": file.filename,
            "columns": info_data["column_names"],
            "numeric_columns": info_data["numeric_columns"],
            "row_count": info_data["rows"],
            "column_count": info_data["columns"],
            "missing_count": sum(info_data.get("missing_summary", {}).values()),
            "file_size": len(content),
            "preview_data": preview,
            "column_types": info_data["column_types"],
        })

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/upload/list", summary="获取所有已上传文件列表")
async def list_files(db: Session = Depends(get_db)):
    """获取所有已上传文件的信息列表"""
    files = db.query(UploadedFile).order_by(UploadedFile.upload_time.desc()).all()
    return {
        "total": len(files),
        "files": [
            {
                "file_id": f.file_id,
                "filename": f.filename,
                "file_type": f.file_type,
                "file_size": f.file_size,
                "rows": f.rows,
                "columns": f.columns,
                "is_cleaned": f.is_cleaned,
                "upload_time": f.upload_time.strftime("%Y-%m-%d %H:%M:%S") if f.upload_time else None,
            }
            for f in files
        ],
    }


@router.get("/upload/{file_id}/info", summary="获取文件预览信息")
async def get_file_info(file_id: str, db: Session = Depends(get_db)):
    """获取指定文件的基本信息和预览数据（支持清洗后文件）"""
    df = _load_df(file_id, db)
    preview = DataService.get_preview(df)
    info_data = DataService.get_info(df)
    return _sanitize({
        "file_id": file_id,
        "preview": preview,
        "columns": info_data["column_names"],
        "row_count": info_data["rows"],
        "column_count": info_data["columns"],
    })
