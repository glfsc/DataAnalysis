/**
 * DataVision Pro - 图表渲染模块
 * ECharts 封装，供 App 调用
 */
const Charts = {
    /** 当前图表实例 */
    _instance: null,

    /** 默认主题色 */
    _theme: {
        colors: ['#6366f1', '#8b5cf6', '#ec4899', '#38bdf8', '#10b981', '#f59e0b', '#ef4444', '#84cc16'],
        bg: '#1a1645',
        textColor: '#94a3b8',
        axisColor: 'rgba(255,255,255,0.1)',
        splitColor: 'rgba(255,255,255,0.04)',
    },

    /**
     * 渲染图表到指定 DOM 元素
     * @param {string} domId - DOM 元素 ID
     * @param {object} result - 后端返回的图表数据 {chart_type, chart_option, data, ...}
     */
    renderChart(domId, result) {
        const dom = document.getElementById(domId);
        if (!dom) { console.error('DOM不存在:', domId); return; }

        // 清空并创建容器
        dom.innerHTML = '';
        const chartDom = document.createElement('div');
        chartDom.style.width = '100%';
        chartDom.style.height = '400px';
        dom.appendChild(chartDom);

        // 销毁旧实例
        if (this._instance && !this._instance.isDisposed()) {
            this._instance.dispose();
        }

        this._instance = echarts.init(chartDom, 'dark', { renderer: 'canvas' });

        // 优先使用后端返回的 option，否则根据类型自动生成
        let option;
        if (result.chart_option) {
            option = result.chart_option;
        } else {
            option = this._buildOption(result);
        }

        // 注入主题
        option = this._applyTheme(option);

        this._instance.setOption(option);

        // 响应式
        const resizeHandler = Utils.debounce(() => {
            if (this._instance && !this._instance.isDisposed()) this._instance.resize();
        }, 200);
        window.addEventListener('resize', resizeHandler);
    },

    /** 根据 chart_type 和数据构建 ECharts option */
    _buildOption(result) {
        const chartType = result.chart_type || 'bar';
        const data = result.data || [];
        const xCol = result.x_column || 'x';
        const yCols = result.y_columns || [];
        const title = result.title || '';

        const baseOption = {
            title: { text: title, left: 'center', textStyle: { color: '#e2e8f0', fontSize: 14 } },
            tooltip: { trigger: chartType === 'pie' ? 'item' : 'axis' },
            legend: { bottom: 0, textStyle: { color: '#94a3b8', fontSize: 11 } },
        };

        // 如果 data 是数组字符串
        if (Array.isArray(data)) {
            const xData = data.map(d => d[xCol] !== undefined ? d[xCol] : Object.values(d)[0]);
            const series = yCols.length > 0 ? yCols.map(col => ({
                name: col,
                type: chartType,
                data: data.map(d => d[col]),
            })) : [{
                name: 'value',
                type: chartType,
                data: data.map(d => Object.values(d)[1]),
            }];

            return { ...baseOption, xAxis: { type:'category', data:xData }, yAxis: { type:'value' }, series };
        }

        return { ...baseOption, series: [{ type: chartType, data: [] }] };
    },

    /** 注入默认主题 */
    _applyTheme(option) {
        const t = this._theme;
        const defaults = {
            backgroundColor: 'transparent',
            color: t.colors,
            xAxis: { axisLine: { lineStyle: { color: t.axisColor } },
                      axisLabel: { color: t.textColor, fontSize: 11 },
                      splitLine: { lineStyle: { color: t.splitColor } } },
            yAxis: { axisLine: { lineStyle: { color: t.axisColor } },
                      axisLabel: { color: t.textColor, fontSize: 11 },
                      splitLine: { lineStyle: { color: t.splitColor } } },
        };

        // 浅合并（不覆盖已设置的）
        return echarts.util.merge ? echarts.util.merge({}, defaults, option) : { ...defaults, ...option };
    },
};

window.Charts = Charts;
