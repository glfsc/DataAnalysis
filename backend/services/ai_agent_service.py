"""
AI智能分析助手服务
提供自然语言交互、自动洞察发现、智能图表推荐和数据故事生成
"""
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

from services.analysis_service import AnalysisService
from services.visualization_service import VisualizationService

logger = logging.getLogger(__name__)


class AIAgentService:
    """AI智能助手服务类：规则匹配 + 模板驱动的智能分析"""

    # 常见问题模式库
    QUERY_PATTERNS = [
        # 最大值相关
        {
            "pattern": r"(最大|最高|最多|max|top\s*\d+|最大值)",
            "keywords": ["最大", "最高", "最多", "max", "top"],
            "action": "find_extreme",
            "extreme_type": "max",
        },
        # 最小值相关
        {
            "pattern": r"(最小|最低|最少|min|最小值)",
            "keywords": ["最小", "最低", "最少", "min"],
            "action": "find_extreme",
            "extreme_type": "min",
        },
        # 平均值相关
        {
            "pattern": r"(平均|均值|average|mean)",
            "keywords": ["平均", "均值", "average", "mean"],
            "action": "calculate_stat",
            "stat_type": "mean",
        },
        # 总和相关
        {
            "pattern": r"(总和|合计|total|sum|总数|总计)",
            "keywords": ["总和", "合计", "total", "sum", "总数", "总计"],
            "action": "calculate_stat",
            "stat_type": "sum",
        },
        # 排序相关
        {
            "pattern": r"(排序|升序|降序|sort|排名|排行)",
            "keywords": ["排序", "排序", "sort", "排名", "排行"],
            "action": "sort_data",
        },
        # 趋势相关
        {
            "pattern": r"(趋势|trend|走势|变化|增长|下降|波动)",
            "keywords": ["趋势", "trend", "走势", "变化", "增长", "下降", "波动"],
            "action": "analyze_trend",
        },
        # 分布相关
        {
            "pattern": r"(分布|distribution|频率|frequency|histogram|直方图)",
            "keywords": ["分布", "distribution", "频率", "frequency", "直方图"],
            "action": "analyze_distribution",
        },
        # 相关性相关
        {
            "pattern": r"(相关|correlation|关系|关联|影响)",
            "keywords": ["相关", "correlation", "关系", "关联", "影响"],
            "action": "analyze_correlation",
        },
        # 推荐图表
        {
            "pattern": r"(推荐|建议|用什么图|什么图表|如何可视化)",
            "keywords": ["推荐", "建议", "什么图", "可视化"],
            "action": "recommend_chart",
        },
        # 数据概览
        {
            "pattern": r"(概览|概况|overview|总结|summary|基本.*信息)",
            "keywords": ["概览", "概况", "overview", "总结", "summary", "基本"],
            "action": "data_overview",
        },
    ]

    # 数据洞察模板
    INSIGHT_TEMPLATES = {
        "high_variance": "列'{column}'的标准差为{std:.2f}，数据波动较大，建议关注极端值的影响",
        "skewed": "列'{column}'的偏度为{skew:.2f}，数据呈{skew_direction}分布",
        "missing_data": "列'{column}'存在{missing_count}个缺失值（{missing_pct:.1f}%），建议进行数据清洗",
        "strong_correlation": "'{col1}'和'{col2}'的相关系数为{corr:.2f}，存在{corr_direction}关系",
        "outlier_detected": "列'{column}'中检测到{outlier_count}个异常值（超出{bound_type}范围）",
        "dominant_category": "分类列'{column}'中，'{top_value}'占比最高，达{top_pct:.1f}%",
    }

    @classmethod
    def process_query(cls, query: str, df: pd.DataFrame, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        处理用户自然语言查询

        Args:
            query: 用户查询文本
            df: 当前数据DataFrame
            context: 上下文信息

        Returns:
            包含回答、建议操作和洞察的字典
        """
        query_lower = query.lower().strip()

        # 1. 匹配查询模式
        matched_action = None
        matched_pattern = None
        for pattern_def in cls.QUERY_PATTERNS:
            if re.search(pattern_def["pattern"], query_lower):
                matched_action = pattern_def
                matched_pattern = pattern_def["pattern"]
                break

        # 2. 提取查询中提到的列名
        mentioned_columns = []
        for col in df.columns:
            if col.lower() in query_lower or col in query:
                mentioned_columns.append(col)

        # 3. 提取数字（如top N，第N个）
        numbers_in_query = re.findall(r"\d+", query)
        top_n = int(numbers_in_query[0]) if numbers_in_query else 5

        # 4. 根据匹配模式生成回答
        if matched_action is None:
            answer, suggestions = cls._generate_fallback_response(query, df)
            return {
                "answer": answer,
                "suggested_action": suggestions,
                "chart_recommendation": None,
                "insights": [],
            }

        action_type = matched_action["action"]
        answer = ""
        suggested_action = None
        chart_recommendation = None
        insights = []

        try:
            if action_type == "find_extreme":
                extreme_type = matched_action["extreme_type"]
                answer, insights = cls._find_extreme(df, mentioned_columns, extreme_type, top_n)

            elif action_type == "calculate_stat":
                stat_type = matched_action["stat_type"]
                answer = cls._calculate_stat(df, mentioned_columns, stat_type)

            elif action_type == "sort_data":
                answer = cls._sort_data_info(df, mentioned_columns, query_lower)

            elif action_type == "analyze_trend":
                answer, chart_recommendation = cls._analyze_trend(df, mentioned_columns)

            elif action_type == "analyze_distribution":
                answer, chart_recommendation = cls._analyze_distribution(df, mentioned_columns)

            elif action_type == "analyze_correlation":
                answer, chart_recommendation = cls._analyze_correlation_query(df, mentioned_columns)

            elif action_type == "recommend_chart":
                answer, chart_recommendation = cls._recommend_chart_for_query(df)
                suggested_action = "visualization"

            elif action_type == "data_overview":
                answer, insights = cls._generate_data_overview(df)

        except Exception as e:
            logger.error(f"AI查询处理出错: {str(e)}")
            answer = f"分析过程中遇到问题: {str(e)}。请尝试更具体的查询。"
            suggested_action = None

        return {
            "answer": answer,
            "suggested_action": suggested_action,
            "chart_recommendation": chart_recommendation,
            "insights": insights,
        }

    @classmethod
    def auto_discover_insights(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        自动发现数据中的洞察

        Args:
            df: DataFrame对象

        Returns:
            洞察列表
        """
        insights = []

        # 1. 检查缺失值
        missing = df.isnull().sum()
        for col in df.columns:
            if missing[col] > 0:
                insights.append({
                    "type": "data_quality",
                    "severity": "warning" if missing[col] / len(df) > 0.1 else "info",
                    "title": f"列 '{col}' 存在缺失值",
                    "description": cls.INSIGHT_TEMPLATES["missing_data"].format(
                        column=col,
                        missing_count=int(missing[col]),
                        missing_pct=missing[col] / max(len(df), 1) * 100,
                    ),
                    "action": "建议使用数据清洗功能处理缺失值",
                })

        # 2. 检查数值列的分布特征
        num_cols = df.select_dtypes(include=[np.number]).columns
        for col in num_cols:
            col_data = df[col].dropna()
            if len(col_data) < 3:
                continue

            std = col_data.std()
            mean = col_data.mean()
            cv = std / abs(mean) if mean != 0 else 0

            if cv > 1.5:
                insights.append({
                    "type": "distribution",
                    "severity": "info",
                    "title": f"列 '{col}' 波动较大",
                    "description": cls.INSIGHT_TEMPLATES["high_variance"].format(
                        column=col, std=std
                    ),
                    "action": "考虑使用箱线图查看分布，或对数据进行标准化",
                })

            skew = col_data.skew()
            if abs(skew) > 1:
                insights.append({
                    "type": "distribution",
                    "severity": "info",
                    "title": f"列 '{col}' 分布偏斜",
                    "description": cls.INSIGHT_TEMPLATES["skewed"].format(
                        column=col, skew=skew,
                        skew_direction='右偏' if skew > 0 else '左偏'
                    ),
                    "action": "数据呈偏斜分布，可能影响统计分析的准确性",
                })

            # 异常值检测（IQR方法）
            Q1, Q3 = col_data.quantile(0.25), col_data.quantile(0.75)
            IQR = Q3 - Q1
            outlier_count = int(((col_data < Q1 - 1.5 * IQR) | (col_data > Q3 + 1.5 * IQR)).sum())
            if outlier_count > 0:
                insights.append({
                    "type": "outlier",
                    "severity": "warning" if outlier_count / len(col_data) > 0.1 else "info",
                    "title": f"列 '{col}' 存在异常值",
                    "description": cls.INSIGHT_TEMPLATES["outlier_detected"].format(
                        column=col, outlier_count=outlier_count, bound_type="IQR"
                    ),
                    "action": "建议使用异常值检测功能或箱线图查看详情",
                })

        # 3. 检查分类列的集中度
        cat_cols = df.select_dtypes(include=["object", "category"]).columns
        for col in cat_cols:
            value_counts = df[col].value_counts()
            if len(value_counts) > 0:
                top_value = value_counts.index[0]
                top_pct = value_counts.iloc[0] / len(df) * 100
                if top_pct > 80:
                    insights.append({
                        "type": "imbalance",
                        "severity": "info",
                        "title": f"列 '{col}' 类别高度集中",
                        "description": cls.INSIGHT_TEMPLATES["dominant_category"].format(
                            column=col, top_value=top_value, top_pct=top_pct
                        ),
                        "action": "数据集中度过高，可能影响分析的代表性",
                    })

        # 4. 强相关性检测
        if len(num_cols) >= 2:
            corr_matrix = df[num_cols].corr()
            for i in range(len(num_cols)):
                for j in range(i + 1, len(num_cols)):
                    corr_val = corr_matrix.iloc[i, j]
                    if abs(corr_val) >= 0.7:
                        insights.append({
                            "type": "correlation",
                            "severity": "info",
                            "title": f"强相关性发现",
                            "description": cls.INSIGHT_TEMPLATES["strong_correlation"].format(
                                col1=num_cols[i], col2=num_cols[j], corr=corr_val,
                                corr_direction='强正相关' if corr_val > 0 else '强负相关'
                            ),
                            "action": "可以进一步分析因果关系，或考虑在建模时处理多重共线性",
                        })

        # 按严重程度排序
        severity_order = {"warning": 0, "info": 1}
        insights.sort(key=lambda x: severity_order.get(x["severity"], 2))

        return insights[:15]  # 最多返回15条洞察

    @classmethod
    def generate_data_story(
        cls,
        df: pd.DataFrame,
        file_id: str,
        sections: Optional[List[str]] = None,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        生成数据分析故事/报告

        Args:
            df: DataFrame对象
            file_id: 文件ID
            sections: 报告章节
            title: 报告标题

        Returns:
            报告结构化数据
        """
        sections = sections or ["overview", "analysis", "insights"]
        report = {
            "title": title or "数据分析报告",
            "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sections": [],
        }

        for section in sections:
            if section == "overview":
                report["sections"].append(cls._story_overview(df))
            elif section == "analysis":
                report["sections"].append(cls._story_analysis(df))
            elif section == "insights":
                report["sections"].append(cls._story_insights(df))
            elif section == "recommendations":
                report["sections"].append(cls._story_recommendations(df))

        return report

    # ============ 私有辅助方法 ============

    @classmethod
    def _find_extreme(
        cls, df: pd.DataFrame, columns: List[str], extreme_type: str, top_n: int
    ) -> Tuple[str, List[str]]:
        """查找极值"""
        num_cols = df.select_dtypes(include=[np.number]).columns
        target_cols = [c for c in columns if c in num_cols] if columns else num_cols.tolist()

        if not target_cols:
            return "未找到可分析的数值列，请指定具体的数值列名。", []

        answers = []
        for col in target_cols[:3]:
            if extreme_type == "max":
                top_rows = df.nlargest(top_n, col)
                val = top_rows[col].iloc[0]
                answers.append(f"**{col}** 的最大值是 **{val:.2f}**")
            else:
                top_rows = df.nsmallest(top_n, col)
                val = top_rows[col].iloc[0]
                answers.append(f"**{col}** 的最小值是 **{val:.2f}**")

        return "\n\n".join(answers), []

    @classmethod
    def _calculate_stat(
        cls, df: pd.DataFrame, columns: List[str], stat_type: str
    ) -> str:
        """计算统计量"""
        num_cols = df.select_dtypes(include=[np.number]).columns
        target_cols = [c for c in columns if c in num_cols] if columns else num_cols.tolist()

        if not target_cols:
            return "未找到可分析的数值列，请指定包含数值的列名。"

        answers = []
        stat_labels = {"mean": "平均值", "sum": "总和", "median": "中位数"}

        for col in target_cols[:5]:
            col_data = df[col].dropna()
            if stat_type == "mean":
                val = col_data.mean()
            elif stat_type == "sum":
                val = col_data.sum()
            else:
                val = col_data.median()

            answers.append(f"**{col}** 的{stat_labels.get(stat_type, stat_type)}是 **{val:,.2f}**")

        return "\n\n".join(answers)

    @classmethod
    def _sort_data_info(cls, df: pd.DataFrame, columns: List[str], query: str) -> str:
        """排序信息"""
        num_cols = df.select_dtypes(include=[np.number]).columns
        target_col = columns[0] if columns and columns[0] in num_cols else (num_cols[0] if len(num_cols) > 0 else None)

        if target_col is None:
            return "未找到可排序的数值列。"

        ascending = "升" if "升" in query else "降"
        sorted_df = df.sort_values(target_col, ascending=ascending == "升")
        top5 = sorted_df.head(5)
        cols_to_show = [target_col] + [c for c in df.columns[:3] if c != target_col]

        lines = [f"按 **{target_col}** {ascending}序排列，前5条数据：\n"]
        for i, (_, row) in enumerate(top5.iterrows()):
            values = [f"{c}: {row[c]}" for c in cols_to_show if c in row.index]
            lines.append(f"{i+1}. " + ", ".join(values))

        return "\n".join(lines)

    @classmethod
    def _analyze_trend(
        cls, df: pd.DataFrame, columns: List[str]
    ) -> Tuple[str, Optional[Dict]]:
        """分析趋势"""
        num_cols = df.select_dtypes(include=[np.number]).columns
        target_col = columns[0] if columns and columns[0] in num_cols else (num_cols[0] if len(num_cols) > 0 else None)

        if target_col is None:
            return "未找到可分析趋势的数值列。", None

        col_data = df[target_col].dropna()
        x = np.arange(len(col_data))
        from sklearn.linear_model import LinearRegression
        model = LinearRegression()
        model.fit(x.reshape(-1, 1), col_data.values)

        trend = "上升" if model.coef_[0] > 0 else "下降"
        answer = f"**{target_col}** 整体呈 **{trend}** 趋势，每个数据点{'增加' if trend == '上升' else '减少'}约 {abs(model.coef_[0]):.4f} 单位"

        chart_recommendation = {
            "chart_type": "line",
            "x_column": df.columns[0] if df.columns[0] != target_col else None,
            "y_column": target_col,
            "title": f"{target_col} 趋势分析",
            "reason": "折线图适合展示数据随时间/顺序的变化趋势",
        }

        return answer, chart_recommendation

    @classmethod
    def _analyze_distribution(
        cls, df: pd.DataFrame, columns: List[str]
    ) -> Tuple[str, Optional[Dict]]:
        """分析分布"""
        num_cols = df.select_dtypes(include=[np.number]).columns
        target_col = columns[0] if columns and columns[0] in num_cols else (num_cols[0] if len(num_cols) > 0 else None)

        if target_col is None:
            return "未找到可分析分布的数值列。", None

        col_data = df[target_col].dropna()
        stats = {
            "mean": col_data.mean(),
            "std": col_data.std(),
            "min": col_data.min(),
            "max": col_data.max(),
            "skew": col_data.skew(),
        }

        answer = (
            f"**{target_col}** 分布特征：\n"
            f"- 均值: {stats['mean']:.2f}\n"
            f"- 标准差: {stats['std']:.2f}\n"
            f"- 范围: [{stats['min']:.2f}, {stats['max']:.2f}]\n"
            f"- 偏度: {stats['skew']:.2f}（{'右偏' if stats['skew'] > 0 else '左偏'}）"
        )

        chart_recommendation = {
            "chart_type": "histogram",
            "y_column": target_col,
            "title": f"{target_col} 分布分析",
            "reason": "直方图适合展示数据的分布形态",
        }

        return answer, chart_recommendation

    @classmethod
    def _analyze_correlation_query(
        cls, df: pd.DataFrame, columns: List[str]
    ) -> Tuple[str, Optional[Dict]]:
        """分析相关性"""
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        target_cols = [c for c in columns if c in num_cols] if columns else num_cols[:5]

        if len(target_cols) < 2:
            return "相关性分析需要至少2个数值列。", None

        corr_result = AnalysisService.correlation_analysis(df, target_cols)
        strong = corr_result.get("strong_correlations", [])

        if strong:
            answer = "发现以下强相关关系：\n"
            for s in strong[:5]:
                answer += f"- {s['pair'][0]} 和 {s['pair'][1]}: {s['correlation']}（{s['direction']}，{s['strength']}相关）\n"
        else:
            answer = "未发现强相关关系（|相关系数| >= 0.5），各数值列之间关联较弱。"

        chart_recommendation = {
            "chart_type": "heatmap",
            "title": "相关性热力图",
            "reason": "热力图可以直观展示各变量之间的相关性强弱",
        }

        return answer, chart_recommendation

    @classmethod
    def _recommend_chart_for_query(cls, df: pd.DataFrame) -> Tuple[str, Optional[Dict]]:
        """推荐图表"""
        recommendations = VisualizationService.recommend_charts(df)

        if not recommendations:
            return "无法根据当前数据推荐合适的图表类型。", None

        top_rec = recommendations[0]
        answer = f"根据数据特征，推荐使用 **{top_rec['chart_type']}** 图表：{top_rec['reason']}\n\n"
        answer += "其他推荐：\n"
        for rec in recommendations[1:4]:
            answer += f"- **{rec['chart_type']}**: {rec['reason']}\n"

        chart_recommendation = {
            "chart_type": top_rec["chart_type"],
            "title": top_rec["reason"],
        }

        return answer, chart_recommendation

    @classmethod
    def _generate_data_overview(cls, df: pd.DataFrame) -> Tuple[str, List[str]]:
        """生成数据概览"""
        info = AnalysisService.descriptive_statistics(df)
        overall = info.get("overall", {})

        answer = (
            f"## 📊 数据概览\n\n"
            f"- **数据量**: {overall.get('total_rows', 0):,} 行 × {overall.get('total_columns', 0)} 列\n"
            f"- **数值列**: {overall.get('numeric_columns', 0)} 个\n"
            f"- **分类列**: {overall.get('categorical_columns', 0)} 个\n"
            f"- **缺失值**: {overall.get('total_missing', 0)} 个\n"
            f"- **重复行**: {overall.get('total_duplicates', 0)} 行\n"
            f"- **内存占用**: {overall.get('memory_usage_mb', 0):.2f} MB\n"
            f"\n数据质量总体{'良好' if overall.get('total_missing', 0) == 0 and overall.get('total_duplicates', 0) == 0 else '需关注'}。"
        )

        # 生成洞察
        insights_list = cls.auto_discover_insights(df)
        insights = [i["description"] for i in insights_list[:5]]

        return answer, insights

    @classmethod
    def _generate_fallback_response(cls, query: str, df: pd.DataFrame) -> Tuple[str, Optional[str]]:
        """生成兜底回答"""
        suggestions = []
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        answer = f"收到您的问题：「{query}」\n\n我可以帮您：\n"
        answer += "- 📊 查看数据概览\n"
        answer += "- 📈 分析数据趋势和分布\n"
        answer += "- 🔍 查找最大/最小值\n"
        answer += "- 📐 计算平均值、总和等统计量\n"
        answer += "- 🔗 分析列之间的相关性\n"
        answer += "- 💡 推荐合适的可视化图表\n"

        if num_cols:
            answer += f"\n当前数据的数值列包括：{', '.join(num_cols[:8])}"

        return answer, None

    # ============ 数据故事生成 ============

    @classmethod
    def _story_overview(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """生成概览章节"""
        info = AnalysisService.descriptive_statistics(df)
        overall = info.get("overall", {})
        quality = "良好" if overall.get("total_missing", 0) == 0 else "有待改善"

        return {
            "title": "📋 数据概览",
            "content": f"数据集包含 {overall.get('total_rows', 0):,} 条记录和 {overall.get('total_columns', 0)} 个字段。"
                       f"数据完整性{quality}，共发现 {overall.get('total_missing', 0)} 个缺失值。",
            "key_metrics": {
                "total_rows": overall.get("total_rows", 0),
                "total_columns": overall.get("total_columns", 0),
                "numeric_columns": overall.get("numeric_columns", 0),
                "categorical_columns": overall.get("categorical_columns", 0),
                "missing_values": overall.get("total_missing", 0),
                "quality_assessment": quality,
            },
        }

    @classmethod
    def _story_analysis(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """生成分析章节"""
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        findings = []

        if len(num_cols) >= 2:
            corr = AnalysisService.correlation_analysis(df, num_cols[:8])
            strong = corr.get("strong_correlations", [])
            if strong:
                for s in strong[:3]:
                    findings.append(f"{s['pair'][0]} 与 {s['pair'][1]} 呈{s['direction']}（r={s['correlation']}）")

        return {
            "title": "🔍 分析发现",
            "content": "通过对数据的探索性分析，发现以下关键信息：",
            "findings": findings if findings else ["未发现显著的相关关系，建议进一步探索数据。"],
        }

    @classmethod
    def _story_insights(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """生成洞察章节"""
        insights = cls.auto_discover_insights(df)
        return {
            "title": "💡 关键洞察",
            "content": "系统自动识别出以下数据特征和潜在问题：",
            "insights": [{"title": i["title"], "description": i["description"]} for i in insights[:8]],
        }

    @classmethod
    def _story_recommendations(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """生成建议章节"""
        recs = VisualizationService.recommend_charts(df)
        return {
            "title": "🎯 行动建议",
            "content": "基于数据分析结果，提出以下建议：",
            "recommendations": [
                {"chart": r["chart_type"], "reason": r["reason"]}
                for r in recs[:5]
            ],
        }
