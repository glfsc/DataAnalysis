"""
可视化API路由
"""
import logging
import uuid
from typing import Optional, List, Union

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database import get_db
from models.database_models import UploadedFile, ChartConfig
from services.data_service import DataService
from services.visualization_service import VisualizationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/visualization", tags=["数据可视化"])


class GenerateChartRequest(BaseModel):
    file_id: str
    chart_type: str = Field(..., description="图表类型")
    x_column: Optional[str] = Field(None, description="X轴列名")
    y_columns: Optional[List[str]] = Field(None, description="Y轴列名列表")
    title: Optional[str] = Field(None, description="图表标题")


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


@router.post("/generate", summary="生成可视化图表")
async def create_visualization(request: GenerateChartRequest, db: Session = Depends(get_db)):
    """根据参数生成ECharts可视化图表配置"""
    df = _load_df(request.file_id, db)

    # 自动选择列
    x_col = request.x_column
    y_cols = request.y_columns

    if not x_col:
        # 自动选第一列作为X轴
        x_col = df.columns[0]

    if not y_cols:
        # 自动选数值列作为Y轴
        y_cols = df.select_dtypes(include=["number"]).columns.tolist()[:3]
        if not y_cols:
            y_cols = [df.columns[-1]] if len(df.columns) > 1 else [df.columns[0]]

    try:
        result = VisualizationService.generate_chart(
            df=df,
            chart_type=request.chart_type,
            x_column=x_col,
            y_column=y_cols,  # 后端服务接受 list 或 str
            title=request.title or f"{request.chart_type} 图表",
        )

        # 保存图表配置
        chart_id = result.get("chart_id", str(uuid.uuid4()))
        chart_record = ChartConfig(
            chart_id=chart_id,
            file_id=request.file_id,
            chart_type=request.chart_type,
            title=request.title or f"{request.chart_type}图表",
            config=result.get("echarts_option", {}),
        )
        db.add(chart_record)
        db.commit()

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"图表生成失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"图表生成失败: {str(e)}")
