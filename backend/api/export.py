"""
结果导出API路由
"""
import io
import logging

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse, HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models.database_models import UploadedFile
from services.data_service import DataService
from services.cleaning_service import CleaningService
from services.analysis_service import AnalysisService
from services.ai_agent_service import AIAgentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/export", tags=["结果导出"])


class ExportRequest(BaseModel):
    file_id: str


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
async def export_data(request: ExportRequest, db: Session = Depends(get_db)):
    """导出清洗后的数据为CSV文件"""
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
        headers={"Content-Disposition": f'attachment; filename="{base_name}_cleaned.csv"'},
    )


@router.post("/report", summary="导出分析报告（HTML）")
async def export_report(request: ExportRequest, db: Session = Depends(get_db)):
    """生成并导出HTML格式的数据分析报告"""
    df = _load_df(request.file_id, db)

    story = AIAgentService.generate_data_story(df, request.file_id, title="数据分析报告")
    quality = CleaningService.get_data_quality_report(df)
    stats = AnalysisService.descriptive_statistics(df)

    html_content = _build_html_report(story, quality, stats, "数据分析报告")
    return HTMLResponse(
        content=html_content,
        headers={"Content-Disposition": 'attachment; filename="report.html"'},
    )


def _build_html_report(story, quality, stats, title):
    """生成HTML报告"""
    overall = stats.get("overall", {})
    score = quality.get("overall_score", 0)
    bar_class = "quality-excellent" if score >= 90 else "quality-good" if score >= 70 else "quality-warning"

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>{title}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:linear-gradient(135deg,#0f0c29,#302b63);color:#e2e8f0;line-height:1.6;min-height:100vh}}
.container{{max-width:900px;margin:0 auto;padding:40px 20px}}
.header{{text-align:center;padding:60px 0;border-bottom:2px solid rgba(99,102,241,0.5);margin-bottom:40px}}
.header h1{{font-size:2.2em;color:#6366f1}}
.section{{background:rgba(30,30,50,0.6);border:1px solid rgba(100,100,255,0.2);border-radius:16px;padding:30px;margin-bottom:24px}}
.section h2{{color:#6366f1;margin-bottom:16px}}
.footer{{text-align:center;padding:30px;color:#64748b;border-top:1px solid rgba(100,100,255,0.15);margin-top:40px}}
</style></head>
<body><div class="container">
<div class="header"><h1>{title}</h1><p style="color:#94a3b8;margin-top:8px">DataVision Pro 生成</p></div>
<div class="section"><h2>数据概览</h2>
<p>行数: {overall.get('total_rows',0):,} | 列数: {overall.get('total_columns',0)} | 缺失值: {overall.get('total_missing',0)}</p>
</div>
<div class="section"><h2>数据质量</h2><p>整体评分: <strong>{score}/100</strong></p>
<ul>{''.join(f'<li style="padding:4px 0">• {s}</li>' for s in quality.get('suggestions',[]))}</ul>
</div>
<div class="footer">DataVision Pro - 交互式数据分析系统</div>
</div></body></html>"""
    return html
