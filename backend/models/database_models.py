"""
ORM数据库模型定义
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean, ForeignKey
from database import Base


class User(Base):
    """用户账户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    password_hash = Column(String(128), nullable=False, comment="密码哈希（PBKDF2-SHA256）")
    salt = Column(String(64), nullable=False, comment="密码盐值")
    email = Column(String(120), default="", comment="邮箱")
    avatar_url = Column(String(500), default="", comment="头像URL")
    display_name = Column(String(100), default="", comment="显示名称")
    is_admin = Column(Boolean, default=False, comment="是否为管理员")
    created_at = Column(DateTime, default=datetime.utcnow, comment="注册时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")


class UserSession(Base):
    """用户会话令牌表"""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    token = Column(String(64), unique=True, nullable=False, index=True, comment="会话令牌")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    expires_at = Column(DateTime, nullable=False, comment="过期时间")


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
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True, comment="上传用户ID")


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


class AIConfig(Base):
    """AI模型配置表"""
    __tablename__ = "ai_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    name = Column(String(100), nullable=False, comment="配置方案名称")
    api_key = Column(String(500), nullable=False, comment="API Key")
    base_url = Column(String(500), nullable=False, comment="API地址URL")
    model_name = Column(String(200), nullable=False, comment="模型名称")
    is_enabled = Column(Boolean, default=False, comment="是否启用（同一用户只能启用一个）")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
