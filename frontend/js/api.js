/**
 * DataVision Pro - API 调用模块
 * 封装所有后端接口请求
 */
const API = {
    BASE_URL: '/api',

    /**
     * 通用请求
     */
    async request(endpoint, options = {}) {
        const url = `${this.BASE_URL}${endpoint}`;
        const config = {
            headers: { 'Accept': 'application/json' },
            ...options,
        };

        if (!(options.body instanceof FormData)) {
            config.headers['Content-Type'] = 'application/json';
            if (options.body && typeof options.body === 'object') {
                config.body = JSON.stringify(options.body);
            }
        } else {
            // FormData 不设置 Content-Type，让浏览器自动
            delete config.headers['Content-Type'];
        }

        const response = await fetch(url, config);

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `请求失败 (${response.status})`);
        }

        const contentType = response.headers.get('content-type') || '';
        if (contentType.includes('text/csv') || contentType.includes('text/html')) {
            return response;
        }

        return response.json();
    },

    /* ----- 系统 ----- */
    healthCheck() {
        return this.request('/health');
    },

    systemInfo() {
        return this.request('/info');
    },

    /* ----- 文件上传 ----- */
    async uploadFile(file, onProgress) {
        const formData = new FormData();
        formData.append('file', file);

        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', `${this.BASE_URL}/upload`);

            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable && onProgress) {
                    onProgress(Math.round((e.loaded / e.total) * 100));
                }
            };

            xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve(JSON.parse(xhr.responseText));
                } else {
                    try {
                        const err = JSON.parse(xhr.responseText);
                        reject(new Error(err.detail || `上传失败 (${xhr.status})`));
                    } catch {
                        reject(new Error(`上传失败 (${xhr.status})`));
                    }
                }
            };

            xhr.onerror = () => reject(new Error('网络连接失败'));
            xhr.send(formData);
        });
    },

    /* ----- 数据清洗 ----- */
    cleanData(params) {
        return this.request('/cleaning/clean', { method: 'POST', body: params });
    },

    /* ----- 数据分析 ----- */
    runAnalysis(action, fileId) {
        const endpoints = {
            statistics:  '/analysis/statistics',
            correlation: '/analysis/correlation',
            groupby:     '/analysis/groupby',
            cluster:     '/analysis/cluster',
            regression:  '/analysis/regression',
            anomaly:     '/analysis/anomaly',
        };
        const endpoint = endpoints[action];
        if (!endpoint) throw new Error(`未知分析类型: ${action}`);

        return this.request(endpoint, {
            method: 'POST',
            body: { file_id: fileId },
        });
    },

    /* ----- 可视化 ----- */
    generateChart(fileId, chartConfig) {
        return this.request('/visualization/generate', {
            method: 'POST',
            body: { file_id: fileId, ...chartConfig },
        });
    },

    /* ----- 导出 ----- */
    async exportData(fileId) {
        const response = await this.request('/export/data', {
            method: 'POST',
            body: { file_id: fileId },
        });

        if (response instanceof Response) {
            const blob = await response.blob();
            Utils.downloadFile(URL.createObjectURL(blob), 'data_export.csv');
        }
    },

    async exportReport(fileId) {
        const response = await this.request('/export/report', {
            method: 'POST',
            body: { file_id: fileId },
        });

        if (response instanceof Response) {
            const blob = await response.blob();
            Utils.downloadFile(URL.createObjectURL(blob), 'report.html');
        }
    },

    /* ----- AI 助手 ----- */
    askAI(question, fileId) {
        return this.request('/ai/query', {
            method: 'POST',
            body: { question, file_id: fileId },
        });
    },

    autoInsights(fileId) {
        return this.request('/ai/insights', {
            method: 'POST',
            body: { file_id: fileId },
        });
    },
};
