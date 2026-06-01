"""
可视化服务
根据数据和分析需求生成ECharts配置对象
支持12种图表类型
"""
import logging
import uuid
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class VisualizationService:
    """可视化服务类：生成ECharts图表配置"""

    # 暗色主题默认颜色方案（霓虹风格）
    COLORS = [
        "#6366f1", "#8b5cf6", "#ec4899", "#38bdf8",
        "#10b981", "#f59e0b", "#ef4444", "#06b6d4",
        "#f97316", "#84cc16", "#14b8a6", "#a855f7",
    ]

    @classmethod
    def generate_chart(
        cls,
        df: pd.DataFrame,
        chart_type: str,
        x_column: Optional[str] = None,
        y_column: Optional[Union[str, List[str]]] = None,
        group_column: Optional[str] = None,
        title: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        根据参数生成ECharts图表配置

        Args:
            df: 数据DataFrame
            chart_type: 图表类型
            x_column: X轴列名
            y_column: Y轴列名
            group_column: 分组列名
            title: 图表标题
            params: 额外参数

        Returns:
            ECharts配置对象
        """
        params = params or {}

        chart_generators = {
            "line": cls._generate_line_chart,
            "bar": cls._generate_bar_chart,
            "pie": cls._generate_pie_chart,
            "scatter": cls._generate_scatter_chart,
            "box": cls._generate_box_chart,
            "heatmap": cls._generate_heatmap_chart,
            "radar": cls._generate_radar_chart,
            "histogram": cls._generate_histogram_chart,
            "area": cls._generate_area_chart,
            "funnel": cls._generate_funnel_chart,
        }

        generator = chart_generators.get(chart_type)
        if generator is None:
            raise ValueError(f"不支持的图表类型: {chart_type}")

        chart_id = str(uuid.uuid4())
        option = generator(df, x_column, y_column, group_column, title, params)

        # 添加公共配置
        option = cls._apply_common_theme(option, chart_type)

        return {
            "chart_id": chart_id,
            "chart_type": chart_type,
            "echarts_option": option,
        }

    @classmethod
    def _apply_common_theme(cls, option: Dict[str, Any], chart_type: str) -> Dict[str, Any]:
        """应用通用主题配置"""
        # 暗色背景
        option.setdefault("backgroundColor", "transparent")

        # 通用tooltip
        if "tooltip" not in option:
            option["tooltip"] = {
                "trigger": "axis" if chart_type != "pie" else "item",
                "backgroundColor": "rgba(20, 20, 40, 0.9)",
                "borderColor": "rgba(99, 102, 241, 0.5)",
                "textStyle": {"color": "#cbd5e1"},
            }

        # 通用legend
        if "legend" not in option:
            option["legend"] = {
                "textStyle": {"color": "#cbd5e1"},
                "top": 5,
            }

        # 颜色方案
        option.setdefault("color", cls.COLORS)

        # 动画
        option.setdefault("animation", True)
        option.setdefault("animationDuration", 800)

        return option

    @classmethod
    def _generate_line_chart(
        cls, df, x_column, y_column, group_column, title, params
    ) -> Dict[str, Any]:
        """生成折线图配置"""
        x_data = df[x_column].tolist() if x_column else list(range(len(df)))

        series = []
        if isinstance(y_column, list):
            for col in y_column:
                if col in df.columns:
                    series.append({
                        "name": col,
                        "type": "line",
                        "data": df[col].where(df[col].notna(), None).tolist(),
                        "smooth": params.get("smooth", True),
                        "symbolSize": 6,
                        "lineStyle": {"width": 2},
                        "areaStyle": {
                            "opacity": 0.1,
                        } if params.get("show_area", False) else None,
                    })
        elif y_column and y_column in df.columns:
            series.append({
                "name": y_column,
                "type": "line",
                "data": df[y_column].where(df[y_column].notna(), None).tolist(),
                "smooth": params.get("smooth", True),
                "symbolSize": 6,
            })

        return {
            "title": {"text": title or "折线图", "textStyle": {"color": "#fff"}},
            "xAxis": {
                "type": "category",
                "data": x_data,
                "axisLine": {"lineStyle": {"color": "rgba(255,255,255,0.2)"}},
                "axisLabel": {"color": "#94a3b8", "rotate": params.get("x_rotate", 0)},
            },
            "yAxis": {
                "type": "value",
                "axisLine": {"lineStyle": {"color": "rgba(255,255,255,0.2)"}},
                "splitLine": {"lineStyle": {"color": "rgba(255,255,255,0.05)"}},
                "axisLabel": {"color": "#94a3b8"},
            },
            "series": series,
            "dataZoom": [{"type": "slider", "start": 0, "end": 100}],
            "toolbox": {"feature": {"saveAsImage": {"title": "保存为PNG"}}},
        }

    @classmethod
    def _generate_bar_chart(
        cls, df, x_column, y_column, group_column, title, params
    ) -> Dict[str, Any]:
        """生成柱状图配置"""
        x_data = df[x_column].tolist() if x_column else list(range(len(df)))

        series = []
        if isinstance(y_column, list):
            for col in y_column:
                if col in df.columns:
                    series.append({
                        "name": col,
                        "type": "bar",
                        "data": df[col].where(df[col].notna(), None).tolist(),
                        "barMaxWidth": 40,
                        "itemStyle": {
                            "borderRadius": [4, 4, 0, 0],
                        },
                    })
        elif y_column and y_column in df.columns:
            series.append({
                "name": y_column,
                "type": "bar",
                "data": df[y_column].where(df[y_column].notna(), None).tolist(),
                "barMaxWidth": 40,
                "itemStyle": {"borderRadius": [4, 4, 0, 0]},
            })

        return {
            "title": {"text": title or "柱状图", "textStyle": {"color": "#fff"}},
            "xAxis": {
                "type": "category",
                "data": x_data,
                "axisLabel": {"color": "#94a3b8", "rotate": params.get("x_rotate", 0)},
            },
            "yAxis": {
                "type": "value",
                "axisLabel": {"color": "#94a3b8"},
                "splitLine": {"lineStyle": {"color": "rgba(255,255,255,0.05)"}},
            },
            "series": series,
            "dataZoom": [{"type": "slider", "start": 0, "end": 100}],
            "toolbox": {"feature": {"saveAsImage": {"title": "保存为PNG"}}},
        }

    @classmethod
    def _generate_pie_chart(
        cls, df, x_column, y_column, group_column, title, params
    ) -> Dict[str, Any]:
        """生成饼图配置"""
        # 智能检测名称列和数值列
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if not num_cols:
            raise ValueError("饼图需要至少一个数值列")

        name_col = x_column or df.columns[0]
        if isinstance(y_column, str):
            value_col = y_column
        elif isinstance(y_column, list) and len(y_column) > 0:
            value_col = y_column[0]
        else:
            # 自动选择第一个数值列
            value_col = num_cols[0] if num_cols else df.columns[1]

        # 确保数值列是数值类型
        if value_col not in num_cols:
            value_col = num_cols[0]

        if name_col not in df.columns or value_col not in df.columns:
            raise ValueError("饼图需要有效的名称列和数值列")

        # 取前15个值，其余合并为"其他"
        top_n = params.get("top_n", 15)
        df_sorted = df.nlargest(top_n, value_col)
        data = []
        for _, row in df_sorted.iterrows():
            data.append({
                "name": str(row[name_col]),
                "value": float(row[value_col]) if pd.notna(row[value_col]) else 0,
            })

        return {
            "title": {"text": title or "饼图", "textStyle": {"color": "#fff"}},
            "tooltip": {"trigger": "item", "formatter": "{a} <br/>{b}: {c} ({d}%)"},
            "series": [{
                "name": title or value_col,
                "type": "pie",
                "radius": params.get("radius", ["40%", "70%"]),
                "center": ["50%", "55%"],
                "roseType": params.get("rose_type", None),
                "itemStyle": {
                    "borderRadius": 10,
                    "borderColor": "rgba(0, 0, 0, 0.3)",
                    "borderWidth": 2,
                },
                "label": {
                    "show": True,
                    "color": "#cbd5e1",
                    "formatter": "{b}\n{d}%",
                },
                "emphasis": {
                    "label": {"show": True, "fontSize": 16},
                    "itemStyle": {"shadowBlur": 10, "shadowColor": "rgba(0, 0, 0, 0.5)"},
                },
                "data": data,
            }],
            "toolbox": {"feature": {"saveAsImage": {"title": "保存为PNG"}}},
        }

    @classmethod
    def _generate_scatter_chart(
        cls, df, x_column, y_column, group_column, title, params
    ) -> Dict[str, Any]:
        """生成散点图配置"""
        x_col = x_column or df.select_dtypes(include=[np.number]).columns[0] if len(df.select_dtypes(include=[np.number]).columns) > 0 else None
        y_col = y_column if isinstance(y_column, str) else (y_column[0] if isinstance(y_column, list) else None)

        if x_col is None or y_col is None:
            # 尝试使用前两个数值列
            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if len(num_cols) >= 2:
                x_col = x_col or num_cols[0]
                y_col = y_col or num_cols[1]

        if x_col not in df.columns or y_col not in df.columns:
            raise ValueError("散点图需要有效的X轴和Y轴列")

        x_data = df[x_col].where(df[x_col].notna(), None).tolist()
        y_data = df[y_col].where(df[y_col].notna(), None).tolist()

        return {
            "title": {"text": title or f"{x_col} vs {y_col}", "textStyle": {"color": "#fff"}},
            "xAxis": {
                "name": x_col,
                "type": "value",
                "splitLine": {"lineStyle": {"color": "rgba(255,255,255,0.05)"}},
                "axisLabel": {"color": "#94a3b8"},
            },
            "yAxis": {
                "name": y_col,
                "type": "value",
                "splitLine": {"lineStyle": {"color": "rgba(255,255,255,0.05)"}},
                "axisLabel": {"color": "#94a3b8"},
            },
            "series": [{
                "name": f"{x_col} vs {y_col}",
                "type": "scatter",
                "data": [[x_data[i], y_data[i]] for i in range(len(x_data))],
                "symbolSize": 8,
                "itemStyle": {"opacity": 0.7},
            }],
            "dataZoom": [{"type": "slider"}, {"type": "inside"}],
            "toolbox": {"feature": {"saveAsImage": {"title": "保存为PNG"}}},
        }

    @classmethod
    def _generate_box_chart(
        cls, df, x_column, y_column, group_column, title, params
    ) -> Dict[str, Any]:
        """生成箱线图配置"""
        # 选择数值列
        if isinstance(y_column, list):
            num_cols = [c for c in y_column if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
        elif y_column and y_column in df.columns and pd.api.types.is_numeric_dtype(df[y_column]):
            num_cols = [y_column]
        else:
            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()[:8]

        if not num_cols:
            raise ValueError("箱线图需要数值列")

        series = []
        for col in num_cols:
            col_data = df[col].dropna()
            if len(col_data) < 4:
                continue
            q1, q3 = col_data.quantile(0.25), col_data.quantile(0.75)
            iqr_val = q3 - q1
            series.append({
                "name": col,
                "type": "boxplot",
                "data": [[
                    float(col_data.min()),
                    float(q1),
                    float(col_data.median()),
                    float(q3),
                    float(col_data.max()),
                ]],
            })

        return {
            "title": {"text": title or "箱线图", "textStyle": {"color": "#fff"}},
            "xAxis": {
                "type": "category",
                "data": num_cols,
                "axisLabel": {"color": "#94a3b8", "rotate": params.get("x_rotate", 30)},
            },
            "yAxis": {
                "type": "value",
                "splitLine": {"lineStyle": {"color": "rgba(255,255,255,0.05)"}},
                "axisLabel": {"color": "#94a3b8"},
            },
            "series": series,
            "toolbox": {"feature": {"saveAsImage": {"title": "保存为PNG"}}},
        }

    @classmethod
    def _generate_heatmap_chart(
        cls, df, x_column, y_column, group_column, title, params
    ) -> Dict[str, Any]:
        """生成热力图配置"""
        numeric_df = df.select_dtypes(include=[np.number])
        if len(numeric_df.columns) < 2:
            raise ValueError("热力图需要至少2个数值列")

        corr = numeric_df.corr()
        col_names = corr.columns.tolist()

        heatmap_data = []
        for i, row_name in enumerate(col_names):
            for j, col_name in enumerate(col_names):
                heatmap_data.append([j, i, round(float(corr.iloc[i, j]), 4)])

        return {
            "title": {"text": title or "相关性热力图", "textStyle": {"color": "#fff"}},
            "xAxis": {
                "type": "category",
                "data": col_names,
                "axisLabel": {"color": "#94a3b8", "rotate": 45},
                "position": "bottom",
            },
            "yAxis": {
                "type": "category",
                "data": col_names,
                "axisLabel": {"color": "#94a3b8"},
            },
            "visualMap": {
                "min": -1,
                "max": 1,
                "calculable": True,
                "orient": "horizontal",
                "left": "center",
                "bottom": 0,
                "inRange": {"color": ["#38bdf8", "#0f0c29", "#ec4899"]},
                "textStyle": {"color": "#cbd5e1"},
            },
            "series": [{
                "type": "heatmap",
                "data": heatmap_data,
                "label": {"show": True, "color": "#cbd5e1", "fontSize": 10},
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowColor": "rgba(0, 0, 0, 0.5)",
                    },
                },
            }],
            "toolbox": {"feature": {"saveAsImage": {"title": "保存为PNG"}}},
        }

    @classmethod
    def _generate_radar_chart(
        cls, df, x_column, y_column, group_column, title, params
    ) -> Dict[str, Any]:
        """生成雷达图配置"""
        numeric_df = df.select_dtypes(include=[np.number])
        if len(numeric_df.columns) < 3:
            raise ValueError("雷达图需要至少3个数值列")

        max_indicators = params.get("max_indicators", 8)
        cols = numeric_df.columns.tolist()[:max_indicators]

        # 计算每个指标的范围
        indicators = []
        for col in cols:
            col_data = numeric_df[col].dropna()
            if len(col_data) > 0:
                indicators.append({
                    "name": col,
                    "max": float(col_data.max()) * 1.2,
                })

        # 取前几行作为不同的系列
        max_series = params.get("max_series", 5)
        sample_df = numeric_df[cols].head(max_series)

        series_data = []
        for i, (_, row) in enumerate(sample_df.iterrows()):
            series_data.append({
                "name": f"样本{i + 1}",
                "value": [float(v) if pd.notna(v) else 0 for v in row.values],
            })

        return {
            "title": {"text": title or "雷达图", "textStyle": {"color": "#fff"}},
            "legend": {"data": [s["name"] for s in series_data], "textStyle": {"color": "#cbd5e1"}},
            "radar": {
                "indicator": indicators,
                "center": ["50%", "55%"],
                "radius": "60%",
                "axisName": {"color": "#cbd5e1"},
                "splitArea": {
                    "areaStyle": {"color": ["rgba(99,102,241,0.05)", "rgba(99,102,241,0.1)"]},
                },
            },
            "series": [{"type": "radar", "data": series_data}],
            "toolbox": {"feature": {"saveAsImage": {"title": "保存为PNG"}}},
        }

    @classmethod
    def _generate_histogram_chart(
        cls, df, x_column, y_column, group_column, title, params
    ) -> Dict[str, Any]:
        """生成直方图配置"""
        col = y_column if isinstance(y_column, str) and y_column in df.columns else (
            x_column if x_column and x_column in df.columns and pd.api.types.is_numeric_dtype(df[x_column])
            else df.select_dtypes(include=[np.number]).columns[0] if len(df.select_dtypes(include=[np.number]).columns) > 0 else None
        )

        if col is None:
            raise ValueError("直方图需要数值列")

        col_data = df[col].dropna()
        bins = params.get("bins", min(20, int(len(col_data) ** 0.5)))
        hist, bin_edges = np.histogram(col_data, bins=bins)

        return {
            "title": {"text": title or f"{col} 分布直方图", "textStyle": {"color": "#fff"}},
            "xAxis": {
                "name": col,
                "type": "category",
                "data": [f"{bin_edges[i]:.2f}-{bin_edges[i+1]:.2f}" for i in range(len(bin_edges) - 1)],
                "axisLabel": {"color": "#94a3b8", "rotate": 45},
            },
            "yAxis": {
                "name": "频数",
                "type": "value",
                "axisLabel": {"color": "#94a3b8"},
                "splitLine": {"lineStyle": {"color": "rgba(255,255,255,0.05)"}},
            },
            "series": [{
                "name": col,
                "type": "bar",
                "data": hist.tolist(),
                "barWidth": "90%",
                "itemStyle": {
                    "borderRadius": [4, 4, 0, 0],
                },
            }],
            "toolbox": {"feature": {"saveAsImage": {"title": "保存为PNG"}}},
        }

    @classmethod
    def _generate_area_chart(
        cls, df, x_column, y_column, group_column, title, params
    ) -> Dict[str, Any]:
        """生成面积图配置"""
        option = cls._generate_line_chart(df, x_column, y_column, group_column, title, params)
        for s in option["series"]:
            s["areaStyle"] = {"opacity": 0.4}
        option["title"]["text"] = title or "面积图"
        return option

    @classmethod
    def _generate_funnel_chart(
        cls, df, x_column, y_column, group_column, title, params
    ) -> Dict[str, Any]:
        """生成漏斗图配置"""
        name_col = x_column or df.columns[0]
        value_col = y_column if isinstance(y_column, str) else (
            y_column[0] if isinstance(y_column, list) else (
                df.select_dtypes(include=[np.number]).columns[0] if len(df.select_dtypes(include=[np.number]).columns) > 0 else None
            )
        )

        if name_col not in df.columns or value_col not in df.columns:
            raise ValueError("漏斗图需要有效的名称列和数值列")

        df_sorted = df.nlargest(params.get("top_n", 10), value_col)
        data = []
        for _, row in df_sorted.iterrows():
            data.append({
                "name": str(row[name_col]),
                "value": float(row[value_col]) if pd.notna(row[value_col]) else 0,
            })

        return {
            "title": {"text": title or "漏斗图", "textStyle": {"color": "#fff"}},
            "tooltip": {"trigger": "item", "formatter": "{a}<br/>{b}: {c}"},
            "series": [{
                "name": title or value_col,
                "type": "funnel",
                "left": "10%",
                "top": 50,
                "width": "80%",
                "sort": "descending",
                "gap": 2,
                "label": {"show": True, "position": "inside", "color": "#fff"},
                "labelLine": {"length": 10, "lineStyle": {"width": 1, "type": "solid"}},
                "itemStyle": {"borderColor": "rgba(0,0,0,0.3)", "borderWidth": 1},
                "data": data,
            }],
            "toolbox": {"feature": {"saveAsImage": {"title": "保存为PNG"}}},
        }

    @classmethod
    def recommend_charts(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        根据数据特征智能推荐图表类型

        Args:
            df: DataFrame对象

        Returns:
            推荐列表
        """
        recommendations = []
        num_cols = df.select_dtypes(include=[np.number]).columns
        cat_cols = df.select_dtypes(include=["object", "category"]).columns
        date_cols = [c for c in df.columns if "date" in c.lower() or "time" in c.lower() or "日期" in c or "时间" in c]

        # 检查是否有日期列 + 数值列 → 推荐折线图
        if date_cols and len(num_cols) >= 1:
            recommendations.append({
                "chart_type": "line",
                "reason": f"检测到日期列'{date_cols[0]}'和数值列，推荐使用折线图分析时间趋势",
                "priority": 90,
            })

        # 检查分类列 + 数值列 → 推荐柱状图
        if len(cat_cols) >= 1 and len(num_cols) >= 1:
            recommendations.append({
                "chart_type": "bar",
                "reason": f"检测到分类数据，推荐使用柱状图对比各类别的数值差异",
                "priority": 85,
            })

        # 检查多个数值列 → 推荐相关性热力图
        if len(num_cols) >= 3:
            recommendations.append({
                "chart_type": "heatmap",
                "reason": f"检测到{len(num_cols)}个数值列，推荐使用热力图分析相关性",
                "priority": 80,
            })

        # 分类列占比分析 → 饼图
        if len(cat_cols) >= 1 and len(num_cols) >= 1:
            recommendations.append({
                "chart_type": "pie",
                "reason": "适合展示分类数据的占比分布",
                "priority": 75,
            })

        # 两个数值列 → 散点图
        if len(num_cols) >= 2:
            recommendations.append({
                "chart_type": "scatter",
                "reason": f"推荐使用散点图分析'{num_cols[0]}'和'{num_cols[1]}'之间的关系",
                "priority": 70,
            })

        # 多个数值列 → 箱线图
        if len(num_cols) >= 2:
            recommendations.append({
                "chart_type": "box",
                "reason": "推荐使用箱线图查看数据分布和异常值",
                "priority": 65,
            })

        # 多维数据 → 雷达图
        if len(num_cols) >= 3:
            recommendations.append({
                "chart_type": "radar",
                "reason": f"检测到{len(num_cols)}个数值维度，推荐使用雷达图展示多维数据",
                "priority": 60,
            })

        return sorted(recommendations, key=lambda r: r["priority"], reverse=True)
