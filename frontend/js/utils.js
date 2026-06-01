/**
 * DataVision Pro - 工具函数模块
 */
const Utils = {
    /** Toast 简写 */
    toast(message, type = 'info', duration = 3000) {
        return this.showToast(message, type, duration);
    },

    /** 显示Toast通知 */
    showToast(message, type = 'info', duration = 3000) {
        const container = document.getElementById('toastContainer');
        if (!container) return;
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(20px)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },

    /** 格式化文件大小 */
    formatFileSize(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        const units = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + units[i];
    },

    /** 格式化数字 */
    formatNumber(num) {
        if (num == null) return '-';
        return Number(num).toLocaleString('zh-CN');
    },

    /** 下载文件 */
    downloadFile(url, filename) {
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    },

    /** 防抖 */
    debounce(fn, delay = 300) {
        let timer;
        return function (...args) {
            clearTimeout(timer);
            timer = setTimeout(() => fn.apply(this, args), delay);
        };
    },

    /** 节流 */
    throttle(fn, limit = 300) {
        let inThrottle;
        return function (...args) {
            if (!inThrottle) {
                fn.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    /** 生成唯一ID */
    generateId() {
        return 'id_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    },

    /** HTML转义 */
    escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    /** 本地存储 */
    storage: {
        get(key, defaultValue = null) {
            try {
                const v = localStorage.getItem(`datavision_${key}`);
                return v ? JSON.parse(v) : defaultValue;
            } catch { return defaultValue; }
        },
        set(key, value) {
            try { localStorage.setItem(`datavision_${key}`, JSON.stringify(value)); } catch {}
        },
        remove(key) { localStorage.removeItem(`datavision_${key}`); },
    },

    /** 检测移动端 */
    isMobile() { return window.innerWidth <= 768; },
};

window.Utils = Utils;
