"""
数据 CRUD API — 表格数据增删改查 + 全量数据获取
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models.database_models import UploadedFile
from services.data_service import DataService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/data", tags=["数据CRUD"])


class UpdateCellRequest(BaseModel):
    file_id: str
    row_index: int
    column: str
    value: str


class AddRowRequest(BaseModel):
    file_id: str
    row_data: dict


class DeleteRowRequest(BaseModel):
    file_id: str
    row_index: int


class ColumnRequest(BaseModel):
    file_id: str
    column: str


class RenameColumnRequest(BaseModel):
    file_id: str
    old_name: str
    new_name: str


class AddColumnRequest(BaseModel):
    file_id: str
    column: str
    default_value: str = ""


class BatchUpdateRequest(BaseModel):
    file_id: str
    rows: list  # list of row dicts (complete replacement)


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


def _save_df(file_id: str, df, db: Session):
    """保存 DataFrame 到缓存和磁盘"""
    DataService.set_dataframe(file_id, df)
    record = db.query(UploadedFile).filter(UploadedFile.file_id == file_id).first()
    if record:
        path = record.cleaned_path or record.file_path
        df.to_csv(path, index=False, encoding="utf-8-sig")
        record.rows = len(df)
        record.columns = len(df.columns)


@router.get("/{file_id}", summary="获取全量数据")
async def get_all_data(
    file_id: str,
    limit: int = 500,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """获取指定文件的全部数据（支持分页）"""
    df = _load_df(file_id, db)
    total = len(df)
    page = df.iloc[offset:offset + limit]
    # JSON 安全转换
    import math, numpy as np
    page = page.replace([float('inf'), float('-inf')], None).where(page.notna(), None)
    records = page.to_dict("records")
    for row in records:
        for k, v in row.items():
            if v is not None and hasattr(v, 'item'):
                row[k] = v.item()
            elif isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                row[k] = None

    return {
        "file_id": file_id,
        "total": total,
        "limit": limit,
        "offset": offset,
        "columns": df.columns.tolist(),
        "data": records,
    }


@router.put("/cell", summary="更新单元格")
async def update_cell(req: UpdateCellRequest, db: Session = Depends(get_db)):
    df = _load_df(req.file_id, db)
    if req.row_index < 0 or req.row_index >= len(df):
        raise HTTPException(status_code=400, detail=f"行索引超出范围 (0-{len(df)-1})")
    if req.column not in df.columns:
        raise HTTPException(status_code=400, detail=f"列 '{req.column}' 不存在")

    # 尝试类型转换
    old_val = df.at[req.row_index, req.column]
    try:
        if old_val is not None:
            if isinstance(old_val, (int, float)):
                new_val = float(req.value) if '.' in req.value else int(req.value)
            else:
                new_val = req.value
        else:
            new_val = req.value
    except ValueError:
        new_val = req.value

    df.at[req.row_index, req.column] = new_val
    _save_df(req.file_id, df, db)
    return {"status": "ok", "row_index": req.row_index, "column": req.column, "new_value": str(new_val)}


@router.post("/row", summary="添加行")
async def add_row(req: AddRowRequest, db: Session = Depends(get_db)):
    import pandas as pd
    df = _load_df(req.file_id, db)
    new_row = {}
    for col in df.columns:
        new_row[col] = req.row_data.get(col, "")
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    _save_df(req.file_id, df, db)
    return {"status": "ok", "new_row_index": len(df) - 1, "total_rows": len(df)}


@router.delete("/row", summary="删除行")
async def delete_row(req: DeleteRowRequest, db: Session = Depends(get_db)):
    df = _load_df(req.file_id, db)
    if req.row_index < 0 or req.row_index >= len(df):
        raise HTTPException(status_code=400, detail=f"行索引超出范围 (0-{len(df)-1})")
    df = df.drop(df.index[req.row_index]).reset_index(drop=True)
    _save_df(req.file_id, df, db)
    return {"status": "ok", "deleted_index": req.row_index, "total_rows": len(df)}


@router.put("/column/rename", summary="重命名列")
async def rename_column(req: RenameColumnRequest, db: Session = Depends(get_db)):
    df = _load_df(req.file_id, db)
    if req.old_name not in df.columns:
        raise HTTPException(status_code=400, detail=f"列 '{req.old_name}' 不存在")
    df = df.rename(columns={req.old_name: req.new_name})
    _save_df(req.file_id, df, db)
    return {"status": "ok", "old_name": req.old_name, "new_name": req.new_name}


@router.delete("/column", summary="删除列")
async def delete_column(req: ColumnRequest, db: Session = Depends(get_db)):
    df = _load_df(req.file_id, db)
    if req.column not in df.columns:
        raise HTTPException(status_code=400, detail=f"列 '{req.column}' 不存在")
    df = df.drop(columns=[req.column])
    _save_df(req.file_id, df, db)
    return {"status": "ok", "deleted_column": req.column, "remaining_columns": df.columns.tolist()}


@router.post("/column", summary="添加列")
async def add_column(req: AddColumnRequest, db: Session = Depends(get_db)):
    df = _load_df(req.file_id, db)
    if req.column in df.columns:
        raise HTTPException(status_code=400, detail=f"列 '{req.column}' 已存在")
    df[req.column] = req.default_value
    _save_df(req.file_id, df, db)
    return {"status": "ok", "new_column": req.column, "columns": df.columns.tolist()}


@router.put("/batch", summary="批量更新（全量替换数据）")
async def batch_update(req: BatchUpdateRequest, db: Session = Depends(get_db)):
    import pandas as pd
    df_new = pd.DataFrame(req.rows)
    _save_df(req.file_id, df_new, db)
    return {"status": "ok", "total_rows": len(df_new), "columns": df_new.columns.tolist()}
