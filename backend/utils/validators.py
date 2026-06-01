"""
数据验证工具模块
提供列名验证、参数校验等功能
"""
from typing import Any, Dict, List, Optional, Union

import pandas as pd


def validate_columns_exist(df: pd.DataFrame, columns: List[str]) -> List[str]:
    """
    验证列名是否存在于DataFrame中

    Args:
        df: DataFrame对象
        columns: 待验证的列名列表

    Returns:
        不存在的列名列表
    """
    return [col for col in columns if col not in df.columns]


def validate_numeric_columns(df: pd.DataFrame, columns: List[str]) -> List[str]:
    """
    验证列是否为数值类型

    Args:
        df: DataFrame对象
        columns: 列名列表

    Returns:
        非数值类型的列名列表
    """
    return [col for col in columns if col in df.columns and not pd.api.types.is_numeric_dtype(df[col])]


def validate_chart_params(chart_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证图表参数

    Args:
        chart_type: 图表类型
        params: 图表参数

    Returns:
        验证后的参数（过滤无效值）
    """
    valid_params = {}

    # 通用参数
    if "title" in params and params["title"]:
        valid_params["title"] = str(params["title"])

    if "x_rotate" in params:
        try:
            valid_params["x_rotate"] = int(params["x_rotate"])
        except (ValueError, TypeError):
            pass

    # 图表特定参数
    if chart_type in ("line", "area"):
        if "smooth" in params:
            valid_params["smooth"] = bool(params["smooth"])
        if "show_area" in params:
            valid_params["show_area"] = bool(params["show_area"])

    elif chart_type == "pie":
        if "radius" in params:
            valid_params["radius"] = params["radius"]
        if "rose_type" in params:
            valid_params["rose_type"] = params["rose_type"]
        if "top_n" in params:
            try:
                valid_params["top_n"] = min(int(params["top_n"]), 50)
            except (ValueError, TypeError):
                pass

    elif chart_type == "radar":
        if "max_indicators" in params:
            try:
                valid_params["max_indicators"] = min(int(params["max_indicators"]), 12)
            except (ValueError, TypeError):
                pass
        if "max_series" in params:
            try:
                valid_params["max_series"] = min(int(params["max_series"]), 10)
            except (ValueError, TypeError):
                pass

    elif chart_type == "histogram":
        if "bins" in params:
            try:
                valid_params["bins"] = min(int(params["bins"]), 100)
            except (ValueError, TypeError):
                pass

    elif chart_type == "funnel":
        if "top_n" in params:
            try:
                valid_params["top_n"] = min(int(params["top_n"]), 20)
            except (ValueError, TypeError):
                pass

    return valid_params


def validate_cluster_params(n_clusters: int, n_samples: int) -> None:
    """
    验证聚类参数

    Args:
        n_clusters: 聚类数
        n_samples: 样本数

    Raises:
        ValueError: 参数无效
    """
    if not isinstance(n_clusters, int) or n_clusters < 1:
        raise ValueError("聚类数量必须为正整数")

    if n_clusters > n_samples:
        raise ValueError(f"聚类数量({n_clusters})不能大于样本数量({n_samples})")

    if n_clusters > 20:
        raise ValueError("聚类数量不能超过20")


def sanitize_string(value: str, max_length: int = 255) -> str:
    """
    清洗字符串输入，防止注入

    Args:
        value: 输入字符串
        max_length: 最大长度

    Returns:
        清洗后的字符串
    """
    if not isinstance(value, str):
        return ""
    return value.strip()[:max_length]


def is_safe_filename(filename: str) -> bool:
    """
    检查文件名是否安全

    Args:
        filename: 文件名

    Returns:
        是否安全
    """
    dangerous_patterns = ["..", "/", "\\", "\0"]
    return not any(p in filename for p in dangerous_patterns)
