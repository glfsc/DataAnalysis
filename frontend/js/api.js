/**
 * DataVision Pro - API 调用模块
 */
const API = {
    BASE_URL: '/api',

    async request(endpoint, options = {}) {
        const url = `${this.BASE_URL}${endpoint}`;
        const config = { headers: { 'Accept': 'application/json' }, ...options };
        // 自动附加认证令牌
        if (window.Auth && window.Auth.getToken()) {
            config.headers['Authorization'] = `Bearer ${window.Auth.getToken()}`;
        }
        if (!(options.body instanceof FormData)) {
            config.headers['Content-Type'] = 'application/json';
            if (options.body && typeof options.body === 'object') config.body = JSON.stringify(options.body);
        } else { delete config.headers['Content-Type']; }
        const response = await fetch(url, config);
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `请求失败 (${response.status})`);
        }
        const contentType = response.headers.get('content-type') || '';
        if (contentType.includes('text/csv') || contentType.includes('text/html')) return response;
        return response.json();
    },

    healthCheck() { return this.request('/health'); },

    /* ----- 上传 ----- */
    async uploadFile(file, onProgress) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', `${this.BASE_URL}/upload`);
            // 附加认证令牌
            if (window.Auth && window.Auth.getToken()) {
                xhr.setRequestHeader('Authorization', `Bearer ${window.Auth.getToken()}`);
            }
            xhr.upload.onprogress = (e) => { if (e.lengthComputable && onProgress) onProgress(Math.round((e.loaded / e.total) * 100)); };
            xhr.onload = () => { if (xhr.status >= 200 && xhr.status < 300) resolve(JSON.parse(xhr.responseText)); else { try { reject(new Error(JSON.parse(xhr.responseText).detail || `上传失败 (${xhr.status})`)); } catch { reject(new Error(`上传失败 (${xhr.status})`)); } } };
            xhr.onerror = () => reject(new Error('网络连接失败'));
            const fd = new FormData(); fd.append('file', file); xhr.send(fd);
        });
    },

    /* ----- 文件管理 ----- */
    deleteFile(fileId) { return this.request(`/upload/${fileId}`, { method: 'DELETE' }); },
    downloadFile(fileId) {
        // 直接触发下载
        const token = window.Auth ? window.Auth.getToken() : '';
        const a = document.createElement('a');
        a.href = `${this.BASE_URL}/upload/${fileId}/download`;
        if (token) a.href += `?token=${encodeURIComponent(token)}`;
        // 使用 fetch 方式下载（需要带 auth header）
        fetch(`${this.BASE_URL}/upload/${fileId}/download`, {
            headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        }).then(r => {
            if (!r.ok) throw new Error('下载失败');
            return r.blob();
        }).then(blob => {
            Utils.downloadFile(URL.createObjectURL(blob), 'data_export.csv');
        }).catch(e => Utils.toast('下载失败: ' + e.message, 'error'));
    },

    /* ----- 全量数据 ----- */
    getAllData(fileId) { return this.request(`/data/${fileId}`); },

    /* ----- 清洗 ----- */
    cleanData(params) { return this.request('/cleaning/clean', { method: 'POST', body: params }); },

    /* ----- 分析 ----- */
    runAnalysis(action, fileId, extraParams = {}) {
        const eps = { statistics:'/analysis/statistics', correlation:'/analysis/correlation', groupby:'/analysis/groupby', cluster:'/analysis/cluster', regression:'/analysis/regression', anomaly:'/analysis/anomaly' };
        const ep = eps[action]; if (!ep) throw new Error(`未知分析类型: ${action}`);
        return this.request(ep, { method: 'POST', body: { file_id: fileId, ...extraParams } });
    },

    /* ----- 可视化 ----- */
    generateChart(fileId, config) { return this.request('/visualization/generate', { method: 'POST', body: { file_id: fileId, ...config } }); },

    /* ----- 导出 ----- */
    async exportData(fileId, editedData = null) {
        const body = { file_id: fileId };
        if (editedData && editedData.rows) {
            body.rows = editedData.rows;
            body.columns = editedData.columns;
        }
        const r = await this.request('/export/data', { method: 'POST', body });
        if (r instanceof Response) { const blob = await r.blob(); Utils.downloadFile(URL.createObjectURL(blob), 'data_export.csv'); }
    },

    /* ----- AI ----- */
    askAI(question, fileId, history) {
        return this.request('/ai/query', { method: 'POST', body: { question, file_id: fileId, history } });
    },

    /** AI 流式对话 — 返回 ReadableStream 用于实时显示 */
    async chatStream(question, fileId, history, onToken, onDone, onError, onModel) {
        const url = `${this.BASE_URL}/ai/chat`;
        const token = window.Auth ? window.Auth.getToken() : '';
        try {
            const resp = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'text/event-stream',
                    'Authorization': token ? `Bearer ${token}` : '',
                },
                body: JSON.stringify({ question, file_id: fileId, history }),
            });

            if (!resp.ok) {
                const err = await resp.json().catch(() => ({ detail: `HTTP ${resp.status}` }));
                if (onError) onError(err.detail || '请求失败');
                return;
            }

            const reader = resp.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });

                // 解析 SSE 事件
                const lines = buffer.split('\n');
                buffer = lines.pop() || ''; // 最后一行可能不完整

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.type === 'model' && onModel) {
                                onModel(data.name);
                            } else if (data.type === 'token' && onToken) {
                                onToken(data.content);
                            } else if (data.type === 'done' && onDone) {
                                onDone();
                            } else if (data.type === 'error' && onError) {
                                onError(data.message);
                            }
                        } catch (e) { /* ignore parse errors */ }
                    }
                }
            }
            // 处理缓冲区中剩余的数据
            if (buffer.startsWith('data: ')) {
                try {
                    const data = JSON.parse(buffer.slice(6));
                    if (data.type === 'done' && onDone) onDone();
                    if (data.type === 'error' && onError) onError(data.message);
                } catch (e) { /* ignore */ }
            }
        } catch (e) {
            if (onError) onError('网络连接失败: ' + e.message);
        }
    },

    /* ----- AI配置 ----- */
    getAIConfigs() { return this.request('/ai-config/list'); },
    createAIConfig(data) { return this.request('/ai-config/create', { method: 'POST', body: data }); },
    updateAIConfig(id, data) { return this.request(`/ai-config/${id}`, { method: 'PUT', body: data }); },
    deleteAIConfig(id) { return this.request(`/ai-config/${id}`, { method: 'DELETE' }); },
    enableAIConfig(id) { return this.request(`/ai-config/${id}/enable`, { method: 'POST' }); },
    disableAIConfig(id) { return this.request(`/ai-config/${id}/disable`, { method: 'POST' }); },
    testAIConfig(id) { return this.request(`/ai-config/${id}/test`, { method: 'POST' }); },

    /* ----- CRUD ----- */
    updateCell(fileId, rowIndex, column, value) { return this.request('/data/cell', { method: 'PUT', body: { file_id: fileId, row_index: rowIndex, column, value } }); },
    addRow(fileId, rowData) { return this.request('/data/row', { method: 'POST', body: { file_id: fileId, row_data: rowData } }); },
    deleteRow(fileId, rowIndex) { return this.request('/data/row', { method: 'DELETE', body: { file_id: fileId, row_index: rowIndex } }); },
    renameColumn(fileId, oldName, newName) { return this.request('/data/column/rename', { method: 'PUT', body: { file_id: fileId, old_name: oldName, new_name: newName } }); },
    deleteColumn(fileId, column) { return this.request('/data/column', { method: 'DELETE', body: { file_id: fileId, column } }); },
    addColumn(fileId, column, default_value = '') { return this.request('/data/column', { method: 'POST', body: { file_id: fileId, column, default_value } }); },

    /* ----- 批量操作 ----- */
    async batchUpdate(fileId, rows) { return this.request('/data/batch', { method: 'PUT', body: { file_id: fileId, rows } }); },

    /* ----- 列表 ----- */
    getUploadList() { return this.request('/upload/list'); },
    getFileInfo(fileId) { return this.request(`/upload/${fileId}/info`); },

    /* ----- 用户认证 ----- */
    authRegister(username, password, password_confirm) {
        return this.request('/auth/register', { method: 'POST', body: { username, password, password_confirm } });
    },
    authLogin(username, password, remember = false) {
        return this.request('/auth/login', { method: 'POST', body: { username, password, remember } });
    },
    authRecover(username, newPassword = null) {
        const body = { username };
        if (newPassword) body.new_password = newPassword;
        return this.request('/auth/recover', { method: 'POST', body });
    },
    authCheck() {
        return this.request('/auth/check');
    },
    authGetMe() {
        return this.request('/auth/me');
    },
    authUpdateMe(data) {
        return this.request('/auth/me', { method: 'PUT', body: data });
    },
    authLogout() {
        return this.request('/auth/logout', { method: 'POST' });
    },

    /* ----- 管理员 ----- */
    adminListUsers() { return this.request('/auth/admin/users'); },
    adminDeleteUser(userId) { return this.request(`/auth/admin/users/${userId}`, { method: 'DELETE' }); },
    adminResetPassword(userId) { return this.request(`/auth/admin/users/${userId}/reset-password`, { method: 'POST' }); },
    adminToggleAdmin(userId) { return this.request(`/auth/admin/users/${userId}/toggle-admin`, { method: 'POST' }); },
};
window.API = API;
