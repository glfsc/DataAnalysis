"""
结果导出API路由
"""
import io
import logging

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models.database_models import UploadedFile
from services.data_service import DataService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/export", tags=["结果导出"])


class ExportRequest(BaseModel):
    file_id: str


class ExportDataRequest(BaseModel):
    file_id: str
    rows: list = None  # 可选：前端编辑后的数据行
    columns: list = None  # 可选：前端编辑后的列名


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


@router.post("/data", summary="导出数据（CSV）")
async def export_data(request: ExportDataRequest, db: Session = Depends(get_db)):
    """导出数据为CSV文件（支持导出前端编辑后的数据）"""
    import pandas as pd

    # 如果前端提供了编辑后的数据，使用编辑后的数据
    if request.rows is not None:
        df = pd.DataFrame(request.rows)
        if request.columns:
            # 确保列顺序
            df = df[request.columns] if all(c in df.columns for c in request.columns) else df
    else:
        df = _load_df(request.file_id, db)

    stream = io.StringIO()
    df.to_csv(stream, index=False, encoding="utf-8-sig")
    stream.seek(0)

    file_record = db.query(UploadedFile).filter(
        UploadedFile.file_id == request.file_id
    ).first()
    base_name = (file_record.filename if file_record else "data").rsplit(".", 1)[0]

    return StreamingResponse(
        iter([stream.getvalue().encode("utf-8-sig")]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{base_name}_exported.csv"'},
    )

