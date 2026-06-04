# DataVision Pro 数据分析系统 — 实验报告

**成员 B** | 负责模块：数据分析引擎 + 机器学习 + AI 智能助手

---

## 1 整个系统分析与设计

### 1.1 项目背景与目标

DataVision Pro 是一个基于 Web 的交互式数据分析平台，目标是为非技术用户提供从数据上传到深度分析的一站式解决方案。用户无需编写任何代码，通过浏览器即可完成数据清洗、统计分析、机器学习建模、可视化呈现和报告导出等全流程操作。

系统采用前后端分离架构，后端提供 RESTful API，前端为单页应用（SPA），整体设计遵循"管道式"数据处理流程：

```
数据上传 → 数据清洗 → 统计分析 → 机器学习 → 可视化 → 导出报告
```

### 1.2 系统架构设计

系统采用经典的三层架构：

```
┌─────────────────────────────────────────────────────────────┐
│                     前端展示层 (Frontend)                      │
│  index.html + main.js + charts.js + auth.js + ai-agent.js   │
│         ECharts 5 可视化  |  CSS3 玻璃拟态风格                │
├─────────────────────────────────────────────────────────────┤
│                      API 网关层 (FastAPI)                      │
│   /api/upload  /api/cleaning  /api/analysis  /api/ai        │
│   /api/visualization  /api/export  /api/auth  /api/data     │
├─────────────────────────────────────────────────────────────┤
│                      业务服务层 (Services)                     │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │DataService│Cleaning  │Analysis  │ MLService│VizService│  │
│  │          │Service   │Service   │          │          │  │
│  ├──────────┴──────────┴──────────┴──────────┴──────────┤  │
│  │            AIAgentService  |  AuthService             │  │
│  └──────────────────────┬───────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    数据持久层 (SQLAlchemy + SQLite)            │
│   Users | UserSessions | UploadedFiles | AnalysisResults    │
└─────────────────────────────────────────────────────────────┘
```

- **前端展示层**：原生 JavaScript (ES6+) + ECharts 5，采用赛博霓虹玻璃拟态（Cyberpunk Glassmorphism）设计风格，Canvas 动态粒子背景
- **API 网关层**：FastAPI 框架，8 个路由模块，提供 RESTful 接口，CORS 中间件支持跨域访问
- **业务服务层**：7 个核心服务类，封装所有业务逻辑，采用类方法（`@classmethod`）设计，无状态服务
- **数据持久层**：SQLAlchemy ORM + SQLite（WAL 模式），5 张数据表

### 1.3 本人负责模块在系统中的定位

本人（成员 B）负责的是系统的**核心分析引擎**，包含三个子模块，在整体架构中处于"承上启下"的关键位置：

| 子模块 | 定位 | 上游依赖 | 下游消费 |
|--------|------|---------|---------|
| 统计分析服务 (analysis_service.py) | 基础统计计算层 | DataService 提供的 DataFrame | 可视化服务、AI 助手、导出服务 |
| 机器学习服务 (ml_service.py) | 高级算法层 | DataService、AnalysisService | 可视化服务（PCA 散点图）、前端聚类对比面板 |
| AI 智能助手 (ai_agent_service.py) | 智能交互层 | AnalysisService、VisualizationService | 前端 AI 聊天视图、洞察面板 |

这三个模块共同构成了系统的"大脑"——既提供底层的统计计算和机器学习算法，又向上提供自然语言交互的智能分析能力。用户上传数据后，无论是点击分析面板中的按钮进行聚类/回归/异常检测，还是在 AI 聊天框中输入自然语言问题，最终都由本人负责的服务层进行处理和响应。

### 1.4 技术选型说明

- **Pandas + NumPy**：作为数据分析的基础库，提供高效的 DataFrame 操作和数值计算
- **scikit-learn**：提供 K-Means、OPTICS、AgglomerativeClustering、GaussianMixture、LinearRegression、IsolationForest 等成熟算法实现
- **PCA 降维**：将高维聚类结果投影到 2D 平面用于散点图可视化
- **规则引擎 + 正则匹配**：AI 助手采用规则驱动而非调用外部 LLM API，确保离线可用、响应即时、无 API 费用
- **Pydantic**：API 层请求/响应模型的数据校验

---

## 2 功能模块设计与接口说明（本人负责）

本人负责三大功能模块，共涉及 5 个后端文件和 1 个前端文件，总计约 **2,200 行代码**。

---

### 2.1 统计分析服务 (analysis_service.py)

**文件路径**：`backend/services/analysis_service.py`（233 行）

**功能概述**：提供描述性统计、相关性分析、分组聚合、时间序列分析四大类基础统计功能。

#### 2.1.1 描述性统计 (`descriptive_statistics`)

**输入**：`pd.DataFrame`
**输出**：

```json
{
  "overall": {
    "total_rows": 1000,
    "total_columns": 12,
    "numeric_columns": 8,
    "categorical_columns": 4,
    "total_missing": 15,
    "total_duplicates": 3,
    "memory_usage_mb": 0.52
  },
  "numeric": {
    "销售额": {
      "mean": 5230.5, "std": 2100.3,
      "min": 120.0, "25%": 3200.0, "50%": 5100.0, "75%": 7200.0, "max": 15000.0,
      "variance": 4411260.09,
      "skewness": 0.35, "kurtosis": -0.42,
      "unique": 980, "missing": 5, "missing_pct": 0.5
    }
  },
  "categorical": {
    "地区": {
      "count": 1000, "unique": 4,
      "top": "华东", "freq": 350,
      "missing": 0, "missing_pct": 0.0
    }
  }
}
```

**核心逻辑**：
1. 使用 `df.select_dtypes(include=[np.number])` 分离数值列和分类列
2. 对数值列使用 `df.describe(percentiles=[0.25, 0.5, 0.75])` 获取基础统计量，补充方差、偏度、峰度、唯一值数、缺失值统计
3. 对分类列统计计数、唯一值、众数及其频次
4. 汇总整体数据质量指标

#### 2.1.2 相关性分析 (`correlation_analysis`)

**输入**：`DataFrame`, `columns`（可选，默认全部数值列）, `method`（pearson/spearman/kendall）

**输出**：

```json
{
  "correlation_matrix": [[1.0, 0.85, -0.32], [0.85, 1.0, -0.15], [-0.32, -0.15, 1.0]],
  "column_names": ["销售额", "利润", "折扣"],
  "heatmap_data": [[0, 1, 0.85], [0, 2, -0.32], [1, 2, -0.15]],
  "strong_correlations": [
    {"pair": ["销售额", "利润"], "correlation": 0.85, "strength": "强", "direction": "正相关"}
  ]
}
```

**核心逻辑**：
1. 调用 `df.corr(method=method)` 计算相关系数矩阵
2. 遍历矩阵上三角，筛选 |r| ≥ 0.5 的强相关对，按 |r| ≥ 0.7 区分"强"/"中等"强度
3. 生成 ECharts 热力图所需的三元组数据 `[x_index, y_index, value]`

#### 2.1.3 分组聚合分析 (`groupby_analysis`)

支持 8 种聚合函数：mean / sum / count / min / max / std / var / median。

**核心逻辑**：
1. 使用 `df.groupby(group_column).agg(agg_dict)` 执行分组聚合
2. 将结果展开为 `{列名: {函数名: [值列表]}}` 的层级结构
3. 对 NaN 值进行 None 替换以确保 JSON 序列化兼容

#### 2.1.4 时间序列分析 (`time_series_analysis`)

计算 3 日/7 日移动平均、百分比变化率，判断整体趋势方向和波动性。

**设计接口**：

| API 端点 | 方法 | 对应服务方法 | 说明 |
|---------|------|-------------|------|
| `/api/analysis/statistics` | POST | `descriptive_statistics()` | 描述性统计 |
| `/api/analysis/correlation` | POST | `correlation_analysis()` | 相关性矩阵 |
| `/api/analysis/groupby` | POST | `groupby_analysis()` | 分组聚合 |

---

### 2.2 机器学习服务 (ml_service.py)

**文件路径**：`backend/services/ml_service.py`（1,008 行，系统最大单文件）

**功能概述**：提供 5 种聚类算法、线性回归、异常检测、关联规则挖掘、时间序列预测共 9 大 ML 功能。

#### 2.2.1 多算法聚类系统（核心功能）

这是本模块最复杂的功能，实现了五种聚类算法的统一接口和横向对比机制。

**五种聚类算法一览**：

| 算法 | 类型 | 核心参数 | 特点 |
|------|------|---------|------|
| **K-Means** | 划分法 | `n_clusters` | 速度快，适合球形簇；使用惯性（inertia）评估 |
| **K-Medoids (PAM)** | 划分法 | `n_clusters`, `max_iter` | 使用实际数据点作为中心，对异常值鲁棒；纯 NumPy 实现 |
| **OPTICS** | 密度法 | `min_samples`, `xi` | 自动发现任意形状簇，无需预设 K 值；自动标记噪声点 |
| **AGNES** | 层次法 | `n_clusters`, `linkage` | 自底向上凝聚，支持 ward/complete/average/single 四种链接 |
| **GMM** | 概率模型 | `n_components`, `covariance_type` | 软聚类（概率分配），提供 BIC/AIC 模型选择指标 |

**多算法对比机制** (`multi_clustering`)：

```
用户选择算法 → 逐一执行 → 收集指标 → 横向对比 → 推荐最优
                                  ↓
            silhouette_score  /  calinski_harabasz_score  /  davies_bouldin_score
```

每种算法执行后自动计算三种聚类质量指标：
- **轮廓系数 (Silhouette Score)**：越大越好，衡量簇内紧密度与簇间分离度
- **CH 指数 (Calinski-Harabasz Index)**：越大越好，衡量簇间方差与簇内方差之比
- **DB 指数 (Davies-Bouldin Index)**：越小越好，衡量簇间相似度的平均值

最终按三种指标分别选出最优算法，返回给前端进行可视化对比。

**K-Medoids (PAM) 手工实现**：

由于 scikit-learn 不提供 K-Medoids，本模块使用纯 NumPy 手工实现了 PAM（Partitioning Around Medoids）算法：

```python
@staticmethod
def _euclidean_cdist(XA, XB):
    """纯 NumPy 欧几里得距离矩阵，无需 scipy 依赖"""
    XA_sq = np.sum(XA**2, axis=1, keepdims=True)
    XB_sq = np.sum(XB**2, axis=1, keepdims=True)
    dist_sq = XA_sq + XB_sq.T - 2 * np.dot(XA, XB.T)
    return np.sqrt(np.maximum(dist_sq, 0))
```

核心流程：随机初始化 medoids → 分配每个点到最近的 medoid → 在每个簇内选择最小化簇内距离和的点作为新 medoid → 迭代直到 medoids 不再变化。

**PCA 降维可视化**：

所有聚类算法均内置 PCA 降维（2 维），将高维特征空间投影到二维平面，输出 `scatter_data`（x、y、labels、方差解释率）供前端绘制彩色散点图。

#### 2.2.2 线性回归 (`linear_regression`)

**核心流程**：

```
特征矩阵 X + 目标向量 y
    ↓
train_test_split (默认 8:2)
    ↓
StandardScaler 标准化
    ↓
sklearn LinearRegression 训练
    ↓
输出：系数、截距、R²、MSE、RMSE、训练集 R²、特征重要性
```

**特征重要性**基于标准化系数的绝对值占比计算：`importance_i = |coef_i| / Σ|coef_j|`。

小数据集（< 20 行）自动调整测试集比例为 30%，避免测试集过小。

#### 2.2.3 异常检测 (`anomaly_detection`)

使用 **Isolation Forest**（100 棵树的集成）检测异常，同时提供 **IQR 辅助分析**。

**输出亮点**：
- 每行异常的归一化异常分数（0~1，越高越异常）
- 每行中哪些列的值超出 IQR 范围（标注列名、实际值、上下界）
- 完整数据行内容（方便用户核查）

```json
{
  "anomaly_count": 23,
  "anomaly_ratio": 4.6,
  "anomaly_rows": [
    {
      "index": 142,
      "score": 0.92,
      "data": {"销售额": 99999, "数量": 1, "日期": "2024-03-15", ...},
      "outlier_columns": [
        {"column": "销售额", "value": 99999, "lower_bound": 500, "upper_bound": 15000}
      ]
    }
  ],
  "col_iqr_bounds": {
    "销售额": {"Q1": 3200, "Q3": 7200, "IQR": 4000, "lower": -2800, "upper": 13200}
  }
}
```

#### 2.2.4 Apriori 关联规则挖掘 (`apriori_association`)

**简易实现**：遍历单列频繁项和多列组合（两两组合），计算 support / confidence / lift 三个经典指标。限制每列最多前 10 个值参与组合，总规则上限 50 条。

#### 2.2.5 时间序列预测 (`time_series_forecast`)

使用线性回归进行趋势外推，配合历史残差标准差构建 **95% 置信区间**（`prediction ± 1.96 × σ_residuals`）。

**设计接口**：

| API 端点 | 方法 | 对应服务方法 | 说明 |
|---------|------|-------------|------|
| `/api/analysis/cluster` | POST | `multi_clustering()` | 多算法聚类对比 |
| `/api/analysis/regression` | POST | `linear_regression()` | 多元线性回归 |
| `/api/analysis/anomaly` | POST | `anomaly_detection()` | Isolation Forest 异常检测 |

---

### 2.3 AI 智能助手服务 (ai_agent_service.py)

**文件路径**：`backend/services/ai_agent_service.py`（646 行）

**功能概述**：提供基于规则引擎的自然语言查询处理、自动洞察发现和数据故事生成三大功能。

#### 2.3.1 自然语言查询引擎 (`process_query`)

**核心架构：规则匹配 + 正则提取**

```
用户输入查询文本
      ↓
正则模式匹配（9 种预定义模式，按优先级逐一匹配）
      ↓
提取列名（匹配 DataFrame 列名）
      ↓
提取数字参数（如 top N）
      ↓
路由到对应的处理函数（共 9 种）
      ↓
返回：回答文本 + 图表推荐 + 洞察列表
```

**9 种查询模式**：

| 模式 | 触发词 | 处理函数 | 示例问题 |
|------|--------|---------|---------|
| find_extreme:max | 最大/最高/最多/max/top | `_find_extreme(max)` | "销售额最高的产品是什么" |
| find_extreme:min | 最小/最低/最少/min | `_find_extreme(min)` | "哪个地区利润最低" |
| calculate_stat:mean | 平均/均值/average/mean | `_calculate_stat(mean)` | "各产品的平均评分" |
| calculate_stat:sum | 总和/合计/total/sum | `_calculate_stat(sum)` | "今年总销售额是多少" |
| sort_data | 排序/排名/排行/sort | `_sort_data_info` | "按利润降序排列" |
| analyze_trend | 趋势/trend/走势/变化 | `_analyze_trend` | "销售额的趋势如何" |
| analyze_distribution | 分布/distribution/频率 | `_analyze_distribution` | "客户评分的分布情况" |
| analyze_correlation | 相关/correlation/关系 | `_analyze_correlation_query` | "广告支出和销售额有关系吗" |
| recommend_chart | 推荐/建议/用什么图 | `_recommend_chart_for_query` | "推荐一个合适的图表" |
| data_overview | 概览/概况/overview/总结 | `_generate_data_overview` | "给我一个数据概览" |

**兜底机制**：当没有模式匹配时，`_generate_fallback_response` 提供帮助信息和可用数值列列表。

#### 2.3.2 自动洞察发现 (`auto_discover_insights`)

系统自动扫描数据并生成最多 15 条洞察，按严重程度（warning > info）排序。检测维度：

| 洞察类型 | 检测方法 | 严重程度规则 |
|---------|---------|------------|
| 缺失值 | `df.isnull().sum()` | > 10% → warning |
| 高方差 | 变异系数 CV > 1.5 | info |
| 偏态分布 | \|skewness\| > 1 | info |
| 异常值 | IQR 方法（Tukey Fences） | > 10% → warning |
| 类别集中 | 众数占比 > 80% | info |
| 强相关性 | \|Pearson r\| ≥ 0.7 | info |

#### 2.3.3 数据故事生成 (`generate_data_story`)

生成结构化分析报告，支持四个章节：
1. **概览 (overview)**：数据规模、完整性评估、关键指标
2. **分析 (analysis)**：强相关关系、关键发现
3. **洞察 (insights)**：自动发现的 TOP 8 条洞察
4. **建议 (recommendations)**：基于数据特征的图表和行动建议

**设计接口**：

| API 端点 | 方法 | 对应服务方法 | 说明 |
|---------|------|-------------|------|
| `/api/ai/query` | POST | `process_query()` | 自然语言查询 |
| `/api/ai/insights` | POST | `auto_discover_insights()` | 自动洞察发现 |

#### 2.3.4 前端 AI 模块 (ai-agent.js)

前端 AI 模块（22 行）提供了轻量级的聊天历史管理：

```javascript
const AIAgent = {
    history: [],
    addToHistory(role, text) { /* 添加消息，上限 50 条 */ },
    getHistory() { /* 获取历史副本 */ },
    clearHistory() { /* 清空历史 */ },
};
```

主要的 AI 交互 UI 逻辑整合在 `main.js` 的 AI 视图中，包括消息发送、回复渲染、图表推荐展示等。

---

### 2.4 模块间调用关系

```
api/analysis.py ──→ AnalysisService.descriptive_statistics()
                ├─→ AnalysisService.correlation_analysis()
                ├─→ AnalysisService.groupby_analysis()
                ├─→ MLService.multi_clustering()
                ├─→ MLService.linear_regression()
                └─→ MLService.anomaly_detection()

api/ai_agent.py ──→ AIAgentService.process_query()
                 └─→ AIAgentService.auto_discover_insights()
                           │
                           ├─→ AnalysisService.descriptive_statistics()
                           ├─→ AnalysisService.correlation_analysis()
                           └─→ VisualizationService.recommend_charts()
```

AI 助手服务依赖于统计分析服务和可视化服务，体现了模块间的高内聚、低耦合设计——AI 助手不需要重复实现统计功能，而是复用已有的 AnalysisService。

---

## 3 系统运行展示（侧重个人部分）

### 3.1 统计分析 — 描述性统计

上传 sales_data.csv 后，进入"分析"视图，点击"描述性统计"卡片。系统返回数据整体概览、各数值列的均值/标准差/偏度/峰度/分位数，以及分类列的值分布。

（此处插入截图：描述性统计结果面板，展示 overall 指标和 numeric 统计表）

### 3.2 统计分析 — 相关性热力图

选择"相关性分析"，系统自动计算全部数值列的 Pearson 相关系数矩阵，并以热力图形式展示，同时列出强相关对。

（此处插入截图：相关性热力图 + 强相关对列表）

### 3.3 机器学习 — 多算法聚类对比

选择"聚类分析"，勾选全部 5 种算法（K-Means、K-Medoids、OPTICS、AGNES、GMM），设置 K=3。系统依次执行 5 种算法，返回对比表：

| 算法 | K值 | 轮廓系数 | CH指数 | DB指数 | 特有指标 |
|------|-----|---------|--------|--------|---------|
| K-Means | 3 | 0.423 | 128.5 | 0.89 | 惯性: 245.3 |
| K-Medoids (PAM) | 3 | 0.418 | 122.1 | 0.92 | 总距离: 198.7 |
| OPTICS | 4 | 0.386 | 105.3 | 1.05 | 噪声点: 12 |
| AGNES (ward) | 3 | 0.445 | 135.2 | 0.81 | — |
| GMM (full) | 3 | 0.431 | 130.8 | 0.85 | BIC: 1523.4 |

最优算法（按轮廓系数）：**AGNES (ward)**
最优算法（按 CH 指数）：**AGNES (ward)**
最优算法（按 DB 指数）：**AGNES (ward)**

切换各个算法的 Tab 可查看 PCA 降维散点图和各簇的中心值、样本量分布。

（此处插入截图：聚类对比面板，展示对比表 + PCA 散点图 + 簇中心表格）

### 3.4 机器学习 — 异常检测

选择"异常检测"，系统使用 Isolation Forest 识别异常数据行。返回异常总数、异常比例、每行的异常分数和具体哪些列的值超出了 IQR 范围。

（此处插入截图：异常检测结果面板，展示异常行表格，异常列用红色高亮）

### 3.5 机器学习 — 线性回归

选择"回归分析"，以"广告支出"和"促销折扣"为特征，以"销售额"为目标。系统返回：
- 回归方程系数和截距
- R² 得分（模型拟合优度）
- MSE / RMSE（预测误差）
- 特征重要性排序
- 预测值 vs 实际值对比

（此处插入截图：回归分析结果面板）

### 3.6 AI 助手 — 自然语言查询

在 AI 助手视图中输入："销售额最高的 5 个产品是什么？"

系统回复：
> **销售额** 的最大值是 **15,000.00**，对应数据行: ...

同时附带了图表推荐："建议使用柱状图展示各产品的销售额对比"。

（此处插入截图：AI 助手聊天界面，展示用户问题和 AI 回复）

### 3.7 AI 助手 — 自动洞察发现

点击"自动洞察"按钮，系统扫描数据后返回：

- ⚠️ **列 '折扣' 存在缺失值**（12 个，占 2.4%）— 建议使用数据清洗功能处理
- ℹ️ **列 '销售额' 波动较大**（CV=1.82）— 考虑使用箱线图查看分布
- ℹ️ **强相关性发现**：销售额与利润的相关系数为 0.85，存在强正相关关系
- ...共 8 条洞察

（此处插入截图：AI 洞察面板，展示自动发现的数据特征和问题）

---

## 4 个人遇到的问题与解决方法

### 问题 1：GMM 聚类参数 `n_clusters` 与 `n_components` 不兼容

**问题描述**：在多算法聚类对比功能 (`multi_clustering`) 中，前端统一传递 `n_clusters` 参数给所有算法。但 sklearn 的 `GaussianMixture` 使用 `n_components` 而非 `n_clusters` 作为参数名，导致 GMM 运行时抛出 `TypeError: unexpected keyword argument 'n_clusters'`。

**解决方法**：在 `multi_clustering` 方法中为 GMM 添加参数名转换逻辑：

```python
elif algo_key == "gmm":
    algo_params.setdefault("n_components",
        algo_params.pop("n_clusters", params.get("n_clusters", 3)))
    algo_params.pop("n_clusters", None)  # 移除不被 GMM 接受的参数
```

使用 `pop` 将 `n_clusters` 提取出来赋值给 `n_components`，然后再用 `pop("n_clusters", None)` 清理残留，确保传给 `GaussianMixture()` 的参数中不会有 `n_clusters`。

这个问题的根本原因是各 ML 库的 API 设计不统一。K-Means 用 `n_clusters`，GMM 用 `n_components`，OPTICS 甚至不需要预设簇数。在设计统一接口时，需要在适配层做好参数映射和清理。

**对应 commit**：`bf02f25 fix: GMM聚类参数n_clusters与n_components不兼容`

### 问题 2：K-Medoids 算法缺少现成实现

**问题描述**：设计多算法聚类对比时，希望包含 K-Medoids（PAM）算法——它使用实际数据点作为簇中心，对异常值比 K-Means 更鲁棒，是重要的算法对比维度。但 scikit-learn 不提供 K-Medoids 实现，而 scipy 的 `cdist` 也不在项目依赖中。

**解决方法**：手工实现了完整的 PAM 算法，并编写了纯 NumPy 的欧几里得距离矩阵函数 `_euclidean_cdist`，避免引入 scipy 依赖：

```python
@staticmethod
def _euclidean_cdist(XA, XB):
    """纯 numpy 欧几里得距离矩阵"""
    XA_sq = np.sum(XA**2, axis=1, keepdims=True)
    XB_sq = np.sum(XB**2, axis=1, keepdims=True)
    dist_sq = XA_sq + XB_sq.T - 2 * np.dot(XA, XB.T)
    return np.sqrt(np.maximum(dist_sq, 0))
```

利用 $(a-b)^2 = a^2 + b^2 - 2ab$ 的向量化展开，避免了 Python 循环，性能接近原生 C 实现。

PAM 主循环中，每个簇内选择新的 medoid 时，需要计算簇内所有点两两之间的距离矩阵并求和——这一步的计算复杂度是 O(n²)。对于大数据集（n > 5000），这可能很慢。解决的思路是对于大数据集，在计算评估指标（如轮廓系数）时进行随机采样（`sample_size = min(5000, n_samples)`），在不影响结果可靠性的前提下控制计算时间。

### 问题 3：OPTICS 聚类标签中的噪声点（-1）处理

**问题描述**：OPTICS 算法将无法归入任何簇的点标记为 -1（噪声）。在计算轮廓系数、CH 指数、DB 指数等聚类质量指标时，这些噪声点会导致 `silhouette_score` 等函数报错或产生无意义的结果，因为 -1 被当作了一个合法的簇标签。

**解决方法**：在计算评估指标时，使用布尔掩码排除噪声点：

```python
if n_clusters > 1:
    non_noise_mask = labels != -1
    if non_noise_mask.sum() > n_clusters * 2:
        silhouette = float(silhouette_score(
            X_scaled[non_noise_mask], labels[non_noise_mask]
        ))
```

同时检查排除噪声后剩余样本数是否足够（至少是簇数的 2 倍），避免样本过少导致的数值不稳定。

### 问题 4：AI 助手规则覆盖不足与兜底策略

**问题描述**：AI 助手基于 9 种预定义正则模式匹配用户查询。但用户输入是开放式的自然语言，不可避免地会出现无法匹配的情况。例如用户输入"帮我看看这些数据有没有什么问题"，这个查询不直接匹配任何一种模式。

**解决方法**：设计了 `_generate_fallback_response` 兜底机制。当没有模式匹配时，系统不会简单返回"我不理解"，而是：
1. 确认收到用户的问题
2. 列出系统能处理的所有能力（查看概览、分析趋势、计算统计量等）
3. 列出当前数据集的可用数值列名

这样即使无法精确回答，也给用户提供了明确的下一步操作指引，引导用户使用系统支持的功能。

### 问题 5：大数据集 PCA 可视化的性能问题

**问题描述**：当数据集超过 10,000 行时，PCA 降维和散点图渲染的前端数据量过大，导致页面响应缓慢。

**解决方法**：在评估指标计算时加入采样机制（`sample_size = min(5000, n_samples)`）控制计算规模。对于散点图数据，可以进一步在前端进行数据抽样渲染。目前 5,000 点的阈值是一个经验折中值——既保留了聚类的整体形态特征，又保证了交互流畅性。

---

## 5 个人收获与改进建议

### 5.1 个人收获

#### 5.1.1 对多种聚类算法的深入理解

本项目实现了 5 种不同类型的聚类算法，并设计了横向对比机制，这让我深入理解了不同聚类范式的适用场景和评估方法：

- **K-Means** 适合大数据集、球形簇，但对初始中心和异常值敏感。其"惯性"指标仅适合同 K 值下的算法内比较，不适合跨 K 值或跨算法比较
- **K-Medoids** 使用实际数据点作为代表，天然抗异常值，但计算复杂度更高（每次迭代需要计算簇内全距离矩阵）
- **OPTICS** 无需预设簇数，能发现任意形状的簇，但 `xi` 参数的调节直接影响簇提取结果，需要通过调试找到合适的值
- **AGNES（层次聚类）** 通过树状图直观展示合并过程，`ward` 链接倾向于产生大小均衡的簇
- **GMM（高斯混合）** 提供了软聚类（概率分配）和 BIC/AIC 模型选择能力，但需要假设数据服从高斯分布

三种评估指标各有侧重：轮廓系数关注紧密度和分离度的平衡，CH 指数偏好簇间方差大、簇内方差小的划分，DB 指数从"相似度最小化"的角度评估。综合三种指标选出推荐算法，比单一指标更可靠。

#### 5.1.2 规则引擎 vs LLM 的设计取舍

AI 助手采用了纯规则引擎而非调用大语言模型 API。这个设计决策让我体会到工程实践中"够用就好"的原则：

- **优势**：零 API 调用费用、毫秒级响应、无网络依赖、结果可预测可调试
- **局限**：无法处理规则外的复杂查询、不具备上下文理解能力、扩展性受限于规则库规模

对于一个教育/展示型项目，规则引擎是合适的。但在生产环境中，可以考虑将规则引擎作为前端意图识别器，将匹配到的结构化查询 + 上下文交给 LLM 生成更自然的回复，形成"规则路由 + LLM 生成"的混合架构。

#### 5.1.3 机器学习工程化的实践经验

在将 ML 算法集成到 Web 服务的过程中，学到了几个工程化要点：
- **参数校验前置**：在 API 层就验证数据量和参数合法性（如聚类要求 n ≥ n_clusters），避免在服务层抛出难以理解的错误
- **异常隔离**：`multi_clustering` 中每种算法独立 try-catch，一种算法失败不影响其他算法的执行和对比
- **采样策略**：大数据集下对评估指标计算进行采样，平衡精度和性能
- **数据类型转换**：Pandas/NumPy 的 int64/float64 类型需要显式转换为 Python 原生 int/float 才能被 JSON 序列化

### 5.2 改进建议

#### 5.2.1 聚类算法方面

1. **自动确定最优 K 值**：目前需要用户手动输入 K 值。可以引入肘部法则（Elbow Method）和 Gap Statistic，自动推荐最优 K 值，降低使用门槛。

2. **增加 DBSCAN 算法**：虽然已有 OPTICS（DBSCAN 的泛化版本），但 DBSCAN 的 `eps` 参数更直观，且运行速度更快，适合作为快速密度聚类的选项。

3. **聚类结果的可解释性**：当前聚类中心以数值形式展示，可以增加每个簇的"特征画像"——例如"簇 1：高销售额、中等利润、低折扣"，用自然语言描述每个簇的业务特征。

#### 5.2.2 AI 助手方面

1. **增加上下文记忆**：当前每次查询是独立的，不记忆之前的对话。可以引入会话上下文，支持追问（如"那第二高的呢？"），需要维护一个对话状态对象。

2. **引入 embedding 语义匹配**：当前使用正则模式匹配，对同义表达（如"哪个卖得最好" vs "销量冠军是什么"）需要分别维护规则。可以使用轻量级文本 embedding 进行语义相似度匹配，提高召回率。

3. **与 LLM 的混合架构**：将规则引擎作为第一层过滤器，当置信度不足时回退到 LLM API——前端增加"深度分析"按钮，触发 LLM 生成更详细的报告。这样既保持了离线场景的可用性，也能在联网时提供更智能的分析。

#### 5.2.3 整体系统方面

1. **分析结果持久化**：目前分析结果缓存在内存中，刷新页面后需要重新计算。建议将聚类结果、回归模型参数、异常检测结果保存到数据库的 `AnalysisResult` 表中，支持历史分析回顾。

2. **分析任务异步化**：对于大数据集的聚类和异常检测（如 > 50,000 行），同步 HTTP 请求会导致超时。建议引入 FastAPI 的 `BackgroundTasks` 或 Celery 任务队列，将长任务改为异步执行 + 轮询结果。

3. **增加模型导出功能**：训练好的线性回归模型可以导出为 PMML 或 pickle 文件，供外部系统使用。这样数据分析平台不仅是分析工具，还能成为简单的模型训练平台。

---

*报告完成日期：2026 年 6 月 4 日*
