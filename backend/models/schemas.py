"""
Pydantic数据模型定义
用于API请求/响应的数据验证和序列化
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime


# ============ 文件上传相关模型 ============

class FileInfo(BaseModel):
    """文件基本信息"""
    file_id: str = Field(..., description="文件唯一标识")
    filename: str = Field(..., description="原始文件名")
    file_type: str = Field(..., description="文件类型")
    file_size: int = Field(..., description="文件大小（字节）")
    rows: int = Field(..., description="数据行数")
    columns: int = Field(..., description="数据列数")
    column_types: Dict[str, str] = Field(default_factory=dict, description="列数据类型映射")


class UploadResponse(BaseModel):
    """上传响应模型"""
    file_id: str = Field(..., description="文件ID")
    filename: str = Field(..., description="文件名")
    preview: List[Dict[str, Any]] = Field(..., description="数据预览（前10行）")
    info: FileInfo = Field(..., description="文件基本信息")
    message: str = Field("上传成功", description="状态消息")


# ============ 数据清洗相关模型 ============

class CleaningParams(BaseModel):
    """数据清洗参数"""
    handle_missing: str = Field(
        "none",
        description="缺失值处理方式：none/delete/mean/median/mode"
    )
    drop_duplicates: bool = Field(False, description="是否删除重复行")
    columns_to_clean: Optional[List[str]] = Field(None, description="需要清洗的列名列表")
    outlier_method: Optional[str] = Field(
        None,
        description="异常值检测方法：iqr/zscore/none"
    )
    outlier_threshold: Optional[float] = Field(3.0, description="异常值阈值")
    convert_types: Optional[Dict[str, str]] = Field(
        None,
        description="列类型转换映射 {列名: 目标类型}"
    )

    @validator("handle_missing")
    def validate_missing_method(cls, v: str) -> str:
        allowed = {"none", "delete", "mean", "median", "mode"}
        if v not in allowed:
            raise ValueError(f"缺失值处理方法必须为: {', '.join(allowed)}")
        return v

    @validator("outlier_method")
    def validate_outlier_method(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed = {"iqr", "zscore", "none"}
            if v not in allowed:
                raise ValueError(f"异常值检测方法必须为: {', '.join(allowed)}")
        return v


class CleaningSummary(BaseModel):
    """清洗统计摘要"""
    original_rows: int = Field(..., description="原始行数")
    cleaned_rows: int = Field(..., description="清洗后行数")
    missing_handled: int = Field(0, description="处理的缺失值数量")
    duplicates_removed: int = Field(0, description="删除的重复行数")
    outliers_detected: int = Field(0, description="检测到的异常值数量")
    columns_modified: List[str] = Field(default_factory=list, description="修改的列")


class CleaningResponse(BaseModel):
    """清洗响应模型"""
    file_id: str = Field(..., description="文件ID")
    preview: List[Dict[str, Any]] = Field(..., description="清洗后数据预览")
    summary: CleaningSummary = Field(..., description="清洗统计摘要")
    cleaned_file_id: str = Field(..., description="清洗后文件ID")


# ============ 数据分析相关模型 ============

class StatisticsResponse(BaseModel):
    """描述性统计响应"""
    file_id: str = Field(..., description="文件ID")
    statistics: Dict[str, Any] = Field(..., description="统计结果")
    data_types: Dict[str, str] = Field(..., description="数据类型")


class CorrelationRequest(BaseModel):
    """相关性分析请求"""
    columns: Optional[List[str]] = Field(None, description="参与分析的列名")
    method: str = Field("pearson", description="相关性方法：pearson/spearman/kendall")


class CorrelationResponse(BaseModel):
    """相关性分析响应"""
    file_id: str = Field(..., description="文件ID")
    correlation_matrix: List[List[float]] = Field(..., description="相关性矩阵")
    column_names: List[str] = Field(..., description="列名列表")
    heatmap_config: Dict[str, Any] = Field(..., description="热力图配置")


class ClusterRequest(BaseModel):
    """聚类分析请求"""
    n_clusters: int = Field(3, ge=1, le=20, description="聚类数量")
    features: List[str] = Field(..., description="用于聚类的特征列")
    scale_data: bool = Field(True, description="是否标准化数据")


class ClusterResponse(BaseModel):
    """聚类分析响应"""
    file_id: str = Field(..., description="文件ID")
    cluster_labels: List[int] = Field(..., description="聚类标签")
    cluster_centers: List[List[float]] = Field(..., description="聚类中心")
    cluster_sizes: Dict[int, int] = Field(..., description="各簇样本数")
    inertia: float = Field(..., description="聚类惯性")
    scatter_data: Dict[str, Any] = Field(..., description="散点图数据")


class RegressionRequest(BaseModel):
    """回归分析请求"""
    features: List[str] = Field(..., description="特征列名")
    target: str = Field(..., description="目标列名")
    test_size: float = Field(0.2, ge=0.1, le=0.5, description="测试集比例")


class RegressionResponse(BaseModel):
    """回归分析响应"""
    file_id: str = Field(..., description="文件ID")
    coefficients: Dict[str, float] = Field(..., description="回归系数")
    intercept: float = Field(..., description="截距")
    r2_score: float = Field(..., description="R²决定系数")
    mse: float = Field(..., description="均方误差")
    predictions: List[float] = Field(..., description="预测值列表")
    actual: List[float] = Field(..., description="实际值列表")
    feature_importance: Dict[str, float] = Field(..., description="特征重要性")


class GroupByRequest(BaseModel):
    """分组聚合请求"""
    group_column: str = Field(..., description="分组列名")
    agg_columns: List[str] = Field(..., description="聚合列名")
    agg_funcs: List[str] = Field(["mean"], description="聚合函数列表")


# ============ 可视化相关模型 ============

class VisualizationRequest(BaseModel):
    """可视化请求"""
    chart_type: str = Field(..., description="图表类型")
    x_column: Optional[str] = Field(None, description="X轴列名")
    y_column: Optional[Union[str, List[str]]] = Field(None, description="Y轴列名")
    group_column: Optional[str] = Field(None, description="分组列名")
    title: Optional[str] = Field(None, description="图表标题")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="额外参数")

    @validator("chart_type")
    def validate_chart_type(cls, v: str) -> str:
        allowed = {
            "line", "bar", "pie", "scatter", "box", "heatmap",
            "radar", "histogram", "area", "funnel", "scatter3d"
        }
        if v not in allowed:
            raise ValueError(f"图表类型必须为: {', '.join(allowed)}")
        return v


class VisualizationResponse(BaseModel):
    """可视化响应"""
    chart_id: str = Field(..., description="图表ID")
    chart_type: str = Field(..., description="图表类型")
    echarts_option: Dict[str, Any] = Field(..., description="ECharts配置对象")
    data_summary: Optional[Dict[str, Any]] = Field(None, description="数据摘要")


# ============ 导出相关模型 ============

class ExportRequest(BaseModel):
    """导出请求"""
    export_type: str = Field(..., description="导出类型：data/chart/report")
    file_id: Optional[str] = Field(None, description="文件ID")
    chart_id: Optional[str] = Field(None, description="图表ID")
    format: str = Field("csv", description="导出格式")


# ============ AI助手相关模型 ============

class AIQueryRequest(BaseModel):
    """AI助手查询请求"""
    query: str = Field(..., min_length=1, max_length=500, description="用户自然语言查询")
    file_id: str = Field(..., description="当前文件ID")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")


class AIQueryResponse(BaseModel):
    """AI助手查询响应"""
    answer: str = Field(..., description="AI回答")
    suggested_action: Optional[str] = Field(None, description="建议的操作")
    chart_recommendation: Optional[Dict[str, Any]] = Field(None, description="图表推荐")
    insights: List[str] = Field(default_factory=list, description="洞察发现")


class DataStoryRequest(BaseModel):
    """数据故事请求"""
    sections: Optional[List[str]] = Field(None, description="报告章节")
    title: Optional[str] = Field(None, description="报告标题")


# ============ 通用响应模型 ============

class ErrorResponse(BaseModel):
    """错误响应"""
    detail: str = Field(..., description="错误详情")
    error_code: Optional[str] = Field(None, description="错误代码")


class SuccessResponse(BaseModel):
    """成功响应"""
    message: str = Field("操作成功", description="状态消息")
    data: Optional[Dict[str, Any]] = Field(None, description="返回数据")


# ============ 用户认证相关模型 ============

class RegisterRequest(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    password_confirm: str = Field(..., min_length=6, max_length=100, description="确认密码")

    @validator("password_confirm")
    def passwords_match(cls, v: str, values: dict) -> str:
        if "password" in values and v != values["password"]:
            raise ValueError("两次输入的密码不一致")
        return v

    @validator("username")
    def username_valid(cls, v: str) -> str:
        import re
        if not re.match(r'^[a-zA-Z0-9_一-鿿]+$', v):
            raise ValueError("用户名只能包含字母、数字、下划线和中文")
        return v


class LoginRequest(BaseModel):
    """用户登录请求"""
    username: str = Field(..., min_length=1, description="用户名")
    password: str = Field(..., min_length=1, description="密码")
    remember: bool = Field(False, description="是否记住登录（免登录）")


class RecoverRequest(BaseModel):
    """密码找回请求"""
    username: str = Field(..., min_length=1, description="用户名")


class UpdateUserRequest(BaseModel):
    """更新用户信息请求"""
    email: Optional[str] = Field(None, max_length=120, description="邮箱")
    display_name: Optional[str] = Field(None, max_length=100, description="显示名称")
    avatar_url: Optional[str] = Field(None, max_length=500, description="头像URL")
    password: Optional[str] = Field(None, min_length=6, max_length=100, description="新密码（留空不修改）")
    password_confirm: Optional[str] = Field(None, description="确认新密码")

    @validator("password_confirm")
    def passwords_match(cls, v: str, values: dict) -> str:
        if v is not None and "password" in values and v != values.get("password"):
            raise ValueError("两次输入的密码不一致")
        return v


class UserInfo(BaseModel):
    """用户信息响应"""
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field("", description="邮箱")
    display_name: str = Field("", description="显示名称")
    avatar_url: str = Field("", description="头像URL")
    is_admin: bool = Field(False, description="是否为管理员")
    created_at: Optional[str] = Field(None, description="注册时间")


class AuthResponse(BaseModel):
    """认证响应"""
    token: str = Field(..., description="会话令牌")
    user: UserInfo = Field(..., description="用户信息")
    message: str = Field("操作成功", description="状态消息")
