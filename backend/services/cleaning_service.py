"""
数据清洗服务
处理缺失值、重复值、异常值检测和数据类型转换
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np
from scipy import stats

from models.schemas import CleaningParams, CleaningSummary

logger = logging.getLogger(__name__)


class CleaningService:
    """数据清洗服务类：提供全面的数据清洗功能"""

    @classmethod
    def clean_data(cls, df: pd.DataFrame, params: CleaningParams) -> Tuple[pd.DataFrame, CleaningSummary]:
        """
        根据清洗参数清洗数据

        Args:
            df: 原始DataFrame
            params: 清洗参数配置

        Returns:
            (清洗后的DataFrame, 清洗统计摘要)
        """
        original_rows = len(df)
        summary = CleaningSummary(
            original_rows=original_rows,
            cleaned_rows=original_rows,
            missing_handled=0,
            duplicates_removed=0,
            outliers_detected=0,
            columns_modified=[],
        )

        df_clean = df.copy()

        # 1. 处理缺失值
        if params.handle_missing and params.handle_missing != "none":
            df_clean, missing_count = cls._handle_missing_values(
                df_clean, params.handle_missing, params.columns_to_clean
            )
            summary.missing_handled = missing_count

        # 2. 删除重复值
        if params.drop_duplicates:
            before = len(df_clean)
            df_clean = df_clean.drop_duplicates()
            summary.duplicates_removed = before - len(df_clean)

        # 3. 数据类型转换
        if params.convert_types:
            for col, target_type in params.convert_types.items():
                if col in df_clean.columns:
                    try:
                        df_clean[col] = cls._convert_column_type(df_clean[col], target_type)
                        summary.columns_modified.append(col)
                    except Exception as e:
                        logger.warning(f"列 {col} 类型转换失败: {str(e)}")

        # 4. 异常值检测
        if params.outlier_method and params.outlier_method != "none":
            numeric_cols = params.columns_to_clean or df_clean.select_dtypes(
                include=[np.number]
            ).columns.tolist()
            outlier_mask = cls._detect_outliers(
                df_clean[numeric_cols],
                method=params.outlier_method,
                threshold=params.outlier_threshold or 3.0,
            )
            summary.outliers_detected = int(outlier_mask.any(axis=1).sum())

        summary.cleaned_rows = len(df_clean)

        logger.info(
            f"数据清洗完成: {original_rows}行 → {summary.cleaned_rows}行, "
            f"处理缺失值{summary.missing_handled}个, "
            f"删除重复{summary.duplicates_removed}行, "
            f"检测异常值{summary.outliers_detected}个"
        )

        return df_clean, summary

    @classmethod
    def _handle_missing_values(
        cls,
        df: pd.DataFrame,
        method: str,
        columns: Optional[List[str]] = None,
    ) -> Tuple[pd.DataFrame, int]:
        """
        处理缺失值

        Args:
            df: DataFrame对象
            method: 处理方法（delete/mean/median/mode）
            columns: 要处理的列（None表示所有列）

        Returns:
            (处理后的DataFrame, 处理的缺失值数量)
        """
        target_cols = columns or df.columns.tolist()
        before = df[target_cols].isnull().sum().sum()

        if method == "delete":
            df = df.dropna(subset=target_cols)
        else:
            for col in target_cols:
                if col not in df.columns:
                    continue
                if df[col].isnull().sum() > 0:
                    if method == "mean" and pd.api.types.is_numeric_dtype(df[col]):
                        fill_val = df[col].mean()
                    elif method == "median" and pd.api.types.is_numeric_dtype(df[col]):
                        fill_val = df[col].median()
                    elif method == "mode":
                        mode_vals = df[col].mode()
                        fill_val = mode_vals[0] if len(mode_vals) > 0 else df[col].iloc[0]
                    else:
                        continue
                    df[col] = df[col].fillna(fill_val)

        after = df[target_cols].isnull().sum().sum() if method != "delete" else 0
        handled = int(before - after)

        return df, handled

    @classmethod
    def _detect_outliers(
        cls,
        df_numeric: pd.DataFrame,
        method: str = "iqr",
        threshold: float = 3.0,
    ) -> pd.DataFrame:
        """
        检测异常值

        Args:
            df_numeric: 仅包含数值列的DataFrame
            method: 检测方法（iqr/zscore）
            threshold: 阈值

        Returns:
            布尔掩码DataFrame（True表示异常值）
        """
        outlier_mask = pd.DataFrame(False, index=df_numeric.index, columns=df_numeric.columns)

        for col in df_numeric.columns:
            col_data = df_numeric[col].dropna()
            if len(col_data) < 4:
                continue

            if method == "iqr":
                Q1 = col_data.quantile(0.25)
                Q3 = col_data.quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - threshold * IQR
                upper = Q3 + threshold * IQR
                outlier_mask[col] = (df_numeric[col] < lower) | (df_numeric[col] > upper)

            elif method == "zscore":
                z_scores = np.abs(stats.zscore(col_data, nan_policy="omit"))
                # 将z-score映射回原始索引
                outlier_mask.loc[col_data.index, col] = z_scores > threshold

        return outlier_mask

    @classmethod
    def _convert_column_type(cls, series: pd.Series, target_type: str) -> pd.Series:
        """
        转换列的数据类型

        Args:
            series: 列数据
            target_type: 目标类型（int/float/string/datetime）

        Returns:
            转换后的Series
        """
        type_map = {
            "int": "Int64",
            "integer": "Int64",
            "float": "float64",
            "double": "float64",
            "string": "str",
            "str": "str",
            "datetime": "datetime64[ns]",
            "date": "datetime64[ns]",
        }

        dtype = type_map.get(target_type.lower(), target_type)

        if dtype in ("Int64", "float64"):
            return pd.to_numeric(series, errors="coerce")
        elif dtype == "datetime64[ns]":
            return pd.to_datetime(series, errors="coerce")
        else:
            return series.astype(str)

    @classmethod
    def get_data_quality_report(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        生成数据质量评估报告

        Args:
            df: DataFrame对象

        Returns:
            质量报告字典，包含完整性、准确性等评分
        """
        total_cells = df.size
        missing_cells = int(df.isnull().sum().sum())
        duplicate_rows = int(df.duplicated().sum())

        # 完整性评分（缺失值比例）
        completeness = round((1 - missing_cells / max(total_cells, 1)) * 100, 1)

        # 一致性评分（检查数值列是否有混合类型）
        consistency_issues = 0
        for col in df.select_dtypes(include=["object"]).columns:
            # 检查是否可能是数值列
            numeric_ratio = pd.to_numeric(df[col], errors="coerce").notna().mean()
            if numeric_ratio > 0.8 and numeric_ratio < 1.0:
                consistency_issues += 1
        consistency = round(max(0, 100 - consistency_issues * 10), 1)

        # 唯一性评分
        uniqueness = round((1 - duplicate_rows / max(len(df), 1)) * 100, 1)

        # 整体评分
        overall = round(np.mean([completeness, consistency, uniqueness]), 1)

        # 生成优化建议
        suggestions = []
        if missing_cells > 0:
            suggestions.append(f"检测到{missing_cells}个缺失值（{round(missing_cells/max(total_cells,1)*100,1)}%），建议进行缺失值处理")
        if duplicate_rows > 0:
            suggestions.append(f"检测到{duplicate_rows}行重复数据，建议删除重复行")
        if consistency_issues > 0:
            suggestions.append(f"检测到{consistency_issues}列存在数据类型不一致问题，建议检查并转换")
        if not suggestions:
            suggestions.append("数据质量良好，无需特殊处理")

        return {
            "completeness": completeness,
            "consistency": consistency,
            "uniqueness": uniqueness,
            "overall_score": overall,
            "missing_cells": missing_cells,
            "duplicate_rows": duplicate_rows,
            "total_cells": total_cells,
            "suggestions": suggestions,
        }
