# DataVision Pro 数据分析系统 — 实验报告

**成员 C** | 负责模块：前端交互 + 数据可视化 + 用户认证系统

---

## 1 整个系统分析与设计

### 1.1 项目背景与目标

DataVision Pro 是一个面向非技术用户的 Web 数据分析平台。与 Jupyter Notebook 等需要编程能力的工具不同，本系统的核心设计理念是"所见即所得"——用户通过浏览器界面完成从数据上传到报告导出的完整分析流程，全程无需编写代码。

### 1.2 系统总体架构

系统采用前后端分离的 B/S 架构：

```
┌─────────────────────────────────────────────────────────────┐
│                   前端展示与交互层 (本人负责核心部分)           │
│                                                             │
│  ┌─────────┬──────────┬──────────┬──────────┬──────────┐   │
│  │Welcome  │Dashboard │Cleaning  │Analysis  │Viz+CRUD  │   │
│  │粒子背景  │文件管理   │配置面板   │6合1面板   │图表+表格  │   │
│  ├─────────┴──────────┴──────────┴──────────┴──────────┤   │
│  │           AI 助手视图 (聊天界面)          │ Export 视图 │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │   Auth 系统：登录/注册/找回模态框 | 头像裁剪 | 管理员面板  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  技术栈：原生 JS (ES6+) + ECharts 5 + CSS3 Glassmorphism    │
├─────────────────────────────────────────────────────────────┤
│                    API 网关层 (FastAPI)                       │
│  /api/upload | /api/cleaning | /api/analysis | /api/ai     │
│  /api/visualization | /api/export | /api/auth | /api/data  │
├─────────────────────────────────────────────────────────────┤
│                    业务服务与数据层                            │
│  Services → SQLAlchemy ORM → SQLite (WAL)                   │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 前端 SPA 架构设计

前端采用**单页应用（SPA）**架构，核心是一个全局 `App` 对象（约 1,130 行），通过**视图切换**而非页面跳转来实现导航。这种设计避免了频繁的页面重载，提供流畅的用户体验。

**前端模块依赖关系**：

```
index.html (SPA 骨架，220行)
    │
    ├── js/utils.js        工具函数库 (102行)
    ├── js/api.js          HTTP 客户端 (115行)
    ├── js/auth.js         认证模块 (878行)
    ├── js/charts.js       图表引擎 (600行)
    ├── js/ai-agent.js     AI 聊天历史 (22行)
    ├── js/particles.js    粒子背景 (154行)
    └── js/main.js         主控制器 (1,130行) ← 调度所有模块
            │
            ├── css/style.css          全局样式 (~810行)
            ├── css/glassmorphism.css   玻璃拟态 (119行)
            └── css/animations.css      动画库 (230行)
```

**视图系统**：系统包含 5 个主视图（Dashboard、清洗、分析、可视化、AI 助手），通过 `App.switchView(viewName)` 切换。每个视图对应一个 `<section class="view">` 元素，通过 CSS `display` 控制显隐。顶部 stepper（步骤条）和左侧 sidebar 提供两种导航方式。

### 1.4 本人负责模块概览

| 类别 | 文件 | 行数 | 职责 |
|------|------|------|------|
| SPA 骨架 | [index.html](frontend/index.html) | 220 | 完整 HTML 结构、5 个主视图、模态框、Toast、Loading |
| 主控制器 | [js/main.js](frontend/js/main.js) | 1,130 | App 全局状态管理、视图切换、事件绑定、Dashboard、清洗/分析/可视化面板交互逻辑 |
| API 客户端 | [js/api.js](frontend/js/api.js) | 115 | 全接口 fetch 封装、Auth Token 自动注入、XHR 上传带进度 |
| 工具函数 | [js/utils.js](frontend/js/utils.js) | 102 | Toast 通知、格式化、防抖/节流、HTML 转义 |
| 图表引擎 | [js/charts.js](frontend/js/charts.js) | 600 | ECharts 实例管理、智能双 Y 轴、数据点编辑、标题/图例样式编辑、长按拖拽、PNG 导出 |
| 认证模块 | [js/auth.js](frontend/js/auth.js) | 878 | 登录/注册/找回模态框、Token 持久化、头像上传裁剪 UI、管理员面板、设置面板 |
| 粒子背景 | [js/particles.js](frontend/js/particles.js) | 154 | Canvas 粒子系统、连线效果、响应式 |
| 后端可视化 | [services/visualization_service.py](backend/services/visualization_service.py) | 643 | 10 种 ECharts 图表配置生成器（后端完整支持，前端当前开放4种）、霓虹主题、智能图表推荐 |
| 后端认证 | [services/auth_service.py](backend/services/auth_service.py) | 280 | PBKDF2 密码哈希、会话管理、管理员功能 |
| 可视化 API | [api/visualization.py](backend/api/visualization.py) | 90 | 图表生成与配置保存 |
| 认证 API | [api/auth.py](backend/api/auth.py) | 341 | 注册/登录/找回/信息/头像/管理员 全套接口 |
| UI 样式 | [css/style.css](frontend/css/style.css) | ~810 | 全局样式、响应式布局（1200px/768px 断点） |
| 玻璃拟态 | [css/glassmorphism.css](frontend/css/glassmorphism.css) | 119 | 4 色玻璃卡片、悬浮光效 |
| 动画系统 | [css/animations.css](frontend/css/animations.css) | 230 | 15+ 关键帧动画 |

---

## 2 功能模块设计与接口说明（本人负责）

### 2.1 前端核心架构 (main.js)

#### 2.1.1 全局状态管理

`App.state` 对象集中管理所有全局状态：

```javascript
state: {
    files: {},              // {file_id: {fileName, rowCount, progress, ...}}
    fileOrder: [],          // 文件顺序列表
    selectedIds: [],        // 多选文件 ID（支持批量处理）
    currentFileId: null,    // 当前活动文件
    currentView: 'dashboard', // 当前视图
    currentStep: 'upload',  // 当前 stepper 步骤
    currentChart: null,     // 当前 ECharts 实例
    editedData: null,       // 可视化编辑中的数据
}
```

**多文件管理**：系统支持同时上传多个文件，通过 `selectedIds` 数组支持多选批量处理。Dashboard 的文件列表显示每个文件的 5 步进度状态（上传→清洗→分析→可视化→导出）。

#### 2.1.2 视图切换与导航

```javascript
switchView(viewName) {
    // 1. 隐藏所有视图
    // 2. 显示目标视图
    // 3. 更新 sidebar 高亮
    // 4. 更新 stepper 步骤
    // 5. 执行视图初始化逻辑
}
```

**双导航系统**：
- **左侧 Sidebar**：5 个导航项（仪表盘、清洗、分析、可视化、AI 助手）
- **顶部 Stepper**：5 步流程条（上传→清洗→分析→可视化→导出），点击步骤直接跳转

#### 2.1.3 事件绑定体系

`App.init()` 中集中绑定所有事件，按功能模块分组：

```javascript
_initWelcomeParticles(); _bindWelcomeBtn();
_bindNavEvents(); _bindUploadEvents(); _bindCleaningEvents();
_bindAnalysisEvents(); _bindVisualizationEvents(); _bindExportEvents();
_bindAIEvents(); _bindDashboardEvents(); _bindModalEvents();
```

这种集中初始化模式便于维护和调试。

#### 2.1.4 各视图面板交互逻辑

**Dashboard 仪表盘**：4 张统计卡片（总数/待处理/已完成/进行中）动态更新；最近项目列表支持复选框多选、双击预览全量数据。

**清洗视图**：配置面板（缺失值处理方法选择、重复行开关、异常值检测方法），选择 IQR/Z-Score 时自动显示对应帮助文本；结果面板展示清洗前后对比。

**分析视图**：6 张分析模式卡片（统计/相关/分组/聚类/回归/异常），点击后展开参数面板和结果面板。"返回"按钮可回到模式选择。

**可视化视图**：图表配置面板（图表类型、X/Y 轴列选择、标题输入、数据标签/合并相同 X/标签旋转开关、轴定义域编辑） + 图表预览画面 + 数据 CRUD 表格。

**AI 助手视图**：聊天界面，消息气泡展示，支持 Enter 键发送。

### 2.2 API 客户端 (api.js)

封装了全部后端接口的 HTTP 调用，关键设计：

```javascript
const API = {
    // 基础请求方法
    async _fetch(method, url, body) {
        const headers = { 'Content-Type': 'application/json' };
        // 自动注入 Auth Token
        if (window.Auth && window.Auth.state.token) {
            headers['Authorization'] = `Bearer ${window.Auth.state.token}`;
        }
        const res = await fetch(url, { method, headers, body: JSON.stringify(body) });
        if (!res.ok) { /* 统一错误处理 */ }
        return res.json();
    },

    // 文件上传专用（XHR + 进度事件）
    uploadFile(file, onProgress) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.upload.addEventListener('progress', e => {
                if (onProgress) onProgress(e.loaded / e.total);
            });
            // ...
        });
    },
};
```

支持的方法：`uploadFile`、`getAllData`、`cleanData`、`runAnalysis`（6 种分析类型）、`generateChart`、`exportData`/`exportReport`、`askAI`、数据 CRUD（cell/row/column）、认证（register/login/recover/check/me/update/logout）、管理员（list/delete/reset/toggle）。

### 2.3 数据可视化系统

#### 2.3.1 后端可视化服务 (visualization_service.py)

**10 种图表生成器**（后端完整支持，前端 `<select>` 当前开放其中 4 种：柱状图/折线图/饼图/面积图）：

| 图表类型 | 生成方法 | 适用场景 |
|---------|---------|---------|
| 折线图 (line) | `_generate_line_chart` | 时间序列趋势 |
| 柱状图 (bar) | `_generate_bar_chart` | 分类对比 |
| 饼图 (pie) | `_generate_pie_chart` | 占比分布 |
| 散点图 (scatter) | `_generate_scatter_chart` | 双变量关系 |
| 箱线图 (box) | `_generate_box_chart` | 分布与异常值 |
| 热力图 (heatmap) | `_generate_heatmap_chart` | 相关性矩阵 |
| 雷达图 (radar) | `_generate_radar_chart` | 多维对比 |
| 直方图 (histogram) | `_generate_histogram_chart` | 频率分布 |
| 面积图 (area) | `_generate_area_chart` | 趋势+量级 |
| 漏斗图 (funnel) | `_generate_funnel_chart` | 转化率/递减 |

**统一霓虹主题**：`_apply_common_theme()` 为所有图表应用统一风格——透明暗色背景、半透明 tooltip、霓虹色彩方案（12 色）：

```python
COLORS = [
    "#6366f1", "#8b5cf6", "#ec4899", "#38bdf8",
    "#10b981", "#f59e0b", "#ef4444", "#06b6d4",
    "#f97316", "#84cc16", "#14b8a6", "#a855f7",
]
```

**图表推荐引擎** (`recommend_charts`)：分析数据的列特征（是否有日期列、数值列数量 vs 分类列数量）自动推荐最适合的图表类型并给出优先级。

#### 2.3.2 前端图表引擎 (charts.js)

**智能双 Y 轴**：自动检测多个 Y 系列的值范围差异。当某系列的值范围是其他系列的 8 倍以上时，自动为其分配右侧 Y 轴，避免小量级数据被压缩成一条直线。

**合并相同 X 轴数据**：当 X 轴出现重复值时（如同一日期有多条记录），自动将重复项的数据值累加，确保图表中每个分类/时间点只有一个数据点。

**交互式图表编辑**（本模块最大亮点）：
- **数据点点击编辑**：点击图表中的柱状/折线数据点 → 弹出输入框 → 修改值后图表即时更新 → 同步到下方数据表格
- **标题/图例双击编辑**：双击图表标题或图例 → 出现样式编辑面板 → 可修改文字、颜色、字体大小、水平位置
- **轴定义域编辑**：在配置面板设置 X/Y 轴的最小/最大值，支持局部放大查看
- **长按拖拽重定位**：长按标题、图例、dataZoom 滑块 → 拖拽到任意位置放手 → 组件在新位置渲染
- **每列颜色自定义**：Y 轴多选时，每一列旁边显示颜色圆点，点击可弹出颜色选择器

**PNG 导出**：使用 ECharts 的 `getDataURL()` 方法，将图表导出为高分辨率 PNG 图片供下载。

### 2.4 用户认证系统

#### 2.4.1 后端认证服务 (auth_service.py)

**密码安全**：使用行业标准的 **PBKDF2-HMAC-SHA256** 进行密码哈希，迭代次数 100,000 次，每个用户 32 字节随机盐值：

```python
def _hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(32)       # 64字符随机盐
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"),
        salt.encode("utf-8"), iterations=100_000
    )
    return dk.hex(), salt
```

**会话管理**：
- 普通登录：令牌有效期 30 天
- "记住我"：令牌有效期 365 天
- 令牌使用 `secrets.token_urlsafe(48)` 生成，64 字符随机字符串
- 每次请求通过 `Authorization: Bearer <token>` 头验证

**管理员系统**：
- 首个注册用户自动成为管理员
- 可通过 `ADMIN_USERNAME` 环境变量指定管理员
- 管理员功能：查看所有用户列表、删除用户（不能删除自己和唯一管理员）、重置用户密码、切换管理员权限

#### 2.4.2 前端认证模块 (auth.js)

**Token 持久化与自动恢复**：

```javascript
// 登录时将 token + 过期时间存入 localStorage
_saveToken(token, rememberDays) { ... }

// 页面加载时自动检查并恢复登录状态
async _checkAndRestore() {
    const result = await API.authCheck();
    if (result.logged_in) {
        this.state.loggedIn = true;
        this.state.user = result.user;
        this._renderAll();
    }
}
```

**认证模态框**：3 个 Tab（登录 / 注册 / 密码找回），包含表单验证（用户名 2-50 字符、密码 6-100 字符、确认密码一致性）。

**头像上传裁剪 UI**：
1. 用户选择图片文件（支持 PNG/JPG/GIF/WebP，最大 2MB）
2. 图片显示在裁剪区域，带有圆形裁剪蒙版
3. 点击/拖拽定位裁剪位置，滑块调节缩放比例
4. 点击"确认上传"，FormData 发送到 `/api/auth/avatar`
5. 后端 PIL 处理：自动裁剪为正方形（取中心）、缩放到 200×200、保存为 PNG
6. 刷新页面各处头像显示

**欢迎页集成**：
- 未登录：右上角显示"登录"/"注册"按钮
- 已登录：右上角显示用户头像，点击展开下拉菜单（设置 / 管理员面板（仅管理员可见）/ 退出登录）

**管理员面板**：用户列表表格、重置密码按钮（显示新密码弹窗）、切换管理员开关、删除用户按钮（带确认对话框和安全检查）。

### 2.5 UI/UX 设计系统

#### 2.5.1 玻璃拟态风格 (glassmorphism.css)

核心效果通过 CSS 实现：

```css
.glass-card {
    background: rgba(20, 20, 40, 0.6);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
}
/* 顶部光晕 */
.glass-card::before {
    background: radial-gradient(ellipse at top, rgba(99, 102, 241, 0.15), transparent 70%);
}
/* 角落高光 */
.glass-card::after {
    background: linear-gradient(135deg, rgba(255,255,255,0.06), transparent 40%);
}
```

4 种颜色变体：`.glass-card`（默认）、`.glass-card-dark`、`.glass-card-neon`（紫色发光）、`.glass-card-pink`、`.glass-card-cyan`，各有独特的 hover 悬浮和 glow 效果。

#### 2.5.2 动画系统 (animations.css)

15+ 关键帧动画：`fadeInUp`、`fadeInRight`、`fadeIn`、`fadeOut`、`float`、`pulse`、`spin`、`shine`（进度条）、`neonBlink`、`scaleIn`、`skeleton`（加载骨架屏）、`ripple`、`typingCursor`、`rowSlideIn`、`borderGlow`（色相旋转边框）、`toastIn/Out`、`modalIn`。

#### 2.5.3 Canvas 粒子背景 (particles.js)

```javascript
const ParticleBackground = {
    init() {
        // 创建 80 个粒子
        // 每个粒子有随机位置、速度、颜色（从5色霓虹色板中选）
        // requestAnimationFrame 驱动动画循环
        // 距离 < 150px 的粒子之间绘制半透明连线
        // 窗口 resize 时重建 Canvas
    }
};
```

#### 2.5.4 响应式设计

两个断点：`@media (max-width: 1200px)` 平板优化，`@media (max-width: 768px)` 手机优化。调整内容包括：侧边栏折叠、卡片列数减少、字体缩小、表格横向滚动。

### 2.6 可视化 API 接口设计

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/visualization/generate` | POST | 生成 ECharts 图表配置并保存到数据库 |
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/logout` | POST | 退出登录 |
| `/api/auth/recover` | POST | 密码找回 |
| `/api/auth/me` | GET | 获取当前用户信息 |
| `/api/auth/me` | PUT | 更新用户信息 |
| `/api/auth/check` | GET | 检查登录状态 |
| `/api/auth/avatar` | POST | 上传头像（自动裁剪） |
| `/api/auth/admin/users` | GET | 管理员获取用户列表 |
| `/api/auth/admin/users/{id}` | DELETE | 管理员删除用户 |
| `/api/auth/admin/users/{id}/reset-password` | POST | 管理员重置密码 |
| `/api/auth/admin/users/{id}/toggle-admin` | POST | 管理员切换权限 |

---

## 3 系统运行展示（侧重个人部分）

### 3.1 欢迎页 — 粒子动画与认证入口

用户访问 `http://localhost:8000` 首先看到欢迎页。Canvas 画布渲染 100 个随机霓虹色粒子，粒子之间距离 < 120px 时绘制半透明连线。右上角显示"登录"/"注册"按钮（未登录时）或用户头像下拉菜单（已登录时）。

（此处插入截图：欢迎页整体效果，展示粒子动画和霓虹标题）

### 3.2 登录/注册模态框

点击"登录"弹出模态框，包含 3 个 Tab：登录、注册、密码找回。登录支持"记住我"（365 天免登录）。注册需输入用户名、密码和确认密码。

（此处插入截图：登录模态框 + 注册表单 + 密码找回）

### 3.3 Dashboard 仪表盘

进入主应用后展示 Dashboard。4 张霓虹统计卡片（数据集总数、待处理、已完成、进行中），4 个快速操作按钮。最近项目列表展示已上传文件，每行有进度指示器（5 个圆点对应 5 步流程），支持复选框多选。

（此处插入截图：Dashboard 主界面，展示多文件列表和进度指示器）

### 3.4 可视化 — 图表生成与交互

选择柱状图，X 轴为"地区"，Y 轴为"销售额"和"利润"。系统自动生成双 Y 轴柱状图（两列数值范围差异大时自动分离 Y 轴）。

（此处插入截图：柱状图生成效果，展示双 Y 轴 + 霓虹配色）

**交互演示**：
- 点击数据点 → 弹出编辑输入框 → 修改值 → 图表即时更新
- 双击标题"销售额分析" → 弹出样式编辑器 → 修改为红色、18px、右对齐
- 长按图例 → 拖拽到图表右上角

（此处插入截图序列：数据点编辑 / 标题样式编辑 / 图例拖拽）

### 3.5 可视化 — 数据表格 CRUD

图表下方展示完整数据表格，支持：双击单元格编辑、双击列头重命名、添加行、删除行（最后一列"删除"按钮）、添加列、筛选、批量保存。

（此处插入截图：数据表格编辑状态，展示正在修改的单元格和列重命名输入框）

### 3.6 用户设置 — 头像上传裁剪

在设置面板中上传头像。选择图片后，展示圆形裁剪预览区域，可拖拽定位和缩放。上传后后端自动裁剪为 200×200 正方形 PNG，刷新顶部导航栏和欢迎页的头像显示。

（此处插入截图：头像裁剪界面序列——原图选择 → 裁剪调整 → 上传后头像展示）

### 3.7 管理员面板

管理员在用户头像下拉菜单中看到"管理员面板"入口。面板展示所有注册用户列表，包含用户名、邮箱、角色、注册时间。可操作：重置某用户密码（显示新密码弹窗）、切换管理员权限、删除用户。

（此处插入截图：管理员面板，展示用户列表和管理操作按钮）

### 3.8 响应式适配

在手机/平板视口下，侧边栏自动折叠，统计卡片从 4 列变为 2 列，表格可横向滚动，字体适配缩小。

（此处插入截图：手机端 Dashboard 视图 + 可视化视图）

---

## 4 个人遇到的问题与解决方法

### 问题 1：ECharts 实例在视图切换时的残留与内存泄漏

**问题描述**：SPA 架构下，用户在可视化视图生成图表后切换到其他视图再切回来，如果不处理 ECharts 实例，会出现图表重复渲染、事件监听器累积、内存泄漏等问题。

**解决方法**：在 `Charts` 模块中实现实例生命周期管理：

```javascript
// 渲染前先销毁旧实例
render(domId, option) {
    if (this._instance) {
        this._instance.dispose();
        this._instance = null;
    }
    const dom = document.getElementById(domId);
    this._instance = echarts.init(dom);
    this._instance.setOption(option);
}

// 视图切换时清理
destroy() {
    if (this._instance) {
        this._instance.dispose();
        this._instance = null;
    }
}
```

在 `App.switchView()` 中，离开可视化视图时调用 `Charts.destroy()`。

### 问题 2：图表数据点编辑时不同步到数据表格

**问题描述**：用户点击图表中的数据点修改值后，图表即时更新了（因为直接修改了 ECharts 的 option），但下方的数据表格和缓存中的原始数据没有同步更新。当用户刷新或重新生成图表时，修改丢失。

**解决方法**：建立"图表 → 表格 → 缓存"双向数据绑定：

1. 图表数据点编辑 → 更新 `Charts._currentOption` → `setOption` 重绘
2. 同时触发 `App` 的编辑回调 → 更新 `App.state.editedData`
3. 重新渲染数据表格 → 用户看到修改后的值
4. 点击"保存修改" → 调用 `/api/data/batch` 持久化到磁盘

```javascript
// charts.js 中
_onDataPointClick(params) {
    // 弹出编辑输入框
    const newVal = prompt('修改值:', params.value);
    if (newVal !== null) {
        // 更新图表
        option.series[params.seriesIndex].data[params.dataIndex] = Number(newVal);
        this._instance.setOption(option);
        // 回调通知主控制器更新数据
        if (this._editCallback) {
            this._editCallback(params.seriesIndex, params.dataIndex, Number(newVal));
        }
    }
}
```

### 问题 3：多系列数据 Y 轴范围差异过大导致可视化失真

**问题描述**：当同一图表中展示两个量级差异很大的数据系列时（例如"销量"范围 1-100 vs "销售额"范围 1000-100000），共用同一个 Y 轴会导致小量级数据被压缩成几乎不可见的直线。

**解决方法**：实现了智能双 Y 轴判定算法：

```javascript
_needDualAxis(seriesData) {
    if (seriesData.length < 2) return false;
    // 计算每个系列的值范围
    const ranges = seriesData.map(s => {
        const vals = (s.data || []).filter(v => v !== null && !isNaN(v));
        return Math.max(...vals) - Math.min(...vals);
    });
    // 范围差异超过 8 倍 → 启用双 Y 轴
    const maxR = Math.max(...ranges, 1e-10);
    const minR = Math.min(...ranges.filter(r => r > 0), maxR);
    return (maxR / Math.max(minR, 1e-10)) > 8;
}
```

阈值 8 是经过实际测试的经验值——太小会导致不必要的双轴（增加视觉复杂度），太大则会让部分数据失真。

### 问题 4：头像裁剪 UI 的拖拽定位计算

**问题描述**：头像裁剪功能需要在限制区域内拖拽图片定位，同时配合缩放滑块。涉及 `mousedown/mousemove/mouseup` 事件处理和坐标转换，边界条件（图片不能拖出裁剪框）容易出错。

**解决方法**：
1. 使用 CSS `transform: translate(tx, ty) scale(s)` 控制图片位置和缩放
2. 在 `mousedown` 时记录起始坐标和初始偏移
3. 在 `mousemove` 时计算增量并更新，同时校验边界（`Math.min/Math.max` 钳制）
4. 在 `mouseup` 时解除事件绑定
5. 将最终 `(tx, ty, scale)` 值发送给后端，供 PIL 进行精确裁剪

后端接收后使用 PIL 完成真正的裁剪：居中正方形裁剪 → 缩放至 200×200 → 保存为 PNG。

### 问题 5：localStorage Token 跨标签页同步

**问题描述**：用户在一个标签页登录后，另一个标签页中打开的应用不会感知到登录状态变化，需要手动刷新。

**解决方法**：监听 `storage` 事件，当 token 被其他标签页清除或更新时，自动同步状态：

```javascript
window.addEventListener('storage', (e) => {
    if (e.key === 'da_auth') {
        if (e.newValue) {
            // 其他标签页登录了，尝试恢复
            const data = JSON.parse(e.newValue);
            this.state.token = data.token;
            this._checkAndRestore();
        } else {
            // 其他标签页登出了
            this.state.loggedIn = false;
            this.state.user = null;
            this._renderAll();
        }
    }
});
```

---

## 5 个人收获与改进建议

### 5.1 个人收获

#### 5.1.1 复杂 SPA 状态管理的实践

`main.js` 超过 1,100 行，管理着文件列表、多选状态、视图状态、图表实例、编辑数据等多个维度的状态。在没有使用 React/Vue 框架的情况下，我深刻体会到：
- **集中状态优于分散状态**：所有状态集中在 `App.state` 对象中，便于调试和理解数据流
- **单向数据流**：用户操作 → 更新 state → 重新渲染 UI，避免 UI 和 state 的双向绑定混乱
- **事件委托**：利用冒泡机制在父元素绑定事件，减少事件监听器数量

#### 5.1.2 ECharts 深度定制经验

ECharts 虽然提供了丰富的配置项，但实现"霓虹玻璃拟态"的统一视觉风格仍然需要大量定制：
- 所有 tooltip 使用半透明暗色背景 + 紫色边框
- 坐标轴使用低透明度白色，网格线几乎不可见
- 12 色霓虹色板经过多次迭代调整，确保相邻色系对比度足够
- 图表背景设为 `transparent`，让 CSS 的玻璃拟态卡片背景透出

#### 5.1.3 认证安全实践的完整实现

从前端到后端实现了完整的认证链路：
- **密码安全**：PBKDF2-HMAC-SHA256（10 万次迭代）+ 32 字节随机盐
- **会话安全**：64 字符随机令牌 + 过期时间 + 服务端验证
- **前端安全**：Token 存储在 localStorage + 每个请求 Bearer 头注入 + 页面加载自动验证
- **管理员安全**：不能删除自己、不能取消唯一管理员权限

#### 5.1.4 CSS 艺术效果工程化

玻璃拟态不是简单的 `backdrop-filter: blur()`，而是一个多层叠加的系统：
- `backdrop-filter: blur(12px)` — 背景模糊
- `::before` 伪元素 — 顶部径向渐变光晕
- `::after` 伪元素 — 左上角线性渐变高光
- `border: 1px solid rgba(255,255,255,0.08)` — 微弱边框
- hover 时 elevation 提升（`translateY(-2px)` + `box-shadow` 增强）

### 5.2 改进建议

#### 5.2.1 前端架构方面

1. **引入前端框架**：当前原生 JS 的 DOM 操作代码量很大（main.js 1,100+ 行）。建议迁移到 Vue 3（轻量、渐进式），使用其响应式数据绑定和组件化能力大幅减少 DOM 操作代码。

2. **组件化拆分**：将 main.js 拆分为独立的视图组件（DashboardView、CleaningView、AnalysisView、VisualizationView、AIView），每个组件管理自己的状态和渲染逻辑。

3. **前端路由**：当前通过 `switchView()` + CSS `display` 切换视图。建议引入简单的 hash 路由（如 `#/dashboard`、`#/visualization`），支持浏览器前进/后退按钮。

#### 5.2.2 可视化方面

1. **增加更多图表类型**：目前前端暴露了 4 种（柱状图/折线图/饼图/面积图），后端支持 10 种。可以将散点图、箱线图、热力图、雷达图也开放到前端。

2. **图表模板保存**：用户精心调整的图表配置（颜色、标题样式、轴域）可以保存为模板，下次上传类似数据时一键应用。

3. **图表动画增强**：利用 ECharts 的 `animationEasing` 和 `animationDuration` 为不同图表类型设置差异化的入场动画。

#### 5.2.3 用户系统方面

1. **OAuth 第三方登录**：增加 GitHub/Google OAuth 登录支持，降低注册门槛。

2. **邮箱验证**：注册时发送验证邮件，确保邮箱真实有效，也支持通过邮箱找回密码。

3. **操作审计日志**：记录管理员的关键操作（删除用户、重置密码、切换权限），便于追溯。

#### 5.2.4 UI/UX 方面

1. **深色/浅色主题切换**：当前只有深色霓虹主题。增加浅色主题选项，并持久化到 localStorage。

2. **键盘快捷键**：为常用操作添加快捷键（如 `Ctrl+U` 上传、`Ctrl+S` 保存、`Ctrl+E` 导出）。

3. **引导教程**：首次使用时显示逐步引导 overlay，帮助新用户快速了解系统功能。

---

*报告完成日期：2026 年 6 月 4 日*
