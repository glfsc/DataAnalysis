# DataVision Pro 数据分析系统 — 实验报告

**成员 A（组长）** | 负责模块：系统架构 + 数据管理 + 数据清洗与导出

---

## 1 整个系统分析与设计

### 1.1 系统概述

DataVision Pro 是一个基于 B/S 架构的交互式 Web 数据分析平台。系统的核心目标是让不具备编程能力的用户也能独立完成完整的数据分析工作。用户只需通过浏览器上传 CSV 或 Excel 数据文件，即可在同一个界面内依次完成数据清洗、统计分析、机器学习建模、可视化呈现和结果导出，全程无需编写任何代码。

系统将数据分析流程抽象为五个标准步骤：上传 → 清洗 → 分析 → 可视化 → 导出。用户按照这个流程逐步操作，每一步的输出自动成为下一步的输入，形成一条完整的、可追溯的数据处理链路。同时，系统还提供了 AI 智能助手（主要是正则查询）和用户认证系统（支持多用户注册登录、管理员管理），使平台具备基本的协作和安全能力。

从技术层面看，系统采用前后端分离架构：后端基于 Python FastAPI 框架，以 RESTful API 的形式提供所有业务能力；前端是纯静态的单页应用（SPA），由原生 JavaScript 配合 ECharts 可视化库构建。数据存储使用 SQLite 轻量级数据库，通过 SQLAlchemy ORM 进行管理。整个系统通过打包为 Docker 容器部署到 Railway 云平台。

### 1.2 系统功能

系统提供六大功能模块，覆盖数据分析的完整生命周期：

**（1）数据上传与管理**：支持 CSV 和 Excel（.xlsx / .xls）文件的拖拽或点击上传，单文件限制 10MB。上传时自动检测文件编码和分隔符，解析后立即展示数据预览和基本信息。上传后的文件在 Dashboard 中以卡片列表形式展示，支持多选和批量处理。每个文件配有五步进度指示器，清晰显示当前处理阶段。用户还可以通过全量数据预览弹窗查看完整数据，支持分页加载。

**（2）数据清洗**：用户可选则缺失值处理方案和异常值检测方法。缺失值处理方案可选：删除含缺失值的行 、均值填充 、中位数填充 、众数填充。异常值检测方法有：IQR 四分位距法 、 Z-Score 标准分数法。并且自动实现重复行自动删除、数据类型转换。清洗完成后展示前后对比（行数、缺失值、重复行的变化），被删除的数据行也会列出供用户核对。数据质量评分（完整性/一致性/唯一性）在后端已实现，当前仅在导出 HTML 报告时包含，前端清洗面板尚未集成该展示。

**（3）数据分析**：包含统计分析和机器学习两大子模块。统计分析提供描述性统计、相关性分析、分组聚合。机器学习提供五种聚类算法的多算法对比（K-Means、K-Medoids PAM、OPTICS、AGNES 层次聚类、GMM 高斯混合）、多元线性回归、Isolation Forest 异常检测、Apriori 关联规则挖掘和时间序列预测。

**（4）数据可视化**：后端可视化服务支持 4种 ECharts 图表类型的配置生成（折线图、柱状图、饼图、面积图），统一采用霓虹暗色主题。图表支持丰富的交互操作：点击数据点直接编辑值、双击标题或图例修改样式、长按拖拽组件重新定位、智能双 Y 轴（多系列量级差异大时自动分离 Y 轴）、合并相同 X 轴数据、自定义轴定义域。图表可导出为 PNG 图片，下方配有完整的数据表格支持 CRUD 编辑。

**（5）AI 智能助手**：基于规则引擎的自然语言交互模块。用户可以用中文自由提问（如"销售额最高的产品是什么""各地区的平均利润""数据有什么趋势"），系统通过正则模式匹配 + 列名提取 + 数字参数解析，返回文字回答和图表推荐。此外还提供自动洞察发现功能，从缺失值、波动性、偏态分布、异常值、类别集中度、强相关性六个维度自动扫描数据，输出最多 15 条按严重程度排序的洞察。

**（6）用户认证与管理**：提供完整的用户注册、登录、密码找回、个人信息编辑和头像上传裁剪功能。密码安全存储。首个注册用户自动成为管理员，管理员可通过专用面板查看所有用户、重置密码、切换管理员权限和删除用户。

此外，系统还支持结果导出、在线数据编辑和系统健康检查等辅助功能。

### 1.3 系统架构设计

系统采用经典的分层架构，自下而上分为五个层次，每一层有明确的职责边界，层与层之间通过定义良好的接口进行通信。

#### 1.3.1 整体分层结构

**第一层：基础设施层**

这是系统运行的物理基础。数据库采用 SQLite。文件存储使用本地磁盘目录，上传文件、清洗后文件和用户头像分别存放在不同子目录中。系统通过 `config.py` 中的 `DATA_DIR` 环境变量支持 Railway 等云平台的持久卷挂载，确保容器重启后数据不丢失。

**第二层：数据模型层（Models）**

分为两部分：SQLAlchemy ORM 模型负责数据库表结构的定义和映射，包含 5 张表——`users`（用户账户，含 PBKDF2 密码哈希字段）、`user_sessions`（登录会话，含令牌和过期时间）、`uploaded_files`（文件元数据，记录原始路径和清洗后路径）、`analysis_results`（分析结果缓存）和 `chart_configs`（图表配置持久化）。

**第三层：业务服务层（Services）**

这是系统的核心逻辑所在，包含 7 个独立的服务类，每个类专注于一个业务领域。服务类统一采用 `@classmethod` 设计，无实例状态，方法之间通过参数传递数据。这样的设计使服务层保持无状态特性，便于测试和水平扩展。

1、`DataService`：DataFrame 内存缓存池（最大 20 个，FIFO 淘汰）、文件加载（CSV 编码自动检测、Excel 解析）、数据预览和基本信息获取

2、CleaningService`：四步清洗流水线（缺失值处理 → 去重 → 类型转换 → 异常值标记）、数据质量三维度评估

3、AnalysisService`：描述性统计、Pearson/Spearman/Kendall 相关性分析、分组聚合、时间序列分析

4、`MLService`：五种聚类算法及多算法对比、线性回归、Isolation Forest 异常检测、Apriori 关联规则、时间序列预测

5、`VisualizationService`：4 种 ECharts 图表配置生成器、霓虹主题统一应用。

6、`AIAgentService`：9 种规则模式的自然语言查询处理、六维度自动洞察发现。

7、`AuthService`：PBKDF2 密码哈希与验证、会话令牌管理、管理员用户管理。

**第四层：API 网关层（FastAPI）**

基于 FastAPI 框架构建，承担请求路由、参数校验、认证鉴权和响应格式化的职责。系统共注册 8 个路由模块：

1、upload` 路由（3 个端点）：文件上传、列表查询、预览信息获取

2、`cleaning` 路由（1 个端点）：清洗执行

3、`analysis` 路由（6 个端点）：统计、相关性、分组、聚类、回归、异常检测

4、`visualization` 路由（1 个端点）：图表生成与配置保存

5、`export` 路由（2 个端点）：CSV 流式下载、HTML 报告生成

6、`ai_agent` 路由（2 个端点）：自然语言查询、自动洞察发现

7、`data_crud` 路由（8 个端点）：单元格/行/列的增删改查和批量替换

8、`auth` 路由（12 个端点）：注册、登录、登出、找回密码、个人信息、头像上传、管理员功能

API 层通过 FastAPI 的依赖注入机制获取数据库会话，在服务层完成业务处理后，对返回数据进行递归的 numpy 类型转换，确保所有值都是 JSON 可序列化的 Python 原生类型。全局异常处理器统一拦截 `RequestValidationError` 和未处理异常，返回格式一致的错误响应。CORS 中间件配置为允许所有来源的跨域请求，方便前后端分离开发。



**第五层：前端展示层（Frontend）**

前端是一个不依赖任何框架的纯原生 JavaScript 单页应用。采用"图切换模式而非页面跳转——所有功能视图都在 `index.html` 中预定义，通过 CSS `display` 控制显隐。顶部的 Step Stepper（1→2→3→4→5 流程条）和左侧的 Navigation Sidebar 提供双重导航入口。这种设计避免了频繁的页面加载，交互响应更快，状态保持更简单。

#### 1.3.2 技术选型说明

| 技术 | 选型理由 |
|------|---------|
| **FastAPI** | 高性能异步 Python Web 框架，自动生成 OpenAPI 文档（/docs），类型提示 + Pydantic 验证，适合构建 RESTful API |
| **SQLite + SQLAlchemy** | 轻量级零配置数据库，适合单机部署和小规模并发；WAL 模式提升读写性能；ORM 屏蔽 SQL 细节 |
| **Pandas + NumPy** | Python 数据分析的事实标准，DataFrame 抽象统一了 CSV/Excel 的数据操作 |
| **scikit-learn** | 提供 K-Means / OPTICS / AgglomerativeClustering / GMM / LinearRegression / IsolationForest 等成熟算法，API 统一 |
| **原生 JavaScript** | 对于教学/展示型项目，避免引入前端框架的学习成本和构建工具链，直接操作 DOM，代码即所见 |
| **ECharts 5** | 功能丰富的可视化库，支持 30+ 图表类型，交互能力强，中文文档完善 |
| **CSS Glassmorphism** | 通过 `backdrop-filter: blur()` + 半透明背景 + 渐变伪元素实现现代玻璃拟态效果，无需额外图片资源 |
| **Docker** | 一键构建和部署，环境一致性保证 |

### 1.4 模块分工说明

本项目由 3 名成员协作完成，按照功能领域进行模块划分：

1、成员 A负责系统基础架构与数据管理层。涵盖 FastAPI 应用框架搭建、数据库设计、数据模型定义、文件上传与管理、数据清洗流水线、数据 CRUD 接口、结果导出以及容器化部署。作为数据处理管道的入口和出口，为下游模块提供规范的数据基础。

2、**成员 B** 负责核心分析引擎。涵盖统计分析（描述性统计、相关性、分组聚合）、机器学习（五种聚类算法对比、回归、异常检测、关联规则、预测）以及 AI 智能助手（自然语言查询、自动洞察、数据故事）。是系统的算法核心。

3、**成员 C** 负责前端交互与用户系统。涵盖 SPA 应用架构与全局状态管理、ECharts 图表渲染与交互式编辑、用户认证全流程（含管理员系统），以及完整的 UI/UX 设计（玻璃拟态风格、动画系统、粒子背景）。是系统的用户交互层。

---

## 2 功能模块设计与接口说明

### 2.1 系统基础架构

#### 2.1.1 FastAPI 应用入口 ([main.py](backend/main.py))

`main.py` 是整个系统的启动入口和中央调度器，共注册 **8 个路由模块**：

```python
app.include_router(upload_router)         # /api/upload/*
app.include_router(cleaning_router)       # /api/cleaning/*
app.include_router(analysis_router)       # /api/analysis/*
app.include_router(visualization_router)  # /api/visualization/*
app.include_router(export_router)         # /api/export/*
app.include_router(ai_agent_router)       # /api/ai/*
app.include_router(data_crud_router)      # /api/data/*
app.include_router(auth_router)           # /api/auth/*
```

#### 2.1.2 配置中心 ([config.py](backend/config.py))

集中管理所有可配置项，通过环境变量支持不同部署环境：

```python
# 数据库：通过 DATA_DIR 环境变量支持 Railway 持久卷
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR)))
DB_PATH = DATA_DIR / "data_analysis.db"

# 文件上传：最大 10MB，支持 .csv/.xlsx/.xls
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

# 头像上传：最大 2MB，支持常见图片格式
MAX_AVATAR_SIZE = 2 * 1024 * 1024
ALLOWED_AVATAR_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

# 端口：通过 PORT 环境变量适配 Railway
PORT = int(os.getenv("PORT", "8000"))
```

### **2.1.3 数据库表**

**SQLAlchemy ORM** (77 行)：5 张核心数据表：

| 表名 | 主要字段 | 用途 |
|------|---------|------|
| `users` | username, password_hash, salt, email, display_name, avatar_url, is_admin | 用户账户 |
| `user_sessions` | user_id, token, expires_at | 登录会话 |
| `uploaded_files` | file_id, filename, file_path, cleaned_path, file_size, rows, columns, is_cleaned | 文件元数据 |
| `analysis_results` | file_id, analysis_type, result_data | 分析结果缓存 |
| `chart_configs` | file_id, chart_type, title, config | 图表配置持久化 |

### 2.2API 接口设计

#### 2.2.1 文件上传接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/upload` | POST | 上传 CSV/Excel 文件，返回预览 + 元数据 |
| `/api/upload/list` | GET | 获取所有已上传文件列表（按时间倒序） |
| `/api/upload/{file_id}/info` | GET | 获取指定文件的预览和列信息 |

#### 2.2.2 数据清洗接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/cleaning/clean` | POST | 执行数据清洗 |

请求参数包含：file_id、缺失值处理方法、是否删除重复行、异常值检测方法（iqr/zscore）、阈值。

#### 2.3.3 数据 CRUD 接口

支持对已上传数据进行完整的增删改查操作：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/data/{file_id}` | GET | 分页获取全量数据（limit/offset） |
| `/api/data/cell` | PUT | 更新单个单元格（含智能类型转换） |
| `/api/data/row` | POST | 添加新行 |
| `/api/data/row` | DELETE | 删除指定行 |
| `/api/data/column/rename` | PUT | 重命名列 |
| `/api/data/column` | DELETE | 删除列 |
| `/api/data/column` | POST | 添加新列（含默认值） |
| `/api/data/batch` | PUT | 批量全量替换数据 |

#### 2.3.4 结果导出接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/export/data` | POST | 流式下载清洗后 CSV 文件 |
| `/api/export/report` | POST | 生成 HTML 格式分析报告 |

### 2.4 工具与部署

**文件处理工具**：MD5/SHA256 哈希计算、文件名安全化（去除特殊字符）、扩展名提取、过期文件清理、人类可读文件大小格式化。

**参数验证工具**：列存在性验证、数值列验证、图表类型参数校验、聚类参数校验、字符串安全化。

**Docker 部署**：基于 `continuumio/miniconda3` 镜像，通过 `start.sh` 脚本启动，支持 Railway 的 `PORT` 环境变量动态绑定。

---

## 3 系统运行展示

### 3.1 文件上传与预览

用户在欢迎页点击"开始使用"进入主应用 ，点击"上传数据"选择文件。系统验证文件格式和大小后，自动解析并展示数据预览和基本信息。



欢迎界面展示：

![image-20260604201439701](C:/Users/glfsc/AppData/Roaming/Typora/typora-user-images/image-20260604201439701.png)

​                                                                                                   图1.欢迎界面

主页面展示：上方提供处理流程和当前页面所在步骤。左侧栏可切换到不同的数据处理步骤。中部仪表盘提供数据集总数、待处理文件数量、已完成分析数量、处理中文件数量统计。可勾选要选择处理的文件，并且通过卡片可以快速跳转到相应的处理步骤。每个文件最后方还展示了当前文件的处理进度。

![image-20260604201742533](C:/Users/glfsc/AppData/Roaming/Typora/typora-user-images/image-20260604201742533.png)

​                                                                                    图2.主界面展示

### 3.2 数据清洗 — 缺失值处理

进入清洗视图，选择"删除含缺失值的行"处理缺失值，勾选"删除重复行"，选择 IQR 方法检测异常值。点击"开始清洗"后，展示清洗前后对比。清洗后会展示

![image-20260604201533149](C:/Users/glfsc/AppData/Roaming/Typora/typora-user-images/image-20260604201533149.png)

​                                                                                图3.数据清洗完成界面



### 3.3数据 CRUD — 在线编辑

在可视化视图中，可直接编辑数据表格：双击单元格修改值、双击列头重命名、添加/删除行。还可以筛选数据，方便数据查找。修改后点击"保存修改"持久化。

![image-20260604203050099](C:/Users/glfsc/AppData/Roaming/Typora/typora-user-images/image-20260604203050099.png)

​                                                                                     图4.在线编辑数据表格



---

## 4 个人遇到的问题与解决方法

### 问题 1：Windows GBK 编码导致日志 emoji 乱码

**问题描述**：在 Windows 环境下运行后端时，日志中的 emoji 字符输出为乱码。原因是 Windows 的 `sys.stdout` 默认使用 GBK 编码，无法编码 emoji。

**解决方法**：在 `main.py` 启动日志配置后，显式将 stdout 重定向为 UTF-8 编码：

```python
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
```

使用 `errors="replace"` 参数确保无法编码的字符被替换而非抛出异常。

### 问题 2：Railway 部署 PORT 变量解析失败

**问题描述**：在 Railway 平台部署时，应用无法启动，报端口绑定错误。Railway 通过 `PORT` 环境变量动态分配端口，但某些启动方式下该变量未被正确解析。

**解决方法**：创建 `start.sh` 脚本替代直接启动命令：

```python
# config.py 中正确处理 PORT 变量
PORT = int(os.getenv("PORT", "8000"))
```

同时设计了 `DATA_DIR` 环境变量支持 Railway 持久卷挂载，确保数据库和上传文件不会因容器重启而丢失。

**对应 commit**：`fa42715 fix: 修复Railway部署PORT变量解析失败，改用start.sh脚本启动`

### 问题 3：CSV 编码兼容性问题

**问题描述**：用户上传的 CSV 文件可能使用 UTF-8、GBK、GB2312 等多种编码。如果固定使用一种编码读取，非该编码的文件会解析失败。

**解决方法**：在 `DataService.load_file()` 中实现编码回退机制：

```python
try:
    df = pd.read_csv(io.BytesIO(content), encoding="utf-8")
except UnicodeDecodeError:
    df = pd.read_csv(io.BytesIO(content), encoding="gbk")
```

先尝试最常见的 UTF-8，失败后回退到 GBK（中文 Windows 环境默认编码）。

---

## 5 个人收获与改进建议

### 5.1 个人收获

#### 5.1.1 系统架构设计的实践

作为组长和架构负责人，我深刻体会到"好的架构是演化出来的，不是一步设计出来的"。最初的架构只有上传 → 分析 → 可视化三个步骤，随着开发推进逐步加入了清洗、AI 助手、用户认证、数据 CRUD、导出等功能。关键在于：
- **模块化路由设计**：每个功能模块独立成一个 API 路由文件，新增功能只需添加路由而无需修改现有代码
- **统一的配置管理**：所有魔法数字和硬编码都集中在 `config.py`，修改部署参数不需要深入业务代码
- **清晰的分层边界**：API 层只做参数校验和路由，业务逻辑完全在 Service 层

#### 5.1.2 DataFrame 内存管理策略

设计了 DataFrame 缓存池机制——类级别的 `_data_cache` 字典，上限 20 个，FIFO 淘汰。这个设计在开发阶段足够了，但也让我意识到生产环境中需要用 Redis 等专业缓存方案来处理更大规模的数据。

#### 5.1.3 数据清洗的工程化实践

数据清洗看似简单，实际开发中有大量边界情况需要处理：
- 数值列和分类列需要不同的缺失值填充策略（mean 只能用于数值列）
- 异常值检测方法的选择取决于数据分布（IQR 适合偏态数据，Z-Score 适合正态分布）
- 类型转换需要 `errors="coerce"` 容错，避免因个别数据问题导致整列转换失败

### 5.2 改进建议

#### 5.2.1 架构层面

1. **引入任务队列**：上传大文件（接近 10MB）时的解析和清洗可能超过 HTTP 超时时间。建议引入 Celery + Redis 实现异步任务处理，前端通过轮询获取进度。

2. **数据库升级**：SQLite 在并发写入方面存在天然限制。当用户量增长到 50+ 并发时，建议迁移到 PostgreSQL，利用其行级锁和连接池。

3. **API 版本化**：当前所有 API 在 `/api/` 下无版本前缀。建议改为 `/api/v1/`，为未来不兼容的 API 变更预留空间。

#### 5.2.2 数据管理层面

1. **数据血缘追踪**：当前系统不记录数据变换的历史。建议在 `AnalysisResult` 表中增加操作链（operation_chain）字段，记录从原始数据到当前状态的完整变换路径。

2. **增量清洗**：当用户只修改了清洗的某一个参数时，不需要重新执行整个清洗流水线。可以引入"脏标记"机制，只重新执行变化的步骤。

3. **支持更多数据源**：目前只支持 CSV 和 Excel。可以考虑增加 JSON、Parquet 格式支持，以及直接连接 MySQL/PostgreSQL 数据库。

#### 5.2.3 部署层面

1. **健康检查增强**：当前 `/api/health` 只返回静态信息。建议增加数据库连接检查、磁盘空间检查、缓存状态检查，提供真实的健康状态。

2. **蓝色-绿色部署**：在 Railway 上实现蓝绿部署策略，`start.sh` 中加入健康检查等待逻辑，确保新版本就绪后再切换流量。

---

*报告完成日期：2026 年 6 月 4 日*
