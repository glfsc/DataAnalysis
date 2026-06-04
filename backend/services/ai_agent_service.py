"""
AI智能分析助手服务 v2
纯 LLM 驱动，支持流式输出、上下文感知、专业数据分析
"""
import json
import logging
from typing import Any, Dict, List, Optional, AsyncGenerator

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class AIAgentService:
    """AI智能助手服务类：纯 LLM 驱动的智能分析"""

    @classmethod
    def _build_system_prompt(cls, model_name: str) -> str:
        """构建包含当前模型信息的系统提示词"""
        return f"""你是一个专业的商业数据分析助手，运行在 DataVision Pro 数据分析平台上。
你当前由 **{model_name}** 模型驱动。当用户询问"你用的是什么模型"或类似问题时，请直接回答你的底层模型是 {model_name}，不要编造其他身份。

## 你的能力
- 分析用户上传的表格数据（CSV/Excel）
- 提供数据概览、统计分析、趋势洞察
- 识别数据质量问题（缺失值、异常值、重复数据）
- 建议合适的可视化图表类型
- 解读相关性、分布特征等统计指标
- 回答问题并提供可操作的建议

## 平台功能（用户可以使用的工具）
1. **数据上传**：支持 CSV 和 Excel 文件
2. **数据清洗**：缺失值处理（删除/均值/中位数/众数填充）、重复行删除、异常值检测（IQR/Z-Score）
3. **数据分析**：描述性统计、相关性分析（皮尔逊）、分组聚合、聚类分析（K-Means/K-Medoids/OPTICS/AGNES/GMM）、线性回归、异常检测（Isolation Forest）
4. **可视化**：柱状图、折线图、饼图、面积图，支持交互式编辑
5. **数据导出**：支持 CSV 导出

## 回答要求
- 使用中文回答，专业但不生硬
- 基于提供的数据给出具体数值和分析
- 如果数据不足以回答问题，诚实说明并给出建议
- 使用 Markdown 格式组织回答（标题、列表、表格、加粗等）
- 回答结尾可以给出 1-2 个后续分析建议
- 保持简洁，重点突出，避免冗长"""

    @classmethod
    def build_data_context(cls, df: pd.DataFrame) -> str:
        """构建完整的数据上下文描述"""
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        datetime_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()

        ctx_parts = [f"## 当前数据集信息"]
        ctx_parts.append(f"- 行数: {len(df):,}")
        ctx_parts.append(f"- 列数: {len(df.columns)}")
        ctx_parts.append(f"- 列名: {', '.join(df.columns.tolist())}")
        ctx_parts.append(f"- 数值列 ({len(num_cols)}): {', '.join(num_cols) if num_cols else '无'}")
        ctx_parts.append(f"- 分类列 ({len(cat_cols)}): {', '.join(cat_cols) if cat_cols else '无'}")

        # 缺失值统计
        missing = df.isnull().sum()
        missing_cols = {col: int(cnt) for col, cnt in missing.items() if cnt > 0}
        if missing_cols:
            ctx_parts.append(f"- 含缺失值的列: {json.dumps(missing_cols, ensure_ascii=False)}")
        else:
            ctx_parts.append(f"- 缺失值: 无")

        # 重复行
        dup_count = int(df.duplicated().sum())
        ctx_parts.append(f"- 重复行: {dup_count}")

        # 数据预览（前10行）
        ctx_parts.append(f"\n## 数据预览（前10行）")
        try:
            preview = df.head(10).to_string(max_colwidth=30)
            if len(preview) > 3000:
                preview = df.head(5).to_string(max_colwidth=20)
            ctx_parts.append(f"```\n{preview}\n```")
        except Exception:
            ctx_parts.append("(无法生成预览)")

        # 数值列统计
        if num_cols:
            ctx_parts.append(f"\n## 数值列统计摘要")
            try:
                stats = df[num_cols].describe().to_string(max_colwidth=20)
                if len(stats) > 2000:
                    # 精简版
                    stats_df = df[num_cols].describe()
                    stats_lines = []
                    for col in num_cols:
                        s = stats_df[col]
                        stats_lines.append(f"  {col}: 均值={s['mean']:.2f}, 标准差={s['std']:.2f}, 最小={s['min']:.2f}, 最大={s['max']:.2f}, 中位数={s['50%']:.2f}")
                    ctx_parts.append("\n".join(stats_lines))
                else:
                    ctx_parts.append(f"```\n{stats}\n```")
            except Exception:
                ctx_parts.append("(无法生成统计)")

        # 分类列统计
        if cat_cols:
            ctx_parts.append(f"\n## 分类列概况")
            for col in cat_cols[:5]:
                try:
                    vc = df[col].value_counts().head(5)
                    items = [f"{k}: {v}" for k, v in vc.items()]
                    ctx_parts.append(f"  {col}: {', '.join(items)}")
                except Exception:
                    pass

        return "\n".join(ctx_parts)

    @classmethod
    async def test_connection(cls, ai_config: Dict[str, Any]) -> Dict[str, Any]:
        """测试 AI API 连接是否可用"""
        import httpx

        base_url = ai_config["base_url"].rstrip("/")
        test_messages = [
            {"role": "user", "content": "请回复'连接成功'这两个字。"},
        ]

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {ai_config['api_key']}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": ai_config["model_name"],
                        "messages": test_messages,
                        "max_tokens": 20,
                        "temperature": 0,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    return {
                        "success": True,
                        "message": f"连接成功！模型回复: {reply.strip()}",
                        "model": ai_config["model_name"],
                    }
                else:
                    error_detail = ""
                    try:
                        error_detail = resp.json()
                    except Exception:
                        error_detail = resp.text[:200]
                    return {
                        "success": False,
                        "message": f"API 返回错误 ({resp.status_code}): {error_detail}",
                    }
        except httpx.TimeoutException:
            return {"success": False, "message": "连接超时：请检查 API 地址是否正确，网络是否可达"}
        except httpx.ConnectError as e:
            return {"success": False, "message": f"连接失败：无法访问 {base_url}，请检查 URL 是否正确"}
        except Exception as e:
            return {"success": False, "message": f"连接测试失败: {str(e)}"}

    @classmethod
    async def chat_stream(
        cls,
        query: str,
        df: pd.DataFrame,
        ai_config: Dict[str, Any],
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        流式 AI 对话 — 逐步返回 LLM 生成的 token

        Yields:
            SSE 格式的事件字符串
        """
        import httpx

        base_url = ai_config["base_url"].rstrip("/")
        model_name = ai_config["model_name"]

        # 首先发送模型信息
        yield f"data: {json.dumps({'type': 'model', 'name': model_name})}\n\n"

        # 构建数据上下文
        data_context = cls.build_data_context(df)

        # 构建消息列表（含模型身份信息）
        messages = [{"role": "system", "content": cls._build_system_prompt(model_name)}]

        # 添加上下文消息（如果有）
        if chat_history:
            for msg in chat_history[-10:]:  # 最近10条
                if msg.get("role") in ("user", "assistant"):
                    messages.append({"role": msg["role"], "content": msg["content"]})

        # 添加当前数据上下文和用户问题
        user_message = f"{data_context}\n\n## 用户问题\n{query}"
        messages.append({"role": "user", "content": user_message})

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {ai_config['api_key']}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model_name,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 4096,
                        "stream": True,
                    },
                ) as resp:
                    if resp.status_code != 200:
                        error_text = ""
                        try:
                            error_body = await resp.aread()
                            error_text = error_body.decode()[:300]
                        except Exception:
                            error_text = f"HTTP {resp.status_code}"
                        yield f"data: {json.dumps({'type': 'error', 'message': f'API 错误 ({resp.status_code}): {error_text}'})}\n\n"
                        yield f"data: {json.dumps({'type': 'done'})}\n\n"
                        return

                    buffer = ""
                    async for chunk in resp.aiter_bytes():
                        if not chunk:
                            continue
                        buffer += chunk.decode("utf-8", errors="replace")

                        # 解析 SSE 行
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()
                            if not line or not line.startswith("data: "):
                                continue
                            data_str = line[6:]  # 去掉 "data: "
                            if data_str == "[DONE]":
                                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                                return

                            try:
                                data = json.loads(data_str)
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
                            except json.JSONDecodeError:
                                continue

                    # 流结束
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except httpx.TimeoutException:
            yield f"data: {json.dumps({'type': 'error', 'message': '请求超时，AI 服务响应过慢，请稍后重试'})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except httpx.ConnectError:
            yield f"data: {json.dumps({'type': 'error', 'message': '无法连接到 AI 服务，请检查 API 地址和网络连接'})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            logger.error(f"AI 流式调用失败: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': f'AI 服务异常: {str(e)}'})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    @classmethod
    async def chat(
        cls,
        query: str,
        df: pd.DataFrame,
        ai_config: Dict[str, Any],
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        非流式 AI 对话（兼容不支持 SSE 的客户端）
        """
        import httpx

        base_url = ai_config["base_url"].rstrip("/")
        model_name = ai_config["model_name"]
        data_context = cls.build_data_context(df)

        messages = [{"role": "system", "content": cls._build_system_prompt(model_name)}]
        if chat_history:
            for msg in chat_history[-10:]:
                if msg.get("role") in ("user", "assistant"):
                    messages.append({"role": msg["role"], "content": msg["content"]})

        user_message = f"{data_context}\n\n## 用户问题\n{query}"
        messages.append({"role": "user", "content": user_message})

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {ai_config['api_key']}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model_name,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 4096,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                reply = data["choices"][0]["message"]["content"]

                return {
                    "reply": reply,
                    "model": model_name,
                    "success": True,
                }
        except Exception as e:
            logger.error(f"AI 调用失败: {str(e)}")
            return {
                "reply": f"❌ AI 服务调用失败: {str(e)}\n\n请检查：\n1. API 配置是否正确（地址、密钥、模型名）\n2. 网络连接是否正常\n3. API 账户余额是否充足\n\n可以在 AI 配置中点击「启用」按钮测试连接。",
                "model": model_name,
                "success": False,
            }

    # ============ 自动洞察（保留规则引擎，用于数据探索） ============

    @classmethod
    def auto_discover_insights(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """自动发现数据中的洞察"""
        insights = []
        missing = df.isnull().sum()
        for col in df.columns:
            if missing[col] > 0:
                pct = missing[col] / max(len(df), 1) * 100
                insights.append({
                    "type": "data_quality",
                    "severity": "warning" if pct > 10 else "info",
                    "title": f"列 '{col}' 存在缺失值",
                    "description": f"列'{col}'存在{int(missing[col])}个缺失值（{pct:.1f}%），建议进行数据清洗",
                    "action": "建议使用数据清洗功能处理缺失值",
                })

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
                    "description": f"列'{col}'的标准差为{std:.2f}，变异系数{cv:.2f}，数据波动较大",
                    "action": "考虑使用箱线图查看分布，或对数据进行标准化",
                })

            Q1, Q3 = col_data.quantile(0.25), col_data.quantile(0.75)
            IQR = Q3 - Q1
            outlier_count = int(((col_data < Q1 - 1.5 * IQR) | (col_data > Q3 + 1.5 * IQR)).sum())
            if outlier_count > 0:
                insights.append({
                    "type": "outlier",
                    "severity": "warning" if outlier_count / len(col_data) > 0.1 else "info",
                    "title": f"列 '{col}' 存在异常值",
                    "description": f"列'{col}'中检测到{outlier_count}个异常值（IQR方法）",
                    "action": "建议使用异常值检测功能或箱线图查看详情",
                })

        if len(num_cols) >= 2:
            corr_matrix = df[num_cols].corr()
            for i in range(len(num_cols)):
                for j in range(i + 1, len(num_cols)):
                    corr_val = corr_matrix.iloc[i, j]
                    if abs(corr_val) >= 0.7:
                        insights.append({
                            "type": "correlation",
                            "severity": "info",
                            "title": "强相关性发现",
                            "description": f"'{num_cols[i]}'和'{num_cols[j]}'的相关系数为{corr_val:.2f}",
                            "action": "可以进一步分析因果关系",
                        })

        severity_order = {"warning": 0, "info": 1}
        insights.sort(key=lambda x: severity_order.get(x["severity"], 2))
        return insights[:15]
