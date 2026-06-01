/**
 * DataVision Pro - 主控模块
 * 仪表盘中心架构：左侧纯导航 + 右侧视图切换
 */
const App = {
    state: {
        currentFileId: null,
        fileName: null,
        columns: [],
        numericColumns: [],
        currentView: 'dashboard',
        currentStep: 'upload',
        dataLoaded: false,
        cleanedFileId: null,
        currentChart: null,
    },

    /* ========== 初始化 ========== */
    init() {
        console.log('DataVision Pro 初始化...');
        this._bindNavEvents();
        this._bindUploadEvents();
        this._bindCleaningEvents();
        this._bindAnalysisEvents();
        this._bindVisualizationEvents();
        this._bindExportEvents();
        this._bindAIEvents();
        this._bindGlobalEvents();
        this._initParticles();
        this._checkServerHealth();
    },

    /* ========== 导航 & 视图切换 ========== */
    _bindNavEvents() {
        // 左侧导航
        document.querySelectorAll('.nav-item[data-view]').forEach(item => {
            item.addEventListener('click', () => {
                const view = item.dataset.view;
                this.switchView(view);
            });
        });

        // 步骤进度条
        document.querySelectorAll('.stepper-step').forEach(step => {
            step.addEventListener('click', () => {
                const stepName = step.dataset.step;
                const viewMap = { upload:'upload', cleaning:'cleaning', analysis:'analysis', visualization:'visualization', export:'export' };
                if (viewMap[stepName]) this.switchView(viewMap[stepName]);
            });
        });

        // 仪表盘快捷操作按钮
        document.querySelectorAll('.dash-action-btn[data-nav]').forEach(btn => {
            btn.addEventListener('click', () => this.switchView(btn.dataset.nav));
        });
    },

    /** 切换视图 */
    switchView(viewName) {
        // 更新导航高亮
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        const navItem = document.querySelector(`.nav-item[data-view="${viewName}"]`);
        if (navItem) navItem.classList.add('active');

        // 切换视图
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        const target = document.getElementById(`view-${viewName}`);
        if (target) target.classList.add('active');

        this.state.currentView = viewName;
        this._updateStepper(viewName);
    },

    /** 更新步骤进度条 */
    _updateStepper(viewName) {
        const stepMap = { dashboard:null, upload:'upload', cleaning:'cleaning', analysis:'analysis', visualization:'visualization', export:'export', 'ai-assistant':null };
        const currentStep = stepMap[viewName];
        if (!currentStep) return;

        const steps = document.querySelectorAll('.stepper-step');
        let found = false;
        steps.forEach(step => {
            step.classList.remove('active', 'done');
            if (step.dataset.step === currentStep) { step.classList.add('active'); found = true; }
            else if (!found) { step.classList.add('done'); }
        });
        this.state.currentStep = currentStep;
    },

    /* ========== 文件上传 ========== */
    _bindUploadEvents() {
        const dropzone = document.getElementById('uploadDropzone');
        const fileInput = document.getElementById('fileInput');
        const btnSelect = document.getElementById('btnSelectFile');

        btnSelect.addEventListener('click', () => fileInput.click());

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) this._handleFileUpload(e.target.files[0]);
        });

        // 拖拽上传
        dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('drag-over'); });
        dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-over'));
        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.classList.remove('drag-over');
            if (e.dataTransfer.files.length > 0) this._handleFileUpload(e.dataTransfer.files[0]);
        });
    },

    async _handleFileUpload(file) {
        // 验证文件
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        if (!['.csv', '.xlsx', '.xls'].includes(ext)) {
            Utils.toast('不支持的文件格式，请上传 CSV 或 Excel 文件', 'error');
            return;
        }
        if (file.size > 10 * 1024 * 1024) {
            Utils.toast('文件大小超过 10MB 限制', 'error');
            return;
        }

        this._showLoading('上传中...');
        const progDiv = document.getElementById('uploadProgress');
        const progFill = document.getElementById('progressFill');
        const progText = document.getElementById('progressText');
        progDiv.style.display = 'block';

        try {
            const result = await API.uploadFile(file, (pct) => {
                progFill.style.width = pct + '%';
                progText.textContent = `上传中 ${pct}%...`;
            });

            this.state.currentFileId = result.file_id;
            this.state.fileName = result.file_name;
            this.state.columns = result.columns || [];
            this.state.numericColumns = result.numeric_columns || [];
            this.state.dataLoaded = true;

            progFill.style.width = '100%';
            progText.textContent = '上传完成';
            Utils.toast('文件上传成功', 'success');

            // 显示文件预览
            this._showFilePreview(result);
            // 更新仪表盘
            this._updateDashboard(result);
            // 更新步骤
            this._updateStepper('upload');

            // 1.5 秒后隐藏进度条
            setTimeout(() => { progDiv.style.display = 'none'; progFill.style.width = '0%'; }, 1500);

        } catch (err) {
            Utils.toast('上传失败: ' + err.message, 'error');
        } finally {
            this._hideLoading();
        }
    },

    _showFilePreview(result) {
        const preview = document.getElementById('filePreview');
        preview.style.display = 'block';

        document.getElementById('previewFileName').textContent = result.file_name;
        document.getElementById('fileInfoTags').innerHTML = `
            <span class="file-info-tag">${result.row_count || '?'} 行</span>
            <span class="file-info-tag">${result.column_count || '?'} 列</span>
            <span class="file-info-tag">${Utils.formatFileSize(result.file_size || 0)}</span>
        `;

        // 渲染数据表
        if (result.preview_data && result.preview_data.length > 0) {
            const cols = Object.keys(result.preview_data[0]);
            const thead = '<tr>' + cols.map(c => `<th>${c}</th>`).join('') + '</tr>';
            const tbody = result.preview_data.slice(0, 20).map(row =>
                '<tr>' + cols.map(c => `<td>${row[c] !== null && row[c] !== undefined ? String(row[c]).slice(0, 50) : ''}</td>`).join('') + '</tr>'
            ).join('');
            document.getElementById('uploadDataTable').innerHTML = thead + tbody;
        }
    },

    _updateDashboard(result) {
        document.getElementById('dashRowCount').textContent = result.row_count || '--';
        document.getElementById('dashColCount').textContent = result.column_count || '--';
        document.getElementById('dashMissing').textContent = result.missing_count || '0';
        document.getElementById('dashOutliers').textContent = '--';

        // 添加到最近项目
        const recentList = document.getElementById('recentList');
        const now = new Date();
        const timeStr = `${now.getMonth()+1}/${now.getDate()} ${now.getHours()}:${String(now.getMinutes()).padStart(2,'0')}`;
        const item = document.createElement('div');
        item.className = 'recent-item';
        item.innerHTML = `<span class="recent-item-name">${result.file_name}</span><span class="recent-item-time">${timeStr}</span>`;
        item.addEventListener('click', () => this.switchView('upload'));
        if (recentList.querySelector('.empty-state-sm')) recentList.innerHTML = '';
        recentList.prepend(item);
    },

    /* ========== 数据清洗 ========== */
    _bindCleaningEvents() {
        document.getElementById('btnClean').addEventListener('click', () => this._handleCleaning());
    },

    async _handleCleaning() {
        if (!this.state.currentFileId) {
            Utils.toast('请先上传数据文件', 'warning');
            this.switchView('upload');
            return;
        }

        const params = {
            file_id: this.state.currentFileId,
            missing_method: document.getElementById('missingMethod').value,
            drop_duplicates: document.getElementById('dropDuplicates').checked,
            outlier_method: document.getElementById('outlierMethod').value,
        };

        this._showLoading('清洗中...');
        try {
            const result = await API.cleanData(params);
            this.state.cleanedFileId = result.cleaned_file_id || result.file_id;

            // 显示清洗对比
            document.getElementById('cleanEmpty').style.display = 'none';
            document.getElementById('cleanCompare').style.display = 'flex';
            document.getElementById('cleanOrigRows').textContent = result.original_shape?.[0] || '--';
            document.getElementById('cleanOrigMissing').textContent = result.original_missing || '--';
            document.getElementById('cleanOrigDup').textContent = result.original_duplicates || '--';
            document.getElementById('cleanNewRows').textContent = result.cleaned_shape?.[0] || '--';
            document.getElementById('cleanNewMissing').textContent = result.cleaned_missing || '--';
            document.getElementById('cleanNewDup').textContent = result.cleaned_duplicates || '--';

            // 更新仪表盘缺失值
            document.getElementById('dashMissing').textContent = result.cleaned_missing || '0';

            Utils.toast('数据清洗完成', 'success');
            this._updateStepper('cleaning');
        } catch (err) {
            Utils.toast('清洗失败: ' + err.message, 'error');
        } finally {
            this._hideLoading();
        }
    },

    /* ========== 数据分析 ========== */
    _bindAnalysisEvents() {
        document.querySelectorAll('.analysis-card').forEach(card => {
            card.addEventListener('click', () => this._handleAnalysis(card.dataset.action));
        });
    },

    async _handleAnalysis(action) {
        if (!this.state.currentFileId) {
            Utils.toast('请先上传数据文件', 'warning');
            this.switchView('upload');
            return;
        }

        const fileId = this.state.cleanedFileId || this.state.currentFileId;
        const body = document.getElementById('analysisResultBody');
        const actionNames = { statistics:'描述性统计', correlation:'相关性分析', groupby:'分组聚合', cluster:'K-Means聚类', regression:'线性回归', anomaly:'异常检测' };

        this._showLoading(`正在执行${actionNames[action] || action}...`);
        try {
            const result = await API.runAnalysis(action, fileId);
            this._renderAnalysisResult(action, result, body);
            this._updateStepper('analysis');
        } catch (err) {
            Utils.toast('分析失败: ' + err.message, 'error');
        } finally {
            this._hideLoading();
        }
    },

    _renderAnalysisResult(action, result, body) {
        switch (action) {
            case 'statistics':
                if (result.statistics) {
                    const cols = Object.keys(result.statistics);
                    body.innerHTML = `<div class="table-scroll"><table class="data-table">
                        <thead><tr><th>指标</th>${cols.map(c => `<th>${c}</th>`).join('')}</tr></thead>
                        <tbody>${['count','mean','std','min','25%','50%','75%','max'].map(stat => {
                            return `<tr><td><strong>${stat}</strong></td>${cols.map(c =>
                                `<td>${result.statistics[c][stat] !== undefined ? Number(result.statistics[c][stat]).toFixed(4) : '--'}</td>`
                            ).join('')}</tr>`;
                        }).join('')}</tbody></table></div>`;
                }
                break;
            case 'correlation':
                if (result.correlation_matrix) {
                    const cols = Object.keys(result.correlation_matrix);
                    body.innerHTML = `<div class="table-scroll"><table class="data-table">
                        <thead><tr><th></th>${cols.map(c => `<th>${c}</th>`).join('')}</tr></thead>
                        <tbody>${cols.map(r => `<tr><td><strong>${r}</strong></td>${cols.map(c =>
                            `<td style="color:${Math.abs(result.correlation_matrix[r][c])>0.7?'var(--neon-accent)':'inherit'}">${result.correlation_matrix[r][c].toFixed(3)}</td>`
                        ).join('')}</tr>`).join('')}</tbody></table></div>`;
                }
                break;
            case 'cluster':
                if (result.cluster_result) {
                    body.innerHTML = `<pre style="color:var(--text-secondary);font-size:0.85em;white-space:pre-wrap;">${result.cluster_result}</pre>`;
                }
                break;
            default:
                body.innerHTML = `<pre style="color:var(--text-secondary);font-size:0.85em;white-space:pre-wrap;">${JSON.stringify(result, null, 2)}</pre>`;
        }
    },

    /* ========== 可视化 ========== */
    _bindVisualizationEvents() {
        document.getElementById('chartType').addEventListener('change', () => this._updateColumnSelects());
        document.getElementById('btnGenerateChart').addEventListener('click', () => this._handleVisualization());
        document.getElementById('btnExportPNG').addEventListener('click', () => this._exportChartPNG());
        document.getElementById('btnClearChart').addEventListener('click', () => this._clearChart());
    },

    _updateColumnSelects() {
        const xSelect = document.getElementById('xColumn');
        const ySelect = document.getElementById('yColumn');
        const cols = this.state.columns.length > 0 ? this.state.columns : [];

        [xSelect, ySelect].forEach(sel => {
            sel.innerHTML = cols.map(c => `<option value="${c}">${c}</option>`).join('');
        });
    },

    async _handleVisualization() {
        if (!this.state.currentFileId) {
            Utils.toast('请先上传数据文件', 'warning');
            this.switchView('upload');
            return;
        }

        const fileId = this.state.cleanedFileId || this.state.currentFileId;
        const chartType = document.getElementById('chartType').value;
        const xCol = document.getElementById('xColumn').value;
        const ySelect = document.getElementById('yColumn');
        const yCols = Array.from(ySelect.selectedOptions).map(o => o.value);
        const title = document.getElementById('chartTitle').value || chartType;

        if (!xCol) { Utils.toast('请选择 X 轴列', 'warning'); return; }
        if (yCols.length === 0) { Utils.toast('请选择至少一列 Y 轴', 'warning'); return; }

        this._showLoading('生成图表中...');
        try {
            const result = await API.generateChart(fileId, { chart_type: chartType, x_column: xCol, y_columns: yCols, title: title });
            document.getElementById('chartActions').style.display = 'flex';
            document.getElementById('chartStage').innerHTML = '';
            Charts.renderChart('chartStage', result);
            this.state.currentChart = result;
            this._updateStepper('visualization');
        } catch (err) {
            Utils.toast('图表生成失败: ' + err.message, 'error');
        } finally {
            this._hideLoading();
        }
    },

    _exportChartPNG() {
        if (!this.state.currentChart) { Utils.toast('没有可导出的图表', 'warning'); return; }
        const chartDom = document.getElementById('chartStage').querySelector('[echarts-instance]') || document.getElementById('chartStage').firstElementChild;
        if (chartDom) {
            const instance = echarts.getInstanceByDom(chartDom);
            if (instance) {
                const url = instance.getDataURL({ type:'png', pixelRatio:2, backgroundColor:'#1a1645' });
                Utils.downloadFile(url, 'chart.png');
                Utils.toast('图表已导出', 'success');
            }
        }
    },

    _clearChart() {
        const stage = document.getElementById('chartStage');
        const chartDom = stage.querySelector('[echarts-instance]') || stage.firstElementChild;
        if (chartDom) {
            const instance = echarts.getInstanceByDom(chartDom);
            if (instance) instance.dispose();
        }
        stage.innerHTML = '<div class="empty-state-sm">配置参数后点击"生成图表"</div>';
        document.getElementById('chartActions').style.display = 'none';
        this.state.currentChart = null;
    },

    /* ========== 导出 ========== */
    _bindExportEvents() {
        document.querySelectorAll('.export-card').forEach(card => {
            card.querySelector('button').addEventListener('click', (e) => {
                e.stopPropagation();
                this._handleExport(card.dataset.export);
            });
        });
    },

    async _handleExport(type) {
        if (!this.state.currentFileId) {
            Utils.toast('请先上传数据文件', 'warning');
            return;
        }

        const fileId = this.state.cleanedFileId || this.state.currentFileId;
        this._showLoading('导出中...');
        try {
            switch (type) {
                case 'data': await API.exportData(fileId); break;
                case 'chart': this._exportChartPNG(); break;
                case 'report': await API.exportReport(fileId); break;
            }
            Utils.toast('导出成功', 'success');
            this._updateStepper('export');
        } catch (err) {
            Utils.toast('导出失败: ' + err.message, 'error');
        } finally {
            this._hideLoading();
        }
    },

    /* ========== AI 助手 ========== */
    _bindAIEvents() {
        document.getElementById('btnAISend').addEventListener('click', () => this._sendAIMessage());
        document.getElementById('aiInput').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') this._sendAIMessage();
        });
    },

    async _sendAIMessage() {
        const input = document.getElementById('aiInput');
        const msg = input.value.trim();
        if (!msg) return;

        // 添加用户消息
        this._addAIMessage('user', msg);
        input.value = '';

        try {
            const fileId = this.state.cleanedFileId || this.state.currentFileId;
            const result = await API.askAI(msg, fileId);
            if (result.reply) {
                this._addAIMessage('bot', result.reply);
            }
            if (result.chart_data) {
                this.state.currentChart = result.chart_data;
                this.switchView('visualization');
                setTimeout(() => {
                    document.getElementById('chartStage').innerHTML = '';
                    Charts.renderChart('chartStage', result.chart_data);
                    document.getElementById('chartActions').style.display = 'flex';
                }, 400);
            }
        } catch (err) {
            this._addAIMessage('bot', '抱歉，处理请求时出错了: ' + err.message);
        }
    },

    _addAIMessage(role, text) {
        const area = document.getElementById('aiChatArea');
        const div = document.createElement('div');
        div.className = `ai-msg ${role}`;
        div.innerHTML = `
            <div class="ai-avatar">${role === 'user' ? 'You' : 'AI'}</div>
            <div class="ai-bubble"><p>${text.replace(/\n/g, '<br>')}</p></div>
        `;
        area.appendChild(div);
        area.scrollTop = area.scrollHeight;
    },

    /* ========== 全局事件 ========== */
    _bindGlobalEvents() {
        document.getElementById('btnTheme').addEventListener('click', () => {
            document.body.classList.toggle('theme-light');
            Utils.toast('主题已切换', 'info');
        });
        document.getElementById('btnHelp').addEventListener('click', () => {
            Utils.toast('DataVision Pro — 交互式数据分析系统 v1.0', 'info');
        });
    },

    /* ========== 工具方法 ========== */
    _showLoading(text) {
        document.getElementById('loadingOverlay').style.display = 'flex';
        document.getElementById('loadingText').textContent = text || '处理中...';
    },
    _hideLoading() {
        document.getElementById('loadingOverlay').style.display = 'none';
    },

    async _checkServerHealth() {
        try {
            const res = await API.healthCheck();
            console.log('服务器状态:', res);
        } catch (e) {
            console.warn('服务器连接失败:', e.message);
        }
    },

    _initParticles() {
        if (typeof Particles !== 'undefined') {
            Particles.init();
        }
    },
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => App.init());
