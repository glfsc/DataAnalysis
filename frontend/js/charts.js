/**
 * DataVision Pro - 图表渲染模块 v7
 * 支持双Y轴、数据合并、内联编辑、标题/图例样式编辑、轴定义域、组件拖拽
 */
const Charts = {
    _instance: null,
    _currentOption: null,
    _editCallback: null,
    _titleEditCallback: null,
    _dragState: null,  // 拖拽状态 {target, startX, startY, origLeft, origTop}

    _theme: {
        colors: ['#6366f1','#8b5cf6','#ec4899','#38bdf8','#10b981','#f59e0b','#ef4444','#84cc16'],
        textColor: '#94a3b8',
        axisColor: 'rgba(255,255,255,0.2)',
        splitColor: 'rgba(255,255,255,0.06)',
    },

    _needDualAxis(seriesData) {
        if (seriesData.length < 2) return false;
        const ranges = seriesData.map(s => {
            const vals = (s.data || []).filter(v => v !== null && v !== undefined && !isNaN(v));
            if (vals.length === 0) return 0;
            return Math.max(...vals) - Math.min(...vals);
        });
        const maxR = Math.max(...ranges, 1e-10);
        const minR = Math.min(...ranges.filter(r => r > 0), maxR);
        return (maxR / Math.max(minR, 1e-10)) > 8;
    },

    /** 合并相同X轴数据 */
    mergeSameXAxis(option) {
        const xAxis = option.xAxis;
        if (!xAxis || !xAxis.data) return option;
        const xData = xAxis.data;
        const seen = {};
        const mergeMap = {};
        for (let i = 0; i < xData.length; i++) {
            const key = String(xData[i]);
            if (seen[key] !== undefined) {
                if (!mergeMap[seen[key]]) mergeMap[seen[key]] = [];
                mergeMap[seen[key]].push(i);
            } else {
                seen[key] = i;
            }
        }

        // 如果有重复X值，合并
        const hasMerge = Object.keys(mergeMap).length > 0;
        if (!hasMerge) return option;

        // 构建新的xData（去重）
        const newXData = [];
        const keepIndices = new Set();
        for (let i = 0; i < xData.length; i++) {
            if (!Object.values(mergeMap).some(arr => arr.includes(i))) {
                keepIndices.add(i);
            }
        }
        // Rebuild
        const indexMap = {}; // old index -> new index
        let newIdx = 0;
        for (let i = 0; i < xData.length; i++) {
            const key = String(xData[i]);
            if (seen[key] === i) {
                // First occurrence
                indexMap[i] = newIdx;
                newXData.push(xData[i]);
                newIdx++;
            }
        }
        // For merged indices, accumulate into the first occurrence
        const accumulations = {}; // newIdx -> {oldIndices: []}
        for (const [firstIdx, dupIndices] of Object.entries(mergeMap)) {
            const newI = indexMap[parseInt(firstIdx)];
            if (newI !== undefined) {
                accumulations[newI] = { firstIdx: parseInt(firstIdx), dupIndices };
            }
        }

        // Update series data
        if (option.series) {
            for (const s of option.series) {
                if (!s.data || s.type === 'pie') continue;
                const newData = [];
                for (let i = 0; i < xData.length; i++) {
                    const key = String(xData[i]);
                    if (seen[key] === i) {
                        // First occurrence - sum all values for this key
                        const allIndices = [i];
                        if (mergeMap[i]) allIndices.push(...mergeMap[i]);
                        let sum = 0;
                        let count = 0;
                        for (const idx of allIndices) {
                            const v = s.data[idx];
                            if (v !== null && v !== undefined && !isNaN(v)) {
                                sum += Number(v);
                                count++;
                            }
                        }
                        newData.push(count > 1 ? sum : s.data[i]);
                    }
                }
                s.data = newData;
            }
        }

        option.xAxis.data = newXData;
        return option;
    },

    renderChart(domId, result, opts = {}) {
        const dom = document.getElementById(domId);
        if (!dom) return;

        dom.innerHTML = '';
        const chartDom = document.createElement('div');
        chartDom.style.width = '100%';
        chartDom.style.height = '420px';
        dom.appendChild(chartDom);

        if (this._instance && !this._instance.isDisposed()) this._instance.dispose();
        this._instance = echarts.init(chartDom);

        let option = result.echarts_option || result.chart_option || this._buildOption(result);

        // 合并相同X数据
        if (opts.mergeSameX) {
            option = this.mergeSameXAxis(JSON.parse(JSON.stringify(option)));
        }
        // X轴标签旋转
        if (opts.xLabelRotate && option.xAxis && !Array.isArray(option.xAxis)) {
            option.xAxis.axisLabel = { ...(option.xAxis.axisLabel || {}), rotate: parseInt(opts.xLabelRotate) || 45 };
        }
        // 应用每个series的颜色
        if (opts.seriesColors && option.series) {
            for (const sc of opts.seriesColors) {
                const s = option.series[sc.index];
                if (s) s.itemStyle = { ...(s.itemStyle || {}), color: sc.color };
            }
        }

        this._currentOption = this._applyTheme(option);
        const seriesArr = this._currentOption.series || [];

        // 智能双Y轴
        if (seriesArr.length >= 2 && this._needDualAxis(seriesArr)) {
            for (let i = 0; i < seriesArr.length; i++) {
                seriesArr[i].yAxisIndex = Math.min(i, 1);
            }
            this._currentOption.yAxis = [
                { ...(this._currentOption.yAxis || {}), name: (seriesArr[0] && seriesArr[0].name) || '' },
                { type: 'value', name: (seriesArr[1] && seriesArr[1].name) || '', splitLine: { show: false } },
            ];
        }

        this._instance.setOption(this._currentOption);

        // 点击数据点 → 内联编辑
        this._instance.off('click');
        this._instance.on('click', (params) => {
            if (params.componentType === 'series' && this._editCallback) {
                this._editCallback(params, chartDom);
            }
        });

        // 双击标题/图例 → 样式编辑
        this._instance.off('dblclick');
        this._instance.on('dblclick', (params) => {
            if (this._titleEditCallback && (params.componentType === 'title' || params.componentType === 'legend')) {
                this._titleEditCallback(params);
            }
        });

        // ===== 长按拖拽：标题、图例、dataZoom =====
        this._setupDragInteraction(chartDom);

        const resizeHandler = Utils.debounce(() => {
            if (this._instance && !this._instance.isDisposed()) this._instance.resize();
        }, 200);
        window.addEventListener('resize', resizeHandler);
    },

    /** 设置长按拖拽交互（标题/图例/dataZoom 可拖拽重新定位） */
    _setupDragInteraction(chartDom) {
        const self = this;
        let pressTimer = null;
        let dragInfo = null;

        // 清理上一次的监听器
        if (this._dragCleanup) {
            this._dragCleanup();
            this._dragCleanup = null;
        }

        const onMouseDown = (e) => {
            // 仅在图表区域内处理
            if (!chartDom.contains(e.target)) return;
            const rect = chartDom.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            // 检测鼠标下的 ECharts 组件
            if (!self._instance || self._instance.isDisposed()) return;
            try {
                // 使用 getZr() 检测点击位置所在的元素
                const handler = self._instance.getZr().handler;
                // 通过坐标判断可能点击的组件
                const opt = self._currentOption;
                if (!opt) return;

                let targetComp = null;
                // 检测标题区域
                if (opt.title && opt.title.show !== false) {
                    const titleOpt = opt.title;
                    const titleTop = self._getPixelValue(titleOpt.top, rect.height, 10);
                    const titleLeft = self._getPixelValueFromLeft(titleOpt.left, rect.width, 'center');
                    // 估算标题区域
                    const titleHeight = (titleOpt.textStyle?.fontSize || 14) + 20;
                    const titleWidth = ((titleOpt.text || '').length * (titleOpt.textStyle?.fontSize || 14) * 0.7) + 40;
                    if (x >= titleLeft - titleWidth/2 && x <= titleLeft + titleWidth/2 &&
                        y >= titleTop && y <= titleTop + titleHeight) {
                        targetComp = 'title';
                    }
                }
                // 检测图例区域（通常在底部）
                if (!targetComp && opt.legend && opt.legend.show !== false) {
                    const legendOpt = opt.legend;
                    const legendBottom = legendOpt.bottom !== undefined ? self._getPixelValueFromBottom(legendOpt.bottom, rect.height, 0) : 0;
                    const legendTop = rect.height - legendBottom - 30;
                    const legendLeft = self._getPixelValueFromLeft(legendOpt.left, rect.width, 'center');
                    const legendWidth = 200; // 估算
                    if (x >= legendLeft - legendWidth/2 && x <= legendLeft + legendWidth/2 &&
                        y >= legendTop && y <= rect.height - legendBottom + 5) {
                        targetComp = 'legend';
                    }
                }
                // 检测 dataZoom 区域（底部滑块）
                if (!targetComp && opt.dataZoom && opt.dataZoom.length > 0) {
                    const dz = opt.dataZoom[0];
                    const dzBottom = dz.bottom !== undefined ? dz.bottom : 5;
                    const dzHeight = dz.height || 20;
                    const dzTop = rect.height - dzBottom - dzHeight;
                    const dzLeft = (opt.grid && opt.grid.length > 0 ? (opt.grid[0].left || 60) : 60);
                    const dzRight = (opt.grid && opt.grid.length > 0 ? (opt.grid[0].right || 40) : 40);
                    const dzWidth = rect.width - dzLeft - dzRight;
                    if (x >= dzLeft && x <= dzLeft + dzWidth && y >= dzTop - 5 && y <= rect.height - dzBottom + 5) {
                        targetComp = 'dataZoom';
                    }
                }

                if (targetComp) {
                    chartDom.style.cursor = 'grab';
                    // 长按 400ms 开始拖拽
                    pressTimer = setTimeout(() => {
                        chartDom.style.cursor = 'grabbing';
                        dragInfo = {
                            componentType: targetComp,
                            startX: e.clientX,
                            startY: e.clientY,
                            chartRect: rect,
                            origLeft: targetComp === 'title' ? self._currentOption.title.left :
                                      targetComp === 'legend' ? self._currentOption.legend.left : undefined,
                            origTop: targetComp === 'title' ? self._currentOption.title.top :
                                     targetComp === 'legend' ? self._currentOption.legend.top : undefined,
                            origBottom: targetComp === 'dataZoom' ? (self._currentOption.dataZoom?.[0]?.bottom ?? 5) :
                                        targetComp === 'legend' ? self._currentOption.legend.bottom : undefined,
                        };
                        // Show toast hint
                        if (typeof Utils !== 'undefined' && Utils.toast) {
                            Utils.toast('拖动以重新定位' + (targetComp === 'title' ? '标题' : targetComp === 'legend' ? '图例' : '滑动条'), 'info');
                        }
                    }, 400);
                }
            } catch (err) {
                // getZr may fail, ignore
            }
        };

        const onMouseMove = (e) => {
            if (!dragInfo) return;
            const dx = e.clientX - dragInfo.startX;
            const dy = e.clientY - dragInfo.startY;
            const rect = dragInfo.chartRect;

            const update = {};
            if (dragInfo.componentType === 'title') {
                // 标题：计算新的 left, top 像素值
                const curLeft = self._getPixelValueFromLeft(dragInfo.origLeft, rect.width, 'center');
                const curTop = self._getPixelValue(dragInfo.origTop, rect.height, 10);
                update.title = {
                    left: Math.max(0, Math.min(rect.width, curLeft + dx)),
                    top: Math.max(0, Math.min(rect.height - 40, curTop + dy)),
                };
            } else if (dragInfo.componentType === 'legend') {
                const curBottom = dragInfo.origBottom !== undefined ? dragInfo.origBottom : 0;
                const curLeft = self._getPixelValueFromLeft(dragInfo.origLeft, rect.width, 'center');
                // 图例：调整 left 和 bottom
                const newBottom = Math.max(0, Math.min(rect.height - 20, curBottom - dy));
                update.legend = {
                    left: Math.max(0, Math.min(rect.width, curLeft + dx)),
                    bottom: newBottom,
                };
            } else if (dragInfo.componentType === 'dataZoom') {
                const curBottom = dragInfo.origBottom;
                const newBottom = Math.max(0, Math.min(rect.height - 20, curBottom - dy));
                const dz = self._currentOption?.dataZoom;
                if (dz && dz.length > 0 && dz[0]) {
                    const newDz = { ...dz[0], bottom: newBottom };
                    update.dataZoom = [newDz];
                }
            }

            if (Object.keys(update).length > 0) {
                self._instance.setOption(update);
                // 更新缓存
                if (self._currentOption) {
                    Object.assign(self._currentOption, update);
                }
            }
        };

        const onMouseUp = () => {
            clearTimeout(pressTimer);
            pressTimer = null;
            if (dragInfo) {
                chartDom.style.cursor = '';
                dragInfo = null;
            }
        };

        const onMouseLeave = () => {
            clearTimeout(pressTimer);
            pressTimer = null;
            if (dragInfo) {
                chartDom.style.cursor = '';
                dragInfo = null;
            }
        };

        chartDom.addEventListener('mousedown', onMouseDown);
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
        chartDom.addEventListener('mouseleave', onMouseLeave);

        // 存储清理函数
        this._dragCleanup = () => {
            chartDom.removeEventListener('mousedown', onMouseDown);
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            chartDom.removeEventListener('mouseleave', onMouseLeave);
        };
    },

    /** 将 top/bottom 值转换为像素 */
    _getPixelValue(val, containerHeight, defaultVal) {
        if (val === undefined || val === null) return defaultVal;
        if (typeof val === 'number') return val;
        if (typeof val === 'string' && val.endsWith('%')) {
            return containerHeight * parseFloat(val) / 100;
        }
        return parseInt(val) || defaultVal;
    },

    /** 将 left 值转换为像素（从左边算） */
    _getPixelValueFromLeft(val, containerWidth, defaultVal) {
        if (val === undefined || val === null) {
            if (defaultVal === 'center') return containerWidth / 2;
            return defaultVal;
        }
        if (typeof val === 'number') return val;
        if (val === 'center' || val === 'middle') return containerWidth / 2;
        if (val === 'left' || val === 'start') return 50;
        if (val === 'right' || val === 'end') return containerWidth - 50;
        if (typeof val === 'string' && val.endsWith('%')) {
            return containerWidth * parseFloat(val) / 100;
        }
        return parseInt(val) || containerWidth / 2;
    },

    /** 将 bottom 值转换为像素（从底部算） */
    _getPixelValueFromBottom(val, containerHeight, defaultVal) {
        if (val === undefined || val === null) return defaultVal;
        if (typeof val === 'number') return val;
        if (typeof val === 'string' && val.endsWith('%')) {
            return containerHeight * parseFloat(val) / 100;
        }
        return parseInt(val) || defaultVal;
    },

    /** 编辑图表标题样式 */
    editTitleStyle(style) {
        if (!this._instance || this._instance.isDisposed()) return;
        const opt = {};
        if (style.text !== undefined) opt.text = style.text;
        if (style.color) opt.textStyle = { color: style.color };
        if (style.fontSize) opt.textStyle = { ...(opt.textStyle || {}), fontSize: style.fontSize };
        if (style.left) opt.left = style.left;
        if (style.top) opt.top = style.top;
        this._instance.setOption({ title: opt });
        // 更新缓存
        if (this._currentOption && this._currentOption.title) {
            Object.assign(this._currentOption.title, opt);
        }
    },

    /** 编辑图例样式 */
    editLegendStyle(style) {
        if (!this._instance || this._instance.isDisposed()) return;
        const opt = {};
        if (style.color) opt.textStyle = { color: style.color };
        if (style.fontSize) opt.textStyle = { ...(opt.textStyle || {}), fontSize: style.fontSize };
        if (style.left) opt.left = style.left;
        if (style.top) opt.top = style.top;
        this._instance.setOption({ legend: opt });
        if (this._currentOption && this._currentOption.legend) {
            Object.assign(this._currentOption.legend, opt);
        }
    },

    toggleDataLabels(show) {
        if (!this._instance || this._instance.isDisposed()) return;
        const seriesArr = (this._currentOption && this._currentOption.series) || [];
        for (const s of seriesArr) {
            if (s.type === 'pie') {
                s.label = { ...(s.label || {}), show: show };
            } else {
                s.label = { show: show, position: 'top', color: '#cbd5e1', fontSize: 11 };
            }
        }
        this._instance.setOption({ series: seriesArr });
    },

    updateColors(colors) {
        if (!this._instance || this._instance.isDisposed()) return;
        this._theme.colors = colors;
        this._instance.setOption({ color: colors });
    },

    getColors() { return [...this._theme.colors]; },

    /** 更新轴定义域 */
    updateAxisDomain(domain) {
        if (!this._instance || this._instance.isDisposed()) return;
        const update = {};

        // X轴定义域
        if (domain.xMin !== null || domain.xMax !== null) {
            const xAxis = this._currentOption?.xAxis;
            if (xAxis) {
                // Category 轴使用 dataZoom 来限制可见范围
                if (xAxis.type === 'category' && xAxis.data && xAxis.data.length > 0) {
                    const total = xAxis.data.length;
                    // 获取当前 dataZoom 状态（保留用户拖拽的位置和高度）
                    const curDz = (this._currentOption?.dataZoom && this._currentOption.dataZoom.length > 0)
                        ? this._currentOption.dataZoom[0] : null;
                    const curStart = (curDz && curDz.start !== undefined) ? curDz.start : 0;
                    const curEnd = (curDz && curDz.end !== undefined) ? curDz.end : 100;
                    const xMinIdx = domain.xMin !== null ? Math.max(0, Math.min(total - 1, Math.floor(domain.xMin))) : Math.round(curStart / 100 * total);
                    const xMaxIdx = domain.xMax !== null ? Math.max(0, Math.min(total - 1, Math.floor(domain.xMax))) : Math.round(curEnd / 100 * total) - 1;
                    const startPct = (xMinIdx / total) * 100;
                    const endPct = ((xMaxIdx + 1) / total) * 100;
                    const dz = curDz ? { ...curDz } : { type: 'slider', start: 0, end: 100, bottom: 5, height: 20 };
                    dz.start = Math.max(0, startPct);
                    dz.end = Math.min(100, endPct);
                    update.dataZoom = [dz];
                } else {
                    // Value 轴直接设置 min/max
                    const newX = { ...(xAxis || {}) };
                    if (domain.xMin !== null) newX.min = domain.xMin;
                    else if (newX.min !== undefined) delete newX.min;
                    if (domain.xMax !== null) newX.max = domain.xMax;
                    else if (newX.max !== undefined) delete newX.max;
                    update.xAxis = newX;
                }
            }
        }

        // Y轴定义域
        if (domain.yMin !== null || domain.yMax !== null) {
            const yAxis = this._currentOption?.yAxis;
            if (yAxis) {
                if (Array.isArray(yAxis)) {
                    update.yAxis = yAxis.map(y => {
                        const ny = { ...y };
                        if (domain.yMin !== null) ny.min = domain.yMin;
                        else if (ny.min !== undefined) delete ny.min;
                        if (domain.yMax !== null) ny.max = domain.yMax;
                        else if (ny.max !== undefined) delete ny.max;
                        return ny;
                    });
                } else {
                    const ny = { ...(yAxis || {}) };
                    if (domain.yMin !== null) ny.min = domain.yMin;
                    else if (ny.min !== undefined) delete ny.min;
                    if (domain.yMax !== null) ny.max = domain.yMax;
                    else if (ny.max !== undefined) delete ny.max;
                    update.yAxis = ny;
                }
            }
        }

        this._instance.setOption(update);
        // 更新缓存
        if (this._currentOption) {
            if (update.xAxis) this._currentOption.xAxis = update.xAxis;
            if (update.yAxis) this._currentOption.yAxis = update.yAxis;
            if (update.dataZoom) this._currentOption.dataZoom = update.dataZoom;
        }
    },

    updateDataPoint(seriesIndex, dataIndex, newValue) {
        if (!this._instance || this._instance.isDisposed()) return false;
        const seriesArr = (this._currentOption && this._currentOption.series) || [];
        if (seriesIndex < 0 || seriesIndex >= seriesArr.length) return false;
        const s = seriesArr[seriesIndex];
        if (s.type === 'pie') {
            const data = s.data || [];
            if (dataIndex >= 0 && dataIndex < data.length) {
                data[dataIndex].value = newValue;
                this._instance.setOption({ series: [{ data: data }] });
                return true;
            }
        } else {
            const data = s.data || [];
            if (dataIndex >= 0 && dataIndex < data.length) {
                data[dataIndex] = newValue;
                this._instance.setOption({ series: [{ data: data }] });
                return true;
            }
        }
        return false;
    },

    getChartData() { return (this._currentOption && this._currentOption.series) || []; },

    getInstance() { return this._instance; },

    _buildOption(result) {
        const ct = result.chart_type || 'bar';
        const data = result.data || [];
        const xCol = result.x_column || 'x';
        const yCols = result.y_columns || [];
        const title = result.title || '';
        const base = {
            title: { text: title, left: 'center', triggerEvent: true, textStyle: { color: '#e2e8f0', fontSize: 14 } },
            tooltip: { trigger: ct === 'pie' ? 'item' : 'axis' },
            legend: { bottom: 0, textStyle: { color: '#94a3b8', fontSize: 11 } },
            grid: { bottom: 60, left: 60, right: 40, top: 50 },
            dataZoom: [{ type: 'slider', start: 0, end: 100, bottom: 5, height: 20 }],
        };
        if (Array.isArray(data) && data.length > 0) {
            const xData = data.map(d => d[xCol] !== undefined ? String(d[xCol]) : String(Object.values(d)[0]));
            const series = yCols.length > 0
                ? yCols.map(col => ({ name: col, type: ct, data: data.map(d => d[col]) }))
                : [{ name: 'value', type: ct, data: data.map(d => Object.values(d)[1]) }];
            return { ...base, xAxis: { type: 'category', data: xData }, yAxis: { type: 'value' }, series };
        }
        return { ...base, series: [{ type: ct, data: [] }] };
    },

    _applyTheme(option) {
        const t = this._theme;
        // Ensure title has triggerEvent
        if (option.title) option.title.triggerEvent = true;
        const result = { backgroundColor: 'transparent', color: t.colors, ...option };

        if (result.series) {
            for (const s of result.series) {
                if (s.type === 'bar') {
                    s.itemStyle = { ...(s.itemStyle || {}), borderColor: 'rgba(255,255,255,0.15)', borderWidth: 1 };
                } else if (s.type === 'pie') {
                    s.itemStyle = { ...(s.itemStyle || {}), borderColor: 'rgba(0,0,0,0.3)', borderWidth: 2 };
                } else if (s.type === 'line') {
                    s.lineStyle = { ...(s.lineStyle || {}), width: 2 };
                    s.symbolSize = s.symbolSize || 6;
                }
            }
        }

        const themeAxis = (ax) => ({
            axisLine: { lineStyle: { color: t.axisColor } },
            axisLabel: { color: t.textColor, fontSize: 11 },
            splitLine: { lineStyle: { color: t.splitColor } },
            ...(ax || {}),
            axisLabel: { color: t.textColor, fontSize: 11, ...((ax && ax.axisLabel) || {}) },
            axisLine: { lineStyle: { color: t.axisColor }, ...((ax && ax.axisLine) || {}) },
        });

        if (result.xAxis) {
            result.xAxis = Array.isArray(result.xAxis) ? result.xAxis.map(themeAxis) : themeAxis(result.xAxis);
        }
        if (result.yAxis) {
            result.yAxis = Array.isArray(result.yAxis) ? result.yAxis.map(themeAxis) : themeAxis(result.yAxis);
        }
        return result;
    },
};

window.Charts = Charts;
