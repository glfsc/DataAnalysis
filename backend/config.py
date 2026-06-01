"""
系统配置文件
包含数据库、文件上传、分析参数等全局配置
"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent

# 数据库配置
DATABASE_URL = f"sqlite:///{BASE_DIR}/data_analysis.db"

# 文件上传配置
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

# 静态文件配置 — 指向前端目录
STATIC_DIR = BASE_DIR.parent / "frontend"
TEMPLATE_DIR = STATIC_DIR

# 分析配置
DEFAULT_CLUSTER_N = 3
MAX_CLUSTER_N = 10
CORRELATION_THRESHOLD = 0.7

# 可视化配置
DEFAULT_CHART_THEME = "dark"
CHART_THEMES = ["dark", "light", "vintage"]

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 服务端口
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# AI助手配置
AI_ENABLED = True
AI_MAX_HISTORY = 20
