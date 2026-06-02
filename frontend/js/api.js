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
            xhr.upload.onprogress = (e) => { if (e.lengthComputable && onProgress) onProgress(Math.round((e.loaded / e.total) * 100)); };
            xhr.onload = () => { if (xhr.status >= 200 && xhr.status < 300) resolve(JSON.parse(xhr.responseText)); else { try { reject(new Error(JSON.parse(xhr.responseText).detail || `上传失败 (${xhr.status})`)); } catch { reject(new Error(`上传失败 (${xhr.status})`)); } } };
            xhr.onerror = () => reject(new Error('网络连接失败'));
            const fd = new FormData(); fd.append('file', file); xhr.send(fd);
        });
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
    async exportData(fileId) {
        const r = await this.request('/export/data', { method: 'POST', body: { file_id: fileId } });
        if (r instanceof Response) { const blob = await r.blob(); Utils.downloadFile(URL.createObjectURL(blob), 'data_export.csv'); }
    },
    async exportReport(fileId) {
        const r = await this.request('/export/report', { method: 'POST', body: { file_id: fileId } });
        if (r instanceof Response) { const blob = await r.blob(); Utils.downloadFile(URL.createObjectURL(blob), 'report.html'); }
    },

    /* ----- AI ----- */
    askAI(question, fileId) { return this.request('/ai/query', { method: 'POST', body: { question, file_id: fileId } }); },

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
    authRecover(username) {
        return this.request('/auth/recover', { method: 'POST', body: { username } });
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
};
window.API = API;
