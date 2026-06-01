"""
ORM数据库模型定义
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean
from database import Base


class UploadedFile(Base):
    """已上传文件记录表"""
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(String(36), unique=True, nullable=False, index=True, comment="文件唯一标识UUID")
    filename = Column(String(255), nullable=False, comment="原始文件名")
    file_path = Column(String(500), nullable=False, comment="服务器存储路径")
    file_type = Column(String(10), nullable=False, comment="文件类型（csv/excel）")
    file_size = Column(Integer, nullable=False, comment="文件大小（字节）")
    rows = Column(Integer, default=0, comment="数据行数")
    columns = Column(Integer, default=0, comment="数据列数")
    column_info = Column(JSON, default=dict, comment="列信息（名称和类型）")
    upload_time = Column(DateTime, default=datetime.utcnow, comment="上传时间")
    is_cleaned = Column(Boolean, default=False, comment="是否已清洗")
    cleaned_path = Column(String(500), nullable=True, comment="清洗后文件路径")


class AnalysisResult(Base):
    """分析结果记录表"""
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(String(36), nullable=False, index=True, comment="关联文件ID")
    analysis_type = Column(String(50), nullable=False, comment="分析类型")
    parameters = Column(JSON, default=dict, comment="分析参数")
    result_data = Column(JSON, default=dict, comment="分析结果数据")
    created_time = Column(DateTime, default=datetime.utcnow, comment="创建时间")


class ChartConfig(Base):
    """图表配置记录表"""
    __tablename__ = "chart_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chart_id = Column(String(36), unique=True, nullable=False, index=True, comment="图表唯一标识")
    file_id = Column(String(36), nullable=False, index=True, comment="关联文件ID")
    chart_type = Column(String(50), nullable=False, comment="图表类型")
    title = Column(String(255), nullable=False, comment="图表标题")
    config = Column(JSON, default=dict, comment="ECharts配置")
    created_time = Column(DateTime, default=datetime.utcnow, comment="创建时间")
