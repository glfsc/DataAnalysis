# DataVision Pro - Dockerfile
# 基于 Miniconda3 构建 dataanalysis 环境
FROM continuumio/miniconda3:latest

# 设置工作目录
WORKDIR /app

# 创建 conda 环境 (Python 3.10)
RUN conda create -n dataanalysis python=3.10 -y && \
    conda clean -afy

# 将 conda 环境加入 PATH
ENV PATH=/opt/conda/envs/dataanalysis/bin:$PATH

# 先复制 requirements.txt，利用 Docker 层缓存
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目所有文件
COPY . .

# 创建持久化数据目录（运行时由 Railway 卷挂载覆盖）
# 在 Railway 中配置卷挂载到 /data，并设置环境变量 DATA_DIR=/data
RUN mkdir -p /data/uploads/avatars

# 启动脚本权限
RUN chmod +x start.sh

# 暴露端口（Railway 通过 PORT 环境变量注入）
EXPOSE 8000

# 设置默认环境变量
ENV DATA_DIR=/data

# 启动服务
CMD ["./start.sh"]
