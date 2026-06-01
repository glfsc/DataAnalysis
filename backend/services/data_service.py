"""
数据处理服务
负责文件读取、数据加载、基本数据操作
"""
import uuid
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

from config import UPLOAD_DIR, MAX_FILE_SIZE, ALLOWED_EXTENSIONS

logger = logging.getLogger(__name__)


class DataService:
    """数据处理服务类：管理文件加载、数据预览和基本信息获取"""

    # 缓存已加载的DataFrame，避免重复读取
    _data_cache: Dict[str, pd.DataFrame] = {}

    @classmethod
    def get_dataframe(cls, file_id: str) -> Optional[pd.DataFrame]:
        """从缓存获取DataFrame"""
        return cls._data_cache.get(file_id)

    @classmethod
    def set_dataframe(cls, file_id: str, df: pd.DataFrame) -> None:
        """将DataFrame存入缓存"""
        # 限制缓存大小
        if len(cls._data_cache) > 20:
            oldest_key = next(iter(cls._data_cache))
            del cls._data_cache[oldest_key]
        cls._data_cache[file_id] = df

    @classmethod
    def remove_dataframe(cls, file_id: str) -> None:
        """从缓存移除DataFrame"""
        cls._data_cache.pop(file_id, None)

    @classmethod
    def validate_file(cls, filename: str, file_size: int) -> Tuple[bool, str]:
        """
        验证上传文件的格式和大小

        Args:
            filename: 文件名
            file_size: 文件大小（字节）

        Returns:
            (是否有效, 错误消息)
        """
        # 检查扩展名
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            return False, f"不支持的文件格式: {ext}，仅支持 {', '.join(ALLOWED_EXTENSIONS)}"

        # 检查文件大小
        if file_size > MAX_FILE_SIZE:
            max_mb = MAX_FILE_SIZE / (1024 * 1024)
            return False, f"文件大小超过限制 ({max_mb:.0f}MB)"

        return True, ""

    @classmethod
    def load_file(cls, content: bytes, filename: str) -> pd.DataFrame:
        """
        根据文件类型加载数据到DataFrame

        Args:
            content: 文件二进制内容
            filename: 文件名

        Returns:
            pandas DataFrame对象

        Raises:
            ValueError: 文件格式不支持或读取失败
        """
        import io

        ext = Path(filename).suffix.lower()
        try:
            if ext == ".csv":
                # 尝试自动检测编码和分隔符
                try:
                    df = pd.read_csv(io.BytesIO(content), encoding="utf-8")
                except UnicodeDecodeError:
                    df = pd.read_csv(io.BytesIO(content), encoding="gbk")
            elif ext in (".xlsx", ".xls"):
                df = pd.read_excel(io.BytesIO(content))
            else:
                raise ValueError(f"不支持的文件格式: {ext}")

            if df.empty:
                raise ValueError("文件内容为空")

            logger.info(f"成功加载文件: {filename}, 形状: {df.shape}")
            return df

        except Exception as e:
            logger.error(f"文件加载失败: {filename}, 错误: {str(e)}")
            raise ValueError(f"文件读取失败: {str(e)}")

    @classmethod
    def get_preview(cls, df: pd.DataFrame, rows: int = 10) -> List[Dict[str, Any]]:
        """
        获取数据预览（前N行）

        Args:
            df: DataFrame对象
            rows: 预览行数

        Returns:
            字典列表形式的预览数据
        """
        preview_df = df.head(rows)
        # 将 NaN / Inf 替换为 None，确保 JSON 可序列化
        preview_df = preview_df.replace([float('inf'), float('-inf')], None)
        preview_df = preview_df.where(preview_df.notna(), None)
        records = preview_df.to_dict("records")
        # 将 numpy 类型转换为 Python 原生类型
        for row in records:
            for k, v in row.items():
                if v is not None and hasattr(v, 'item'):
                    row[k] = v.item()
        return records

    @classmethod
    def get_info(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        获取DataFrame的基本信息

        Args:
            df: DataFrame对象

        Returns:
            包含行数、列数、列类型等信息的字典
        """
        # 获取列类型
        column_types = {}
        for col in df.columns:
            dtype = df[col].dtype
            if pd.api.types.is_integer_dtype(dtype):
                column_types[col] = "integer"
            elif pd.api.types.is_float_dtype(dtype):
                column_types[col] = "float"
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                column_types[col] = "datetime"
            elif pd.api.types.is_bool_dtype(dtype):
                column_types[col] = "boolean"
            else:
                column_types[col] = "string"

        # 获取缺失值统计
        missing = df.isnull().sum().to_dict()
        missing = {k: int(v) for k, v in missing.items() if v > 0}

        # 获取数值列的基本统计
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        return {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "column_types": column_types,
            "numeric_columns": numeric_cols,
            "missing_summary": missing,
            "memory_usage": int(df.memory_usage(deep=True).sum()),
        }

    @classmethod
    def get_numeric_columns(cls, df: pd.DataFrame) -> List[str]:
        """获取数值列名列表"""
        return df.select_dtypes(include=[np.number]).columns.tolist()

    @classmethod
    def get_categorical_columns(cls, df: pd.DataFrame) -> List[str]:
        """获取分类/字符串列名列表"""
        return df.select_dtypes(include=["object", "category"]).columns.tolist()

    @classmethod
    def save_dataframe(cls, df: pd.DataFrame, file_id: str, cleaned: bool = False) -> str:
        """
        保存DataFrame到磁盘

        Args:
            df: 要保存的DataFrame
            file_id: 关联的文件ID
            cleaned: 是否为清洗后的数据

        Returns:
            保存的文件路径
        """
        suffix = "_cleaned" if cleaned else ""
        filepath = UPLOAD_DIR / f"{file_id}{suffix}.csv"
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        logger.info(f"DataFrame已保存: {filepath}")
        return str(filepath)
