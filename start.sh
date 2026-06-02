#!/bin/bash
# Data Analysis System - 启动脚本
# 兼容 Railway 部署：正确读取 PORT 环境变量

PORT="${PORT:-8000}"
echo "启动 Data Analysis System on port $PORT"
exec uvicorn backend.main:app --host 0.0.0.0 --port "$PORT"
