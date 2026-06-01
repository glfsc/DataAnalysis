"""
数据分析服务
提供描述性统计、相关性分析、分组聚合等功能
"""
import logging
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class AnalysisService:
    """数据分析服务类：提供全面的统计分析功能"""

    @classmethod
    def descriptive_statistics(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        计算描述性统计

        Args:
            df: DataFrame对象

        Returns:
            包含各项统计指标的字典
        """
        # 数值列统计
        numeric_df = df.select_dtypes(include=[np.number])
        numeric_stats = {}

        if not numeric_df.empty:
            desc = numeric_df.describe(percentiles=[0.25, 0.5, 0.75]).to_dict()

            # 添加更多统计量
            for col in numeric_df.columns:
                col_stats = desc.get(col, {})
                col_stats["variance"] = float(numeric_df[col].var())
                col_stats["skewness"] = float(numeric_df[col].skew())
                col_stats["kurtosis"] = float(numeric_df[col].kurtosis())
                col_stats["unique"] = int(numeric_df[col].nunique())
                col_stats["missing"] = int(numeric_df[col].isnull().sum())
                col_stats["missing_pct"] = round(
                    numeric_df[col].isnull().sum() / max(len(df), 1) * 100, 2
                )
                numeric_stats[col] = col_stats

        # 非数值列统计
        categorical_stats = {}
        for col in df.select_dtypes(include=["object", "category"]).columns:
            col_data = df[col]
            categorical_stats[col] = {
                "count": int(len(col_data)),
                "unique": int(col_data.nunique()),
                "top": str(col_data.mode().iloc[0]) if not col_data.mode().empty else None,
                "freq": int(col_data.value_counts().iloc[0]) if len(col_data.value_counts()) > 0 else 0,
                "missing": int(col_data.isnull().sum()),
                "missing_pct": round(col_data.isnull().sum() / max(len(df), 1) * 100, 2),
            }

        # 总体统计
        overall = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "numeric_columns": len(numeric_stats),
            "categorical_columns": len(categorical_stats),
            "total_missing": int(df.isnull().sum().sum()),
            "total_duplicates": int(df.duplicated().sum()),
            "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
        }

        return {
            "overall": overall,
            "numeric": numeric_stats,
            "categorical": categorical_stats,
        }

    @classmethod
    def correlation_analysis(
        cls,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        method: str = "pearson",
    ) -> Dict[str, Any]:
        """
        计算相关性矩阵

        Args:
            df: DataFrame对象
            columns: 参与计算的列（None表示所有数值列）
            method: 相关性方法（pearson/spearman/kendall）

        Returns:
            相关性矩阵和热力图配置
        """
        if columns is None:
            numeric_df = df.select_dtypes(include=[np.number])
            columns = numeric_df.columns.tolist()
        else:
            numeric_df = df[columns].select_dtypes(include=[np.number])
            columns = [c for c in columns if c in numeric_df.columns]

        if len(columns) < 2:
            return {"correlation_matrix": [], "column_names": columns, "heatmap_config": {}}

        # 计算相关性矩阵
        corr_matrix = numeric_df[columns].corr(method=method)

        # 转换为可序列化格式
        matrix_data = corr_matrix.values.tolist()
        column_names = corr_matrix.columns.tolist()

        # 生成热力图ECharts配置数据
        heatmap_data = []
        for i, row_name in enumerate(column_names):
            for j, col_name in enumerate(column_names):
                heatmap_data.append([j, i, round(float(corr_matrix.iloc[i, j]), 4)])

        # 找出强相关对
        strong_correlations = []
        for i in range(len(column_names)):
            for j in range(i + 1, len(column_names)):
                corr_val = float(corr_matrix.iloc[i, j])
                if abs(corr_val) >= 0.5:
                    strong_correlations.append({
                        "pair": [column_names[i], column_names[j]],
                        "correlation": round(corr_val, 3),
                        "strength": "强" if abs(corr_val) >= 0.7 else "中等",
                        "direction": "正相关" if corr_val > 0 else "负相关",
                    })

        return {
            "correlation_matrix": matrix_data,
            "column_names": column_names,
            "heatmap_data": heatmap_data,
            "strong_correlations": strong_correlations,
        }

    @classmethod
    def groupby_analysis(
        cls,
        df: pd.DataFrame,
        group_column: str,
        agg_columns: List[str],
        agg_funcs: List[str],
    ) -> Dict[str, Any]:
        """
        分组聚合分析

        Args:
            df: DataFrame对象
            group_column: 分组列名
            agg_columns: 聚合列名
            agg_funcs: 聚合函数列表

        Returns:
            分组聚合结果
        """
        if group_column not in df.columns:
            raise ValueError(f"分组列 '{group_column}' 不存在")

        # 过滤有效的聚合列
        valid_agg_cols = [c for c in agg_columns if c in df.columns and c != group_column]
        if not valid_agg_cols:
            raise ValueError("没有有效的聚合列")

        # 过滤有效的聚合函数
        valid_funcs = ["mean", "sum", "count", "min", "max", "std", "var", "median"]
        funcs = [f for f in agg_funcs if f in valid_funcs]
        if not funcs:
            funcs = ["mean"]

        # 构建聚合字典
        agg_dict = {col: funcs for col in valid_agg_cols}

        # 执行分组聚合
        grouped = df.groupby(group_column).agg(agg_dict)

        # 转换为可序列化格式
        result_data = {}
        result_data["group_column"] = group_column
        result_data["groups"] = grouped.index.tolist()
        result_data["aggregations"] = {}

        for col in valid_agg_cols:
            result_data["aggregations"][col] = {}
            col_data = grouped[col]
            for func in funcs:
                values = col_data[func].tolist()
                # 处理numpy类型
                values = [float(v) if not (isinstance(v, float) and np.isnan(v)) else None for v in values]
                result_data["aggregations"][col][func] = values

        return result_data

    @classmethod
    def time_series_analysis(cls, df: pd.DataFrame, date_column: str, value_column: str) -> Dict[str, Any]:
        """
        时间序列分析（简易版）

        Args:
            df: DataFrame对象
            date_column: 日期列名
            value_column: 数值列名

        Returns:
            时间序列分析结果
        """
        df_ts = df.copy()
        df_ts[date_column] = pd.to_datetime(df_ts[date_column], errors="coerce")
        df_ts = df_ts.dropna(subset=[date_column, value_column])
        df_ts = df_ts.sort_values(date_column)

        if df_ts.empty:
            return {"error": "没有有效的时间序列数据"}

        # 计算移动平均
        df_ts["MA_3"] = df_ts[value_column].rolling(window=3).mean()
        df_ts["MA_7"] = df_ts[value_column].rolling(window=7).mean()

        # 计算变化率
        df_ts["pct_change"] = df_ts[value_column].pct_change()

        return {
            "dates": df_ts[date_column].dt.strftime("%Y-%m-%d").tolist(),
            "values": df_ts[value_column].tolist(),
            "ma_3": df_ts["MA_3"].where(df_ts["MA_3"].notna(), None).tolist(),
            "ma_7": df_ts["MA_7"].where(df_ts["MA_7"].notna(), None).tolist(),
            "pct_change": df_ts["pct_change"].where(df_ts["pct_change"].notna(), None).tolist(),
            "trend": "上升" if df_ts[value_column].iloc[-1] > df_ts[value_column].iloc[0] else "下降",
            "volatility": round(float(df_ts[value_column].std()), 4),
        }
