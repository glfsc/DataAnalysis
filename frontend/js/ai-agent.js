/**
 * DataVision Pro - AI 助手模块
 * AI 交互逻辑辅助（UI 已整合到 main.js 的 AI 视图中）
 */
const AIAgent = {
    history: [],

    /** 添加到历史 */
    addToHistory(role, text) {
        this.history.push({ role, text, time: new Date().toISOString() });
        if (this.history.length > 50) this.history.shift();
    },

    /** 获取历史 */
    getHistory() { return [...this.history]; },

    /** 清空历史 */
    clearHistory() { this.history = []; },
};

window.AIAgent = AIAgent;
