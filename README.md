# 🚀 DataVision Pro - 交互式数据分析系统

## 📖 项目简介

一个基于 **FastAPI + ECharts + SQLite** 的现代化Web数据分析平台，采用赛博霓虹玻璃拟态设计风格，支持从数据上传到可视化分析、结果导出的完整流程。

## ✨ 核心特性

- 🎨 **赛博霓虹玻璃拟态UI**：科技感十足的现代化界面，动态粒子背景
- 🤖 **AI智能分析助手**：自然语言交互、自动洞察发现、智能图表推荐
- 📊 **丰富可视化**：支持12种ECharts图表类型（折线图、柱状图、饼图、散点图、箱线图、热力图、雷达图等）
- 🔧 **完整数据流程**：上传 → 清洗 → 分析 → 可视化 → 导出
- 🎭 **交互式探索**：图表联动、全屏查看、PNG导出、图例筛选
- 📱 **响应式设计**：桌面端、平板、移动端完美适配
- 🧠 **机器学习**：K-Means聚类、线性回归、Isolation Forest异常检测
- 📝 **分析报告**：一键生成精美的HTML数据分析报告

## 🛠️ 技术栈

- **后端**: FastAPI, Pandas, NumPy, Scikit-learn, SciPy, SQLAlchemy
- **前端**: 原生JavaScript (ES6+), ECharts 5, CSS3 (Glassmorphism + Cyberpunk)
- **数据库**: SQLite (WAL模式)
- **Python版本**: 3.10+

## 📁 项目结构

```
data-analysis-system/
├── README.md
├── requirements.txt
├── backend/
│   ├── main.py                      # FastAPI应用入口
│   ├── config.py                    # 全局配置
│   ├── database.py                  # 数据库连接与ORM
│   ├── models/
│   │   ├── schemas.py               # Pydantic API模型
│   │   └── database_models.py       # SQLAlchemy ORM模型
│   ├── services/
│   │   ├── data_service.py          # 数据处理服务
│   │   ├── cleaning_service.py      # 数据清洗服务
│   │   ├── analysis_service.py      # 统计分析服务
│   │   ├── ml_service.py            # 机器学习服务
│   │   ├── visualization_service.py # 可视化服务
│   │   └── ai_agent_service.py      # AI智能助手服务
│   ├── api/
│   │   ├── upload.py                # 文件上传API
│   │   ├── cleaning.py              # 数据清洗API
│   │   ├── analysis.py              # 数据分析API
│   │   ├── visualization.py         # 可视化API
│   │   ├── export.py                # 结果导出API
│   │   └── ai_agent.py              # AI助手API
│   ├── utils/
│   │   ├── file_handler.py          # 文件处理工具
│   │   └── validators.py            # 数据验证工具
│   ├── static/                      # 前端静态文件
│   │   ├── index.html
│   │   ├── css/
│   │   │   ├── style.css            # 全局样式
│   │   │   ├── glassmorphism.css    # 玻璃拟态核心样式
│   │   │   ├── animations.css       # 动画效果
│   │   │   └── components/          # 组件样式
│   │   ├── js/
│   │   │   ├── main.js              # 主控制逻辑
│   │   │   ├── api.js               # API调用封装
│   │   │   ├── charts.js            # ECharts图表管理
│   │   │   ├── ai-agent.js          # AI助手前端
│   │   │   ├── utils.js             # 工具函数
│   │   │   └── particles.js         # 粒子背景
│   │   └── lib/
│   │       └── echarts.min.js
│   └── uploads/                     # 上传文件存储
└── examples/                        # 示例数据集
    ├── sales_data.csv               # 销售数据
    ├── weather_data.csv             # 天气数据
    └── movie_ratings.csv            # 电影评分数据
```

## 📦 快速开始

### 环境要求

- Python 3.10+
- pip

### 安装步骤

```bash
# 1. 进入项目目录
cd data-analysis-system

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行项目
cd backend
python main.py

# 或使用uvicorn直接启动
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 访问地址

- **前端界面**: http://localhost:8000
- **API文档 (Swagger)**: http://localhost:8000/docs
- **API文档 (ReDoc)**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/api/health

## 🎯 功能模块

### 1. 📤 数据上传
- 支持CSV和Excel (.xlsx, .xls) 文件
- 拖拽上传或点击选择
- 最大10MB文件大小限制
- 自动检测编码和分隔符
- 实时显示数据预览和基本信息

### 2. 🧹 数据清洗
- **缺失值处理**: 删除、均值填充、中位数填充、众数填充
- **重复值删除**: 一键检测和删除重复行
- **异常值检测**: IQR方法 / Z-Score方法
- **数据类型转换**: 支持int/float/string/datetime转换
- **数据质量报告**: 完整性、一致性、唯一性评分

### 3. 🔍 数据分析
- **描述性统计**: 均值、标准差、偏度、峰度、分位数
- **相关性分析**: Pearson/Spearman/Kendall，自动生成热力图
- **分组聚合**: 多函数聚合（mean/sum/count/max/min）
- **机器学习**:
  - K-Means聚类（可选K值，含PCA可视化）
  - 线性回归（R²、MSE、特征重要性）
  - Isolation Forest异常检测
  - 时间序列趋势预测
  - Apriori关联规则挖掘

### 4. 📊 数据可视化
- **12种图表类型**: 折线图、柱状图、饼图、散点图、箱线图、热力图、雷达图、直方图、面积图、漏斗图
- **交互功能**:
  - 图例筛选和切换
  - 数据缩放（slider + inside）
  - 详细工具提示
  - 全屏查看模式
  - PNG导出
  - 图表联动

### 5. 💾 结果导出
- **数据导出**: 清洗后的CSV文件
- **图表导出**: 高分辨率PNG图片
- **报告导出**: 精美HTML格式分析报告

### 6. 🤖 AI智能助手
- **自然语言查询**: 支持中文提问
- **自动洞察发现**: 异常值、趋势、相关性自动识别
- **智能图表推荐**: 基于数据特征的最优图表推荐
- **数据故事生成**: 结构化分析报告

## 🎨 设计风格

采用**赛博霓虹 + 玻璃拟态（Neon Cyberpunk Glassmorphism）**设计：

- 🌌 深空蓝紫渐变背景 + Canvas动态粒子
- 🪟 半透明玻璃拟态卡片（backdrop-filter + 边框光晕）
- 💜 霓虹色彩方案（蓝紫/紫/粉/青蓝）
- ✨ 丰富的微交互动画（悬浮光效、涟漪、脉冲）

## 📊 示例数据

`examples/` 目录包含3个示例数据集：

1. **sales_data.csv** - 电子产品销售数据（50条）
   - 日期、产品名称、类别、销售数量、单价、销售额、地区、销售人员、客户评分

2. **weather_data.csv** - 四城市天气数据（60条）
   - 日期、城市、温度、降水量、湿度、风速、空气质量、天气状况

3. **movie_ratings.csv** - 电影评分数据（40条）
   - 电影名称、年份、类型、导演、片长、预算、票房、IMDb/豆瓣评分、观看人数

## 🔧 API端点概览

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/upload/` | 上传数据文件 |
| GET | `/api/upload/list` | 文件列表 |
| POST | `/api/clean/{file_id}` | 数据清洗 |
| GET | `/api/clean/quality/{file_id}` | 数据质量报告 |
| GET | `/api/analysis/statistics/{file_id}` | 描述性统计 |
| POST | `/api/analysis/correlation/{file_id}` | 相关性分析 |
| POST | `/api/analysis/cluster/{file_id}` | K-Means聚类 |
| POST | `/api/analysis/regression/{file_id}` | 线性回归 |
| POST | `/api/analysis/groupby/{file_id}` | 分组聚合 |
| POST | `/api/analysis/anomaly/{file_id}` | 异常检测 |
| POST | `/api/analysis/forecast/{file_id}` | 时间序列预测 |
| POST | `/api/visualization/{file_id}` | 生成图表 |
| GET | `/api/visualization/recommend/{file_id}` | 图表推荐 |
| GET | `/api/export/data/{file_id}` | 导出CSV |
| GET | `/api/export/report/{file_id}` | 导出HTML报告 |
| POST | `/api/ai/query` | AI自然语言查询 |
| GET | `/api/ai/insights/{file_id}` | 自动洞察发现 |

## 📄 许可证

MIT License

---

🤖 项目为Python课程教学实验设计 | DataVision Pro
