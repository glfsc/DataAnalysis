"""
DataVision Pro - 交互式数据分析系统
FastAPI应用入口

基于FastAPI + ECharts + SQLite的完整Web数据分析平台
"""
import logging
import sys
from pathlib import Path

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import HOST, PORT, LOG_LEVEL, STATIC_DIR, LOG_FORMAT
from database import init_db

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, "INFO"),
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path(__file__).parent / "app.log", encoding="utf-8"),
    ],
)

# 修复 Windows GBK 编码下 StreamHandler 无法输出 emoji 的问题
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    logger.info("=" * 60)
    logger.info("DataVision Pro 正在启动...")
    logger.info("=" * 60)

    try:
        init_db()
        logger.info("数据库初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")

    if STATIC_DIR.exists():
        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            logger.info(f"前端文件就绪: {index_file}")
        else:
            logger.warning("前端index.html未找到，请确保static目录包含完整前端文件")

    logger.info(f"API文档地址: http://{HOST}:{PORT}/docs")
    logger.info(f"前端地址: http://{HOST}:{PORT}/")
    logger.info("=" * 60)

    yield

    # 关闭
    logger.info("DataVision Pro 正在关闭...")
    from services.data_service import DataService
    DataService._data_cache.clear()


# 创建FastAPI应用实例
app = FastAPI(
    title="DataVision Pro - 交互式数据分析系统",
    description="""
## 功能模块

- **数据上传**: 支持CSV和Excel文件上传（最大10MB）
- **数据清洗**: 缺失值处理、重复值删除、异常值检测、类型转换
- **数据分析**: 描述性统计、相关性分析、分组聚合、机器学习
- **数据可视化**: 支持12种ECharts图表类型，支持交互联动
- **结果导出**: 导出数据、图表和分析报告
- **AI智能助手**: 自然语言查询、自动洞察发现、智能图表推荐

## 技术栈

- FastAPI + Pandas + Scikit-learn
- ECharts + 玻璃拟态UI设计
- SQLite + SQLAlchemy ORM
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    contact={
        "name": "DataVision Pro Team",
        "url": "https://github.com/datavision-pro",
    },
    license_info={
        "name": "MIT",
    },
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求参数验证异常处理"""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append(f"{field}: {error['msg']}")
    return JSONResponse(
        status_code=422,
        content={"detail": "参数验证失败", "errors": errors},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"服务器内部错误: {str(exc)}"},
    )


# ============ 注册API路由 ============

from api.upload import router as upload_router
from api.cleaning import router as cleaning_router
from api.analysis import router as analysis_router
from api.visualization import router as visualization_router
from api.export import router as export_router
from api.ai_agent import router as ai_agent_router
from api.ai_config import router as ai_config_router
from api.data_crud import router as data_crud_router
from api.auth import router as auth_router

app.include_router(upload_router)
app.include_router(cleaning_router)
app.include_router(analysis_router)
app.include_router(visualization_router)
app.include_router(export_router)
app.include_router(ai_agent_router)
app.include_router(ai_config_router)
app.include_router(data_crud_router)
app.include_router(auth_router)

# ============ 静态文件服务 ============

# 挂载静态文件目录
if STATIC_DIR.exists():
    # 挂载CSS、JS和库文件夹
    css_dir = STATIC_DIR / "css"
    js_dir = STATIC_DIR / "js"
    lib_dir = STATIC_DIR / "lib"

    if css_dir.exists():
        app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")
    if js_dir.exists():
        app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")
    if lib_dir.exists():
        app.mount("/lib", StaticFiles(directory=str(lib_dir)), name="lib")

# 挂载上传目录（头像等）
from config import UPLOAD_DIR
if UPLOAD_DIR.exists():
    app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.get("/", include_in_schema=False)
async def serve_frontend():
    """提供前端主页面"""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {
        "message": "DataVision Pro API服务正在运行",
        "docs": "/docs",
        "frontend": "请确保static/index.html存在",
    }


@app.get("/api/health", tags=["系统"], summary="健康检查")
async def health_check():
    """系统健康检查接口"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "DataVision Pro",
        "uptime": "running",
    }


@app.get("/api/info", tags=["系统"], summary="系统信息")
async def system_info():
    """获取系统配置信息"""
    from config import MAX_FILE_SIZE, ALLOWED_EXTENSIONS
    return {
        "name": "DataVision Pro",
        "version": "1.0.0",
        "max_file_size_mb": MAX_FILE_SIZE / (1024 * 1024),
        "allowed_extensions": list(ALLOWED_EXTENSIONS),
        "supported_charts": [
            "bar", "line", "pie", "area"
        ],
        "features": [
            "data_upload", "data_cleaning", "statistical_analysis",
            "machine_learning", "data_visualization", "ai_assistant",
            "report_export", "anomaly_detection", "time_series_forecast",
        ],
    }


# ============ 启动入口 ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=True,
        log_level=LOG_LEVEL.lower(),
    )
