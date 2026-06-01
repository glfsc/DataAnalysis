"""
数据分析API路由
"""
import logging
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database import get_db
from models.database_models import UploadedFile
from services.data_service import DataService
from services.analysis_service import AnalysisService
from services.ml_service import MLService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["数据分析"])


class AnalysisRequest(BaseModel):
    file_id: str
    columns: Optional[List[str]] = None
    group_column: Optional[str] = None
    target: Optional[str] = None
    features: Optional[List[str]] = None
    n_clusters: int = Field(3, ge=1, le=20)


class ClusterRequest(BaseModel):
    file_id: str
    algorithms: List[str] = Field(default=["kmeans"], description="聚类算法列表: kmeans/kmedoids/optics/agnes/gmm")
    features: Optional[List[str]] = None
    n_clusters: int = Field(3, ge=1, le=20)
    params: Optional[Dict[str, Any]] = Field(default=None, description="各算法的参数字典")


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


@router.post("/statistics", summary="描述性统计")
async def get_statistics(request: AnalysisRequest, db: Session = Depends(get_db)):
    """获取数据的描述性统计分析结果"""
    df = _load_df(request.file_id, db)
    stats = AnalysisService.descriptive_statistics(df)
    return {"file_id": request.file_id, "statistics": stats}


@router.post("/correlation", summary="相关性分析")
async def correlation_analysis(request: AnalysisRequest, db: Session = Depends(get_db)):
    """计算数值列之间的相关性矩阵（自动使用全部数值列）"""
    df = _load_df(request.file_id, db)
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if len(numeric_cols) < 2:
        raise HTTPException(status_code=400, detail="需要至少2个数值列才能做相关性分析")

    result = AnalysisService.correlation_analysis(df, numeric_cols, "pearson")
    return {"file_id": request.file_id, **result}


@router.post("/groupby", summary="分组聚合分析")
async def groupby_analysis(request: AnalysisRequest, db: Session = Depends(get_db)):
    """对数据进行分组聚合分析"""
    df = _load_df(request.file_id, db)

    # 自动选择分组列（第一个非数值列）和聚合列（数值列）
    group_col = request.group_column
    if not group_col:
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        if not cat_cols:
            raise HTTPException(status_code=400, detail="没有可用的分组列，请指定 group_column")
        group_col = cat_cols[0]

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if not numeric_cols:
        raise HTTPException(status_code=400, detail="没有可用的数值列")

    try:
        result = AnalysisService.groupby_analysis(df, group_col, numeric_cols, ["mean", "count"])
        return {"file_id": request.file_id, "groupby_result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分组聚合失败: {str(e)}")


@router.post("/cluster", summary="多算法聚类对比分析")
async def cluster_analysis(request: ClusterRequest, db: Session = Depends(get_db)):
    """使用多种聚类算法进行对比分析：K-Means、K-Medoids、OPTICS、AGNES、GMM"""
    df = _load_df(request.file_id, db)

    features = request.features or df.select_dtypes(include=["number"]).columns.tolist()
    if len(features) < 2:
        raise HTTPException(status_code=400, detail="需要至少2个数值列才能聚类")

    df_numeric = df[features].dropna()
    n_clusters = request.n_clusters

    # 根据算法设置合理的最小数据量
    min_required = n_clusters  # K-Means/K-Medoids/AGNES/GMM 至少需要 n_clusters 个样本
    for algo in request.algorithms:
        if algo == "optics":
            min_samples_param = (request.params or {}).get("optics", {}).get("min_samples", 5)
            min_required = max(min_required, min_samples_param)

    if len(df_numeric) < min_required:
        raise HTTPException(status_code=400, detail=f"有效数据行数({len(df_numeric)})少于最小要求({min_required})")

    # 验证算法
    valid_algorithms = {"kmeans", "kmedoids", "optics", "agnes", "gmm"}
    selected = [a for a in request.algorithms if a in valid_algorithms]
    if not selected:
        raise HTTPException(status_code=400, detail=f"请选择至少一个有效算法: {', '.join(valid_algorithms)}")

    try:
        result = MLService.multi_clustering(
            df_numeric,
            features,
            algorithms=selected,
            params=request.params or {"n_clusters": n_clusters},
        )
        logger.info(f"聚类完成: algorithms={selected}, comparison_count={len(result.get('comparison',[]))}")
        return {"file_id": request.file_id, "cluster_result": result}
    except Exception as e:
        import traceback
        logger.error(f"聚类分析失败: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"聚类分析失败: {str(e)}")


@router.post("/regression", summary="线性回归")
async def regression_analysis(request: AnalysisRequest, db: Session = Depends(get_db)):
    """多元线性回归分析"""
    df = _load_df(request.file_id, db)
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    if len(numeric_cols) < 2:
        raise HTTPException(status_code=400, detail="需要至少2个数值列才能做回归分析")

    target = request.target or numeric_cols[-1]
    features = request.features or [c for c in numeric_cols if c != target]

    if not features:
        raise HTTPException(status_code=400, detail="没有可用的特征列")

    try:
        result = MLService.linear_regression(df, features, target, test_size=0.3 if len(df) < 20 else 0.2)
        return {"file_id": request.file_id, "regression_result": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回归分析失败: {str(e)}")


@router.post("/anomaly", summary="异常检测")
async def anomaly_detection(request: AnalysisRequest, db: Session = Depends(get_db)):
    """使用Isolation Forest进行异常检测"""
    df = _load_df(request.file_id, db)
    features = request.features or df.select_dtypes(include=["number"]).columns.tolist()

    if not features:
        raise HTTPException(status_code=400, detail="没有可用的数值列")

    try:
        result = MLService.anomaly_detection(df, features)
        logger.info(f"异常检测完成: anomaly_count={result.get('anomaly_count',0)}, rows_returned={len(result.get('anomaly_rows',[]))}")
        return {"file_id": request.file_id, "anomaly_result": result}
    except Exception as e:
        import traceback
        logger.error(f"异常检测失败: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"异常检测失败: {str(e)}")
