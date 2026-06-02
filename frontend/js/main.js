/**
 * DataVision Pro - 主控模块 v3
 * 全量数据弹窗 · 清洗删除详情 · 统计列选择 · 可视化CRUD
 */
const App = {
    state: {
        files:{}, fileOrder:[], selectedIds:[], currentFileId:null,
        currentView:'dashboard', currentStep:'upload', currentChart:null, currentAnalysisAction:null,
        editedData:null, // 可视化编辑中的数据
    },

    init() {
        console.log('Data Analysis System init');
        // 初始化认证模块
        if (typeof Auth !== 'undefined') Auth.init();
        this._initWelcomeParticles(); this._bindWelcomeBtn();
        this._bindNavEvents(); this._bindUploadEvents(); this._bindCleaningEvents();
        this._bindAnalysisEvents(); this._bindVisualizationEvents(); this._bindExportEvents();
        this._bindAIEvents(); this._bindDashboardEvents(); this._bindModalEvents();
        this._checkServerHealth();
    },

    /* ========== 欢迎页 ========== */
    _initWelcomeParticles() {
        const c=document.getElementById('welcomeParticles'); if(!c)return;
        const ctx=c.getContext('2d');c.width=window.innerWidth;c.height=window.innerHeight;
        const pts=Array.from({length:100},()=>({x:Math.random()*c.width,y:Math.random()*c.height,r:Math.random()*2+1,vx:(Math.random()-0.5)*0.5,vy:(Math.random()-0.5)*0.5,color:['#6366f1','#8b5cf6','#ec4899','#38bdf8','#fff'][Math.floor(Math.random()*5)],alpha:Math.random()*0.6+0.4}));
        (function anim(){if(document.getElementById('welcomeScreen').classList.contains('fade-out'))return;ctx.clearRect(0,0,c.width,c.height);pts.forEach(p=>{p.x+=p.vx;p.y+=p.vy;if(p.x<-10)p.x=c.width+10;if(p.x>c.width+10)p.x=-10;if(p.y<-10)p.y=c.height+10;if(p.y>c.height+10)p.y=-10;ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);ctx.fillStyle=p.color;ctx.globalAlpha=p.alpha;ctx.fill();});ctx.globalAlpha=1;for(let i=0;i<pts.length;i++)for(let j=i+1;j<pts.length;j++){const dx=pts[i].x-pts[j].x,dy=pts[i].y-pts[j].y,dist=Math.sqrt(dx*dx+dy*dy);if(dist<120){ctx.strokeStyle='rgba(99,102,241,'+((1-dist/120)*0.08)+')';ctx.lineWidth=0.5;ctx.beginPath();ctx.moveTo(pts[i].x,pts[i].y);ctx.lineTo(pts[j].x,pts[j].y);ctx.stroke();}}requestAnimationFrame(anim);})();
        window.addEventListener('resize',()=>{c.width=window.innerWidth;c.height=window.innerHeight;});
    },
    _bindWelcomeBtn(){
        document.getElementById('btnStart').addEventListener('click',()=>{
            // 检查登录状态
            if (typeof Auth !== 'undefined' && !Auth.isLoggedIn()) {
                Auth._showAuthModal('login');
                return;
            }
            this._enterApp();
        });
    },
    /** 进入主应用（欢迎页淡出，显示仪表盘） */
    _enterApp(){
        document.getElementById('welcomeScreen').classList.add('fade-out');
        document.getElementById('appWrapper').style.display='block';
        // 刷新顶栏头像
        if (typeof Auth !== 'undefined') Auth._renderTopbarAvatar();
        setTimeout(()=>{if(typeof Particles!=='undefined')Particles.init();},300);
    },

    /* ========== 文件管理 ========== */
    _addFile(r){const fid=r.file_id;this.state.files[fid]={fileName:r.file_name,fileSize:r.file_size,uploadTime:new Date().toISOString(),columns:r.columns||[],numericColumns:r.numeric_columns||[],rowCount:r.row_count||0,colCount:r.column_count||0,missingCount:r.missing_count||0,cleanedFileId:null,previewData:r.preview_data||[],progress:{upload:true,cleaning:false,analysis:false,visualization:false,export:false}};if(!this.state.fileOrder.includes(fid))this.state.fileOrder.unshift(fid);if(!this.state.selectedIds.includes(fid))this.state.selectedIds.push(fid);this.state.currentFileId=fid;this._refreshDashboard();this._updateFileIndicators();},
    _getActiveFileId(){if(this.state.selectedIds.length===1)return this.state.selectedIds[0];if(this.state.currentFileId&&this.state.selectedIds.includes(this.state.currentFileId))return this.state.currentFileId;return this.state.selectedIds[0]||null;},
    _markProgress(fid,s){if(this.state.files[fid])this.state.files[fid].progress[s]=true;},

    /* ========== 仪表盘 ========== */
    _refreshDashboard(){
        const files=Object.values(this.state.files);const t=files.length;
        document.getElementById('dashTotal').textContent=t;
        document.getElementById('dashPending').textContent=files.filter(f=>!f.progress.cleaning&&!f.progress.analysis).length;
        document.getElementById('dashCompleted').textContent=files.filter(f=>f.progress.export).length;
        document.getElementById('dashInProgress').textContent=files.filter(f=>(f.progress.cleaning||f.progress.analysis)&&!f.progress.export).length;
        this._renderRecentList();this._updateQuickBtns();
    },
    _renderRecentList(){
        const list=document.getElementById('recentList');
        if(this.state.fileOrder.length===0){list.innerHTML='<div class="empty-state-sm">暂无项目，点击"上传数据"开始分析</div>';return;}
        list.innerHTML=this.state.fileOrder.map(fid=>{const f=this.state.files[fid];if(!f)return'';const sel=this.state.selectedIds.includes(fid);const t=new Date(f.uploadTime);const ts=(t.getMonth()+1)+'/'+t.getDate()+' '+t.getHours()+':'+String(t.getMinutes()).padStart(2,'0');const p=f.progress;return '<div class="recent-item '+(sel?'selected':'')+'" data-fid="'+fid+'"><input type="checkbox" class="recent-checkbox" '+(sel?'checked':'')+' data-fid="'+fid+'"><div class="recent-info"><span class="recent-name">'+Utils.escapeHtml(f.fileName)+'</span><div class="recent-meta"><span>'+Utils.formatFileSize(f.fileSize)+'</span><span>'+f.rowCount+'行 x '+f.colCount+'列</span><span>'+ts+'</span></div></div><div class="recent-progress"><span class="progress-step-dot '+(p.upload?'done':'active')+'" title="上传"></span><span class="progress-step-dot '+(p.cleaning?'done':'')+'" title="清洗"></span><span class="progress-step-dot '+(p.analysis?'done':'')+'" title="分析"></span><span class="progress-step-dot '+(p.visualization?'done':'')+'" title="可视化"></span><span class="progress-step-dot '+(p.export?'done':'')+'" title="导出"></span><span class="progress-label">'+this._progressText(p)+'</span></div></div>';}).join('');
        list.querySelectorAll('.recent-item').forEach(item=>{item.addEventListener('click',e=>{if(e.target.tagName==='INPUT')return;const cb=item.querySelector('.recent-checkbox');cb.checked=!cb.checked;cb.dispatchEvent(new Event('change'));});item.addEventListener('dblclick',e=>{e.preventDefault();this._showFullDataPreview(item.dataset.fid);});});
        list.querySelectorAll('.recent-checkbox').forEach(cb=>{cb.addEventListener('change',e=>{e.stopPropagation();const fid=cb.dataset.fid;if(cb.checked){if(!this.state.selectedIds.includes(fid))this.state.selectedIds.push(fid);}else{this.state.selectedIds=this.state.selectedIds.filter(id=>id!==fid);}this._updateSelection();});});
    },
    _progressText(p){if(p.export)return'已完成';if(p.visualization)return'已可视化';if(p.analysis)return'已分析';if(p.cleaning)return'已清洗';if(p.upload)return'已上传';return'';},
    _updateSelection(){document.querySelectorAll('.recent-item').forEach(item=>{const fid=item.dataset.fid;item.classList.toggle('selected',this.state.selectedIds.includes(fid));const cb=item.querySelector('.recent-checkbox');if(cb)cb.checked=this.state.selectedIds.includes(fid);});this._updateQuickBtns();this._updateFileIndicators();if(this.state.selectedIds.length===1)this.state.currentFileId=this.state.selectedIds[0];},
    _updateQuickBtns(){const h=this.state.selectedIds.length>0;['btnQuickClean','btnQuickAnalysis','btnQuickViz'].forEach(id=>{document.getElementById(id).disabled=!h;});},
    _bindDashboardEvents(){
        document.getElementById('btnQuickUpload').addEventListener('click',()=>document.getElementById('fileInput').click());
        document.getElementById('btnQuickClean').addEventListener('click',()=>{if(this.state.selectedIds.length>0)this.switchView('cleaning');});
        document.getElementById('btnQuickAnalysis').addEventListener('click',()=>{if(this.state.selectedIds.length>0)this.switchView('analysis');});
        document.getElementById('btnQuickViz').addEventListener('click',()=>{if(this.state.selectedIds.length>0)this.switchView('visualization');});
        document.getElementById('btnSelectAll').addEventListener('click',()=>{this.state.selectedIds=[...this.state.fileOrder];this._updateSelection();this._refreshDashboard();});
        document.getElementById('btnDeselectAll').addEventListener('click',()=>{this.state.selectedIds=[];this._updateSelection();this._refreshDashboard();});
    },
    _updateFileIndicators(){
        const ids=this.state.selectedIds;const single=ids.length===1?(this.state.files[ids[0]]?.fileName||'未选择文件'):(ids.length>1?ids.length+' 个文件已选择':'未选择文件');
        const names=ids.map(id=>this.state.files[id]?.fileName||'?').join(', ');
        ['cleanFileName','analysisFileName','vizFileName'].forEach(elId=>{const el=document.getElementById(elId);if(el)el.textContent=ids.length>1?ids.length+' 个文件: '+names:single;});
    },

    /* ========== 全量数据预览弹窗 ========== */
    _bindModalEvents(){
        document.getElementById('btnClosePreview').addEventListener('click',()=>{document.getElementById('dataPreviewModal').style.display='none';});
        document.getElementById('dataPreviewModal').addEventListener('click',e=>{if(e.target===document.getElementById('dataPreviewModal'))document.getElementById('dataPreviewModal').style.display='none';});
    },
    async _showFullDataPreview(fid){
        const f=this.state.files[fid];if(!f)return;
        document.getElementById('previewModalTitle').textContent=f.fileName;
        document.getElementById('previewModalTags').innerHTML='<span class="file-info-tag">'+f.rowCount+' 行</span><span class="file-info-tag">'+f.colCount+' 列</span><span class="file-info-tag">'+Utils.formatFileSize(f.fileSize)+'</span><span class="file-info-tag">缺失值: '+f.missingCount+'</span>';
        document.getElementById('previewModalTable').innerHTML='<tr><td colspan="10" style="text-align:center;padding:40px;">加载中...</td></tr>';
        document.getElementById('dataPreviewModal').style.display='flex';
        try{
            const useId=f.cleanedFileId||fid;
            const result=await API.getAllData(useId);
            if(result.data&&result.data.length>0){
                const cols=result.columns||Object.keys(result.data[0]);
                const tbody=result.data.map((row,i)=>'<tr>'+cols.map(c=>'<td>'+(row[c]!==null&&row[c]!==undefined?String(row[c]).slice(0,80):'')+'</td>').join('')+'</tr>').join('');
                document.getElementById('previewModalTable').innerHTML='<thead><tr><th>#</th>'+cols.map(c=>'<th>'+c+'</th>').join('')+'</tr></thead><tbody>'+result.data.map((row,i)=>'<tr><td style="color:var(--text-muted);font-size:0.8em">'+(i+1)+'</td>'+cols.map(c=>'<td>'+(row[c]!==null&&row[c]!==undefined?String(row[c]).slice(0,80):'')+'</td>').join('')+'</tr>').join('')+'</tbody>';
            }
        }catch(e){document.getElementById('previewModalTable').innerHTML='<tr><td style="text-align:center;padding:40px;color:var(--danger)">加载失败: '+e.message+'</td></tr>';}
    },

    /* ========== 导航 ========== */
    _bindNavEvents(){
        document.querySelectorAll('.nav-item[data-view]').forEach(item=>{item.addEventListener('click',()=>this.switchView(item.dataset.view));});
        document.querySelectorAll('.stepper-step').forEach(step=>{step.addEventListener('click',()=>{const m={upload:'dashboard',cleaning:'cleaning',analysis:'analysis',visualization:'visualization',export:'visualization'};if(m[step.dataset.step])this.switchView(m[step.dataset.step]);});});
    },
    switchView(v){
        document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));const ni=document.querySelector('.nav-item[data-view="'+v+'"]');if(ni)ni.classList.add('active');
        document.querySelectorAll('.view').forEach(vv=>vv.classList.remove('active'));const t=document.getElementById('view-'+v);if(t)t.classList.add('active');
        this.state.currentView=v;this._updateStepper(v);if(v!=='dashboard')this._updateFileIndicators();
        if(v==='analysis'){document.getElementById('analysisModeSelect').style.display='block';document.getElementById('analysisWorkPanel').style.display='none';this.state.currentAnalysisAction=null;}
        if(v==='visualization'){setTimeout(()=>this._updateYColumnList(),50);}
    },
    _updateStepper(v){const m={dashboard:'upload',cleaning:'cleaning',analysis:'analysis',visualization:'visualization',export:'visualization'};const cs=m[v];if(!cs)return;let fnd=false;document.querySelectorAll('.stepper-step').forEach(s=>{s.classList.remove('active','done');if(s.dataset.step===cs){s.classList.add('active');fnd=true;}else if(!fnd)s.classList.add('done');});this.state.currentStep=cs;},

    /* ========== 多文件上传 ========== */
    _bindUploadEvents(){document.getElementById('fileInput').addEventListener('change',()=>{if(document.getElementById('fileInput').files.length>0)this._handleMultipleUpload(document.getElementById('fileInput').files);document.getElementById('fileInput').value='';});},
    async _handleMultipleUpload(fileList){const files=Array.from(fileList);if(files.length===0)return;this._showLoading('上传 '+files.length+' 个文件...');let ok=0,fail=0;for(const file of files){try{const ext='.'+file.name.split('.').pop().toLowerCase();if(!['.csv','.xlsx','.xls'].includes(ext)){Utils.toast('跳过 '+file.name+': 格式不支持','warning');fail++;continue;}if(file.size>10*1024*1024){Utils.toast('跳过 '+file.name+': >10MB','warning');fail++;continue;}const r=await API.uploadFile(file);this._addFile(r);ok++;}catch(err){Utils.toast(file.name+' 失败: '+err.message,'error');fail++;}}this._hideLoading();if(ok>0)Utils.toast('成功上传 '+ok+' 个文件'+(fail>0?'，'+fail+' 个失败':''),'success');},

    /* ========== 数据清洗 ========== */
    _bindCleaningEvents(){
        document.getElementById('btnClean').addEventListener('click',()=>this._handleCleaning());
        const sel=document.getElementById('outlierMethod');sel.addEventListener('change',()=>{document.getElementById('hintIQR').style.display=sel.value==='iqr'?'block':'none';document.getElementById('hintZScore').style.display=sel.value==='zscore'?'block':'none';});
    },
    async _handleCleaning(){
        const aid=this._getActiveFileId();if(!aid){Utils.toast('请先在仪表盘选择文件','warning');return;}
        const fileIds=this.state.selectedIds.length>0?this.state.selectedIds:[aid];
        this._showLoading('清洗 '+fileIds.length+' 个文件...');let ok=0;
        for(const fid of fileIds){try{const params={file_id:fid,missing_method:document.getElementById('missingMethod').value,drop_duplicates:document.getElementById('dropDuplicates').checked,outlier_method:document.getElementById('outlierMethod').value};const r=await API.cleanData(params);this.state.files[fid].cleanedFileId=r.cleaned_file_id;this._markProgress(fid,'cleaning');ok++;if(fid===aid){this._showCleanResult(r,fid);await this._showCleanedDataTable(r.cleaned_file_id);await this._showDeletedRows(fid,r);}}catch(err){Utils.toast((this.state.files[fid]?.fileName||fid)+' 清洗失败: '+err.message,'error');}}this._hideLoading();if(ok>0)Utils.toast(ok+' 个文件清洗完成','success');this._refreshDashboard();this._updateStepper('cleaning');
    },
    _showCleanResult(r){
        document.getElementById('cleanEmpty').style.display='none';document.getElementById('cleanResultContent').style.display='block';
        document.getElementById('cleanOrigRows').textContent=r.original_shape?.[0]||'--';document.getElementById('cleanOrigMissing').textContent=r.original_missing||'--';document.getElementById('cleanOrigDup').textContent=r.original_duplicates||'--';
        document.getElementById('cleanNewRows').textContent=r.cleaned_shape?.[0]||'--';document.getElementById('cleanNewMissing').textContent=r.cleaned_missing||'--';document.getElementById('cleanNewDup').textContent=r.cleaned_duplicates||'--';
    },
    async _showCleanedDataTable(cfid){
        try{const r=await API.getAllData(cfid);if(r.data&&r.data.length>0){const cols=r.columns;document.getElementById('cleanedDataTable').innerHTML='<thead><tr><th>#</th>'+cols.map(c=>'<th>'+c+'</th>').join('')+'</tr></thead><tbody>'+r.data.map((row,i)=>'<tr><td style="color:var(--text-muted);font-size:0.8em">'+(i+1)+'</td>'+cols.map(c=>'<td>'+(row[c]!==null&&row[c]!==undefined?String(row[c]).slice(0,60):'')+'</td>').join('')+'</tr>').join('')+'</tbody>';document.getElementById('cleanedDataSection').style.display='block';}}catch(e){console.warn('Load cleaned data failed:',e);}
    },
    async _showDeletedRows(fid,cleanResult){
        // 获取原始数据，通过比较行数差异显示被删除的行
        try{
            const origData=await API.getAllData(fid);
            const cleanedData=await API.getAllData(cleanResult.cleaned_file_id);
            const origRows=origData.data||[];const cleanedRows=cleanedData.data||[];
            // 找出被删除的行（原始中有但清洗后没有的）
            const removed=[];let dupRemoved=cleanResult.original_duplicates||0;let missingRemoved=(cleanResult.original_missing||0)-(cleanResult.cleaned_missing||0);
            if(dupRemoved>0||missingRemoved>0||(origRows.length-cleanedRows.length)>0){
                const deletedCount=origRows.length-cleanedRows.length;
                const cols=origData.columns||[];
                document.getElementById('cleanDeletedTable').innerHTML='<thead><tr><th>#</th>'+cols.map(c=>'<th>'+c+'</th>').join('')+'</tr></thead><tbody><tr><td colspan="'+(cols.length+1)+'" style="padding:20px;color:var(--text-muted);text-align:center;">共计删除 <strong style="color:var(--danger)">'+deletedCount+'</strong> 行（重复行: '+dupRemoved+'，含缺失值行: '+missingRemoved+'）</td></tr></tbody>';
                document.getElementById('cleanDeletedSection').style.display='block';
            }
        }catch(e){console.warn('Show deleted rows failed:',e);}
    },

    /* ========== 数据分析 ========== */
    _bindAnalysisEvents(){
        document.querySelectorAll('.analysis-card').forEach(card=>{card.addEventListener('click',()=>this._openAnalysisMode(card.dataset.action));});
        document.getElementById('btnBackToModes').addEventListener('click',()=>{document.getElementById('analysisModeSelect').style.display='block';document.getElementById('analysisWorkPanel').style.display='none';this.state.currentAnalysisAction=null;});
    },
    _openAnalysisMode(action){
        const aid=this._getActiveFileId();if(!aid){Utils.toast('请先选择文件','warning');return;}
        this.state.currentAnalysisAction=action;document.getElementById('analysisModeSelect').style.display='none';document.getElementById('analysisWorkPanel').style.display='block';document.getElementById('analysisResultBody').innerHTML='<div class="empty-state-sm">配置参数后点击"开始分析"</div>';
        this._renderAnalysisParams(action,aid);
    },
    _renderAnalysisParams(action,fid){
        const cols=this.state.files[fid]?.columns||[];const numCols=this.state.files[fid]?.numericColumns||[];const catCols=cols.filter(c=>!numCols.includes(c));
        const panel=document.getElementById('analysisParams');let h='<h3>分析参数配置</h3>';
        switch(action){
        case'statistics':
            h+='<div class="param-group"><label class="form-label">选择要统计的列（勾选数值列）</label><div class="column-check-list" id="statsColList">'+numCols.map(c=>'<label class="column-check-item checked"><input type="checkbox" value="'+c+'" checked>'+c+'</label>').join('')+'</div></div>';
            h+='<p class="param-hint">将计算选中列的计数、均值、标准差、最小值、四分位数、最大值。</p>';
            h+='<div class="param-group"><label class="form-label checkbox-label"><input type="checkbox" id="statsAllNumeric" checked><span>自动选择全部数值列</span></label></div>';
            h+='<button class="btn-primary btn-block" id="btnRunAnalysis">开始描述性统计</button>';
            break;
        case'correlation':
            h+='<p class="param-hint">对全部数值列计算皮尔逊相关系数矩阵。系数 [-1,1]，正值正相关，负值负相关，绝对值越接近1越强。</p><p class="param-hint">数值列: '+numCols.map(c=>'<code>'+c+'</code>').join(', ')+'</p>';
            h+='<button class="btn-primary btn-block" id="btnRunAnalysis">开始相关性分析</button>';break;
        case'groupby':
            h+='<div class="param-group"><label class="form-label">分组列</label><select class="form-select" id="paramGroupCol">'+(catCols.length>0?catCols.map(c=>'<option value="'+c+'">'+c+'</option>').join(''):'<option>无分类列</option>')+'</select></div>';
            h+='<p class="param-hint">聚合列（自动使用全部数值列）: '+numCols.join(', ')+'</p>';
            h+='<button class="btn-primary btn-block" id="btnRunAnalysis">开始分组聚合</button>';break;
        case'cluster':
            h+=this._renderClusterParams(numCols);break;
        case'regression':
            h+='<div class="param-group"><label class="form-label">目标列（要预测的值）</label><select class="form-select" id="paramTarget">'+numCols.map(c=>'<option value="'+c+'">'+c+'</option>').join('')+'</select></div>';
            h+='<p class="param-hint">其他数值列作为特征预测目标列。R² 越接近1拟合越好。</p>';
            h+='<button class="btn-primary btn-block" id="btnRunAnalysis">开始回归分析</button>';break;
        case'anomaly':
            h+='<p class="param-hint">Isolation Forest 隔离森林算法检测异常点。可用列: '+numCols.join(', ')+'</p>';
            h+='<button class="btn-primary btn-block" id="btnRunAnalysis">开始异常检测</button>';break;
        }
        panel.innerHTML=h;
        // 统计列选择交互
        if(action==='statistics'){document.querySelectorAll('#statsColList .column-check-item').forEach(item=>{item.addEventListener('click',()=>{const cb=item.querySelector('input');cb.checked=!cb.checked;item.classList.toggle('checked',cb.checked);});});document.getElementById('statsAllNumeric').addEventListener('change',function(){document.querySelectorAll('#statsColList .column-check-item').forEach(item=>{const cb=item.querySelector('input');cb.checked=this.checked;item.classList.toggle('checked',this.checked);});});}
        if(action==='cluster'){document.querySelectorAll('#clusterAlgoList .column-check-item').forEach(item=>{item.addEventListener('click',(e)=>{e.preventDefault();if(e.target.tagName==='INPUT')return;const cb=item.querySelector('input');cb.checked=!cb.checked;item.classList.toggle('checked',cb.checked);});});document.querySelectorAll('#clusterFeatList .column-check-item').forEach(item=>{item.addEventListener('click',(e)=>{e.preventDefault();if(e.target.tagName==='INPUT')return;const cb=item.querySelector('input');cb.checked=!cb.checked;item.classList.toggle('checked',cb.checked);});});}
        const btn=document.getElementById('btnRunAnalysis');if(btn)btn.addEventListener('click',()=>this._runAnalysis(action));
    },
    async _runAnalysis(action){
        const aid=this._getActiveFileId();if(!aid)return;const fid=aid;const useId=this.state.files[fid]?.cleanedFileId||fid;const body=document.getElementById('analysisResultBody');const names={statistics:'描述性统计',correlation:'相关性分析',groupby:'分组聚合',cluster:'聚类分析',regression:'线性回归',anomaly:'异常检测'};
        this._showLoading('执行'+names[action]+'...');
        try{
            const reqBody={file_id:useId};
            if(action==='statistics'){const cols=[];document.querySelectorAll('#statsColList input:checked').forEach(cb=>cols.push(cb.value));if(cols.length>0)reqBody.columns=cols;}
            if(action==='groupby'){const g=document.getElementById('paramGroupCol');if(g&&g.value)reqBody.group_column=g.value;}
            if(action==='cluster'){
                const algos=[];
                document.querySelectorAll('#clusterAlgoList input:checked').forEach(cb=>algos.push(cb.value));
                if(algos.length>0)reqBody.algorithms=algos;
                else reqBody.algorithms=['kmeans'];
                // 收集选择的特征列
                const feats=[];
                document.querySelectorAll('#clusterFeatList input:checked').forEach(cb=>feats.push(cb.value));
                if(feats.length>0)reqBody.features=feats;
                const k=document.getElementById('paramNClusters');
                if(k)reqBody.n_clusters=parseInt(k.value)||3;
                reqBody.params={};
                for(const a of algos){
                    reqBody.params[a]={};
                    if(a==='kmeans'||a==='kmedoids'||a==='agnes'||a==='gmm'){
                        reqBody.params[a].n_clusters=reqBody.n_clusters;
                        if(a==='gmm')reqBody.params[a].n_components=reqBody.n_clusters;
                    }
                    if(a==='optics'){
                        const ms=document.getElementById('opticsMinSamples');
                        reqBody.params[a].min_samples=ms?parseInt(ms.value)||5:5;
                    }
                    if(a==='agnes'){
                        const lk=document.getElementById('agnesLinkage');
                        reqBody.params[a].linkage=lk?lk.value:'ward';
                    }
                    if(a==='gmm'){
                        const ct=document.getElementById('gmmCovType');
                        reqBody.params[a].covariance_type=ct?ct.value:'full';
                    }
                }
            }
            if(action==='regression'){const t=document.getElementById('paramTarget');if(t&&t.value)reqBody.target=t.value;}
            const r=await API.runAnalysis(action,useId,reqBody);this._markProgress(fid,'analysis');this._renderAnalysisResult(action,r,body);this._updateStepper('analysis');this._refreshDashboard();
        }catch(err){body.innerHTML='<div class="empty-state-sm" style="color:var(--danger)">分析失败: '+err.message+'</div>';}
        finally{this._hideLoading();}
    },
    _renderAnalysisResult(action,r,body){
        switch(action){
        case'statistics':this._renderStatisticsResult(r,body);break;
        case'correlation':this._renderCorrelationResult(r,body);break;
        case'groupby':this._renderGroupbyResult(r,body);break;
        case'cluster':this._renderClusterResult(r,body);break;
        case'regression':this._renderRegressionResult(r,body);break;
        case'anomaly':this._renderAnomalyResult(r,body);break;
        }
    },

    /* --- 统计结果渲染 --- */
    _renderStatisticsResult(r,body){
        if(!r.statistics){body.innerHTML='<div class="empty-state-sm">无统计数据</div>';return;}
        const st=r.statistics;
        let h='<div class="analysis-summary"><strong>描述性统计结果</strong><br>';
        if(st.overall){
            h+='<small>总行数: '+st.overall.total_rows+' · 总列数: '+st.overall.total_columns+' · 数值列: '+st.overall.numeric_columns+' · 分类列: '+st.overall.categorical_columns+' · 总缺失值: '+st.overall.total_missing+' · 重复行: '+st.overall.total_duplicates+' · 内存: '+st.overall.memory_usage_mb+'MB</small>';
        }
        h+='</div>';

        // 数值列统计表
        if(st.numeric&&Object.keys(st.numeric).length>0){
            const numCols=Object.keys(st.numeric);
            const metrics=['count','mean','std','min','25%','50%','75%','max','variance','skewness','kurtosis','unique','missing','missing_pct'];
            const labels={count:'计数',mean:'均值',std:'标准差',min:'最小值','25%':'Q1(25%)','50%':'中位数(50%)','75%':'Q3(75%)',max:'最大值',variance:'方差',skewness:'偏度',kurtosis:'峰度',unique:'唯一值',missing:'缺失值',missing_pct:'缺失率%'};
            h+='<h4 style="margin:16px 0 8px;color:var(--neon-primary);">📊 数值列统计</h4>';
            h+='<div class="table-scroll"><table class="data-table"><thead><tr><th>指标</th>'+numCols.map(c=>'<th>'+c+'</th>').join('')+'</tr></thead><tbody>';
            for(const m of metrics){
                h+='<tr><td><strong>'+labels[m]+'</strong></td>';
                for(const c of numCols){
                    const val=st.numeric[c][m];
                    if(m==='missing_pct'&&val!==undefined)h+='<td>'+(val>0?'<span style="color:var(--danger)">'+val+'%</span>':val+'%')+'</td>';
                    else h+='<td>'+(val!==undefined?Number(val).toFixed(4):'--')+'</td>';
                }
                h+='</tr>';
            }
            h+='</tbody></table></div>';
        }

        // 分类列统计表
        if(st.categorical&&Object.keys(st.categorical).length>0){
            const catCols=Object.keys(st.categorical);
            const catMetrics=['count','unique','top','freq','missing','missing_pct'];
            const catLabels={count:'总数',unique:'唯一值数',top:'众数',freq:'众数频次',missing:'缺失值',missing_pct:'缺失率%'};
            h+='<h4 style="margin:16px 0 8px;color:var(--neon-cyan);">📋 分类列统计</h4>';
            h+='<div class="table-scroll"><table class="data-table"><thead><tr><th>指标</th>'+catCols.map(c=>'<th>'+c+'</th>').join('')+'</tr></thead><tbody>';
            for(const m of catMetrics){
                h+='<tr><td><strong>'+catLabels[m]+'</strong></td>';
                for(const c of catCols){
                    const val=st.categorical[c][m];
                    h+='<td>'+(val!==undefined&&val!==null?String(val).slice(0,40):'--')+'</td>';
                }
                h+='</tr>';
            }
            h+='</tbody></table></div>';
        }
        body.innerHTML=h;
    },

    /* --- 相关性结果渲染（使用列名而非数字索引） --- */
    _renderCorrelationResult(r,body){
        const colNames=r.column_names||[];
        const matrix=r.correlation_matrix||[];
        if(colNames.length===0||matrix.length===0){body.innerHTML='<div class="empty-state-sm">相关性数据为空</div>';return;}

        // 构建 dict-of-dicts 格式供摘要和表格使用
        const corrDict={};
        for(let i=0;i<colNames.length;i++){
            corrDict[colNames[i]]={};
            for(let j=0;j<colNames.length;j++){
                corrDict[colNames[i]][colNames[j]]=matrix[i][j];
            }
        }

        // 摘要：找出强相关对
        let h='<div class="analysis-summary"><strong>相关性分析结果</strong><br>';
        const pairs=[];
        for(let i=0;i<colNames.length;i++){
            for(let j=i+1;j<colNames.length;j++){
                const v=matrix[i][j];
                pairs.push({a:colNames[i],b:colNames[j],v:Math.abs(v),raw:v});
            }
        }
        pairs.sort((a,b)=>b.v-a.v);
        for(const p of pairs.slice(0,8)){
            const d=p.v>0.7?'强'+(p.raw>0?'正':'负')+'相关':p.v>0.4?'中等'+(p.raw>0?'正':'负')+'相关':'弱相关';
            h+='<em>'+p.a+'</em> 与 <em>'+p.b+'</em>: '+p.raw.toFixed(3)+' ('+d+')<br>';
        }
        h+='</div>';

        // 相关性矩阵表格
        h+='<div class="table-scroll" style="margin-top:12px;"><table class="data-table"><thead><tr><th></th>'+colNames.map(c=>'<th>'+c+'</th>').join('')+'</tr></thead><tbody>';
        for(let i=0;i<colNames.length;i++){
            h+='<tr><td><strong>'+colNames[i]+'</strong></td>';
            for(let j=0;j<colNames.length;j++){
                const v=matrix[i][j];
                const color=Math.abs(v)>0.7?'var(--neon-accent)':Math.abs(v)>0.4?'var(--neon-cyan)':'inherit';
                h+='<td style="color:'+color+'">'+v.toFixed(3)+'</td>';
            }
            h+='</tr>';
        }
        h+='</tbody></table></div>';

        // 如果有强相关列表，也显示
        if(r.strong_correlations&&r.strong_correlations.length>0){
            h+='<h4 style="margin:12px 0 8px;color:var(--neon-pink);">🔗 强相关对 (|r|≥0.5)</h4>';
            h+='<div class="table-scroll"><table class="data-table"><thead><tr><th>列1</th><th>列2</th><th>相关系数</th><th>强度</th><th>方向</th></tr></thead><tbody>';
            for(const sc of r.strong_correlations){
                h+='<tr><td>'+sc.pair[0]+'</td><td>'+sc.pair[1]+'</td><td style="color:var(--neon-accent)">'+sc.correlation+'</td><td>'+sc.strength+'</td><td>'+sc.direction+'</td></tr>';
            }
            h+='</tbody></table></div>';
        }
        body.innerHTML=h;
    },

    /* --- 分组聚合结果渲染（表格化） --- */
    _renderGroupbyResult(r,body){
        const gr=r.groupby_result||r;
        if(!gr||!gr.groups||gr.groups.length===0){body.innerHTML='<div class="empty-state-sm">分组聚合结果为空</div>';return;}
        const groups=gr.groups||[];
        const aggs=gr.aggregations||{};
        const groupCol=gr.group_column||'分组';
        let h='<div class="analysis-summary"><strong>分组聚合完成</strong><br>分组列: <em>'+groupCol+'</em> · 共 '+groups.length+' 个分组</div>';

        // 为每个聚合列生成一个表格
        for(const [col, funcs] of Object.entries(aggs)){
            const funcNames=Object.keys(funcs);
            h+='<h4 style="margin:16px 0 8px;color:var(--neon-primary);">📊 '+col+' 聚合结果</h4>';
            h+='<div class="table-scroll"><table class="data-table"><thead><tr><th>'+groupCol+'</th>'+funcNames.map(f=>'<th>'+f+'</th>').join('')+'</tr></thead><tbody>';
            for(let i=0;i<groups.length;i++){
                h+='<tr><td><strong>'+groups[i]+'</strong></td>';
                for(const f of funcNames){
                    const val=funcs[f][i];
                    h+='<td>'+(val!==null&&val!==undefined?Number(val).toFixed(4):'--')+'</td>';
                }
                h+='</tr>';
            }
            h+='</tbody></table></div>';
        }
        body.innerHTML=h;
    },

    /* --- 聚类参数配置 UI --- */
    _renderClusterParams(numCols){
        let h='<p class="param-hint">可用数值列: '+numCols.map(c=>'<code>'+c+'</code>').join(', ')+'</p>';

        // 量化指标说明（提前展示）
        h+='<div class="metrics-preview glass-card-dark" style="padding:12px 14px;margin-bottom:14px;border-radius:8px;">';
        h+='<strong style="color:var(--neon-primary);font-size:0.85em;">📐 算法评估量化指标（运行后对比）</strong>';
        h+='<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:8px;font-size:0.78em;color:var(--text-muted);">';
        h+='<div><strong style="color:var(--neon-cyan);">轮廓系数 ↑</strong> [-1,1] 越接近1簇越紧密</div>';
        h+='<div><strong style="color:var(--neon-accent);">CH指数 ↑</strong> 越大类间分离越好</div>';
        h+='<div><strong style="color:var(--neon-pink);">DB指数 ↓</strong> 越小类内越紧密</div>';
        h+='<div><strong style="color:var(--warning);">算法特指</strong> 惯性/距离/BIC/AIC</div>';
        h+='</div></div>';

        // 算法选择
        h+='<div class="param-group"><label class="form-label">选择聚类算法（可多选，至少选1个）</label>';
        h+='<div class="column-check-list" id="clusterAlgoList">';
        const algos=[
            {key:'kmeans',name:'K-Means',desc:'基于距离的划分聚类，快速高效，适合球形簇',icon:'🎯'},
            {key:'kmedoids',name:'K-Medoids (PAM)',desc:'使用实际数据点作为中心，对异常值更鲁棒',icon:'💊'},
            {key:'optics',name:'OPTICS',desc:'基于密度的聚类，自动发现不同密度的簇，无需预设K值',icon:'👁️'},
            {key:'agnes',name:'AGNES 层次聚类',desc:'自底向上合并，生成层次树状结构',icon:'🌳'},
            {key:'gmm',name:'GMM 高斯混合',desc:'软聚类概率模型，支持椭圆状分布簇',icon:'🔮'},
        ];
        for(const a of algos){
            h+='<label class="column-check-item checked" style="flex-direction:column;align-items:flex-start;padding:10px 12px;gap:4px;"><div style="display:flex;align-items:center;gap:8px;"><input type="checkbox" value="'+a.key+'" checked><strong>'+a.name+'</strong><span style="font-size:1.2em">'+a.icon+'</span></div><small style="color:var(--text-muted);margin-left:24px;">'+a.desc+'</small></label>';
        }
        h+='</div></div>';

        // 特征列选择
        h+='<div class="param-group"><label class="form-label">选择聚类特征列（留空则自动使用全部数值列）</label>';
        h+='<div class="column-check-list" id="clusterFeatList">'+numCols.map(c=>'<label class="column-check-item"><input type="checkbox" value="'+c+'">'+c+'</label>').join('')+'</div></div>';

        // 通用参数
        h+='<div class="param-group"><label class="form-label">聚类数 K（K-Means/K-Medoids/AGNES/GMM）</label><input type="number" class="form-input" id="paramNClusters" value="3" min="1" max="20"></div>';

        // OPTICS 参数
        h+='<div class="param-group"><label class="form-label">OPTICS 最小样本数</label><input type="number" class="form-input" id="opticsMinSamples" value="5" min="2" max="100"><p class="param-hint">邻域内最少点数，值越大对噪声越敏感</p></div>';

        // AGNES 参数
        h+='<div class="param-group"><label class="form-label">AGNES 链接方式</label><select class="form-select" id="agnesLinkage"><option value="ward">Ward（最小方差）</option><option value="complete">Complete（最远距离）</option><option value="average">Average（平均距离）</option><option value="single">Single（最近距离）</option></select></div>';

        // GMM 参数
        h+='<div class="param-group"><label class="form-label">GMM 协方差类型</label><select class="form-select" id="gmmCovType"><option value="full">Full（完全协方差）</option><option value="tied">Tied（相同协方差）</option><option value="diag">Diagonal（对角协方差）</option><option value="spherical">Spherical（球形协方差）</option></select></div>';

        h+='<button class="btn-primary btn-block" id="btnRunAnalysis">开始聚类分析</button>';
        return h;
    },

    /* --- 聚类结果渲染（兼容新旧格式） --- */
    _renderClusterResult(r,body){
        if(!r.cluster_result){body.innerHTML='<div class="empty-state-sm">聚类结果为空</div>';return;}
        const cr=r.cluster_result;

        // 检测新格式（multi_clustering）还是旧格式（单 kmeans）
        if(cr.comparison&&cr.results){
            // 新格式：多算法对比
            this._renderMultiClusterResult(cr,body);
        }else{
            // 旧格式：单算法，包装成多算法格式显示
            const algoName=cr.algorithm||'K-Means';
            const fakeResult={};
            fakeResult['kmeans']=cr;
            const wrapped={
                comparison:[{
                    algorithm:algoName,key:'kmeans',n_clusters:cr.n_clusters||cr.n_components,
                    silhouette_score:cr.silhouette_score,calinski_harabasz_score:cr.calinski_harabasz_score,
                    davies_bouldin_score:cr.davies_bouldin_score,inertia:cr.inertia,
                }],
                results:fakeResult,
                best_by_silhouette:algoName,
            };
            this._renderMultiClusterResult(wrapped,body);
        }
    },

    _renderMultiClusterResult(cr,body){
        const comparison=cr.comparison||[];
        const results=cr.results||{};

        let h='<div class="analysis-summary"><strong>聚类分析完成</strong><br>';
        h+='共运行 <em>'+comparison.length+'</em> 个算法';
        if(cr.best_by_silhouette)h+=' · 最佳轮廓系数: <em style="color:var(--neon-accent)">'+cr.best_by_silhouette+'</em>';
        if(cr.best_by_calinski_harabasz)h+=' · 最佳CH指数: <em style="color:var(--neon-cyan)">'+cr.best_by_calinski_harabasz+'</em>';
        if(cr.best_by_davies_bouldin)h+=' · 最佳DB指数: <em style="color:var(--neon-pink)">'+cr.best_by_davies_bouldin+'</em>';
        h+='</div>';

        // ===== 对比总表（作为主视图） =====
        if(comparison.length>0){
            h+='<div id="clusterComparisonSection">';
            h+='<h4 style="margin:16px 0 8px;color:var(--neon-primary);">📊 多算法量化对比总表</h4>';
            const metricCols=['algorithm','n_clusters','silhouette_score','calinski_harabasz_score','davies_bouldin_score'];
            // 检测是否有算法特有指标
            for(const c of comparison){
                for(const k of ['inertia','total_distance','n_noise','bic','aic']){
                    if(c[k]!==undefined&&!metricCols.includes(k))metricCols.push(k);
                }
            }
            const colLabels={algorithm:'算法',n_clusters:'聚类数',silhouette_score:'轮廓系数 ↑',calinski_harabasz_score:'CH指数 ↑',davies_bouldin_score:'DB指数 ↓',inertia:'惯性(SSE) ↓',total_distance:'总距离 ↓',n_noise:'噪声点数',bic:'BIC ↓',aic:'AIC ↓'};

            h+='<div class="table-scroll"><table class="data-table cluster-compare-table"><thead><tr>'+metricCols.map(m=>'<th>'+((colLabels[m])||m)+'</th>').join('')+'<th>评级</th></tr></thead><tbody>';
            for(const c of comparison){
                if(c.error){h+='<tr><td colspan="'+(metricCols.length+1)+'" style="color:var(--danger)">❌ '+c.algorithm+': '+c.error+'</td></tr>';continue;}
                // Calculate grade
                let grade='--',gradeColor='inherit';
                const sil=c.silhouette_score;
                if(sil!==null&&sil!==undefined){
                    if(sil>0.7){grade='A+';gradeColor='var(--success)';}
                    else if(sil>0.5){grade='A';gradeColor='var(--success)';}
                    else if(sil>0.3){grade='B';gradeColor='var(--warning)';}
                    else if(sil>0.1){grade='C';gradeColor='var(--danger)';}
                    else{grade='D';gradeColor='var(--danger)';}
                }
                h+='<tr>'+metricCols.map(m=>{
                    const v=c[m];
                    if(v===undefined||v===null)return'<td>--</td>';
                    if(m==='silhouette_score'){
                        const color=v>0.5?'var(--success)':v>0.3?'var(--warning)':'var(--danger)';
                        return'<td style="color:'+color+';font-weight:600;">'+Number(v).toFixed(4)+'</td>';
                    }
                    if(m==='davies_bouldin_score'){
                        const color=v<1?'var(--success)':v<2?'var(--warning)':'var(--danger)';
                        return'<td style="color:'+color+';font-weight:600;">'+Number(v).toFixed(4)+'</td>';
                    }
                    if(m==='calinski_harabasz_score'){
                        return'<td style="font-weight:600;">'+Number(v).toFixed(2)+'</td>';
                    }
                    if(typeof v==='number')return'<td>'+Number(v).toFixed(4)+'</td>';
                    return'<td>'+v+'</td>';
                }).join('')+'<td style="color:'+gradeColor+';font-weight:700;font-size:1.1em;">'+grade+'</td></tr>';
            }
            h+='</tbody></table></div>';

            // 最佳算法高亮卡片
            h+='<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:10px;">';
            if(cr.best_by_silhouette)h+='<div class="best-algo-card" style="border-left:3px solid var(--success);"><small style="color:var(--text-muted);">🏆 轮廓系数最佳</small><strong style="color:var(--success);">'+cr.best_by_silhouette+'</strong></div>';
            if(cr.best_by_calinski_harabasz)h+='<div class="best-algo-card" style="border-left:3px solid var(--neon-cyan);"><small style="color:var(--text-muted);">🏆 CH指数最佳</small><strong style="color:var(--neon-cyan);">'+cr.best_by_calinski_harabasz+'</strong></div>';
            if(cr.best_by_davies_bouldin)h+='<div class="best-algo-card" style="border-left:3px solid var(--neon-accent);"><small style="color:var(--text-muted);">🏆 DB指数最佳</small><strong style="color:var(--neon-accent);">'+cr.best_by_davies_bouldin+'</strong></div>';
            h+='</div>';

            h+='<div class="analysis-summary" style="margin-top:8px;"><small><strong>📐 指标解读:</strong> <span style="color:var(--success);">轮廓系数</span> [-1,1] 越接近1簇越紧密；<span style="color:var(--neon-cyan);">CH指数</span> 越大类间分离越好；<span style="color:var(--danger);">DB指数</span> 越小类内越紧密；<span style="color:var(--warning);">评级</span> 综合评估算法适用性</small></div>';
            h+='</div>'; // end clusterComparisonSection
        }

        // ===== 各算法详情（通过按钮切换） =====
        const algoKeys=Object.keys(results);
        if(algoKeys.length>0){
            h+='<div id="clusterDetailSection" style="display:none;">';
            h+='<div style="display:flex;align-items:center;gap:10px;margin:20px 0 8px;flex-wrap:wrap;">';
            h+='<button class="btn-sm" id="btnBackToCompare" style="border-color:rgba(99,102,241,0.4);color:var(--neon-primary);">← 返回对比总表</button>';
            h+='<span style="color:var(--text-muted);font-size:0.82em;">切换查看各算法详情：</span>';
            h+='<div class="cluster-detail-tabs" style="display:flex;gap:6px;flex-wrap:wrap;" id="clusterDetailTabs">';
            let first=true;
            for(const ak of algoKeys){
                const ar=results[ak];
                const name=(ar&&ar.algorithm)||ak;
                h+='<button class="cluster-tab-btn'+(first?' active':'')+'" data-cluster-tab="'+ak+'">'+name+'</button>';
                first=false;
            }
            h+='</div></div>';
            let firstTab=true;
            for(const ak of algoKeys){
                const ar=results[ak];
                if(!ar)continue;
                const name=ar.algorithm||ak;
                h+='<div class="cluster-tab-content" id="clusterTab-'+ak+'" style="display:'+(firstTab?'block':'none')+';">';
                h+=this._renderSingleClusterDetail(ar,name);
                h+='</div>';
                firstTab=false;
            }
            h+='</div>'; // end clusterDetailSection

            // 查看详情按钮（在对比表下方）
            h+='<div style="margin-top:12px;text-align:center;" id="btnViewDetailsWrap">';
            h+='<button class="btn-primary" id="btnViewAlgoDetails" style="font-size:0.9em;">📋 查看各算法详情</button>';
            h+='</div>';
        }
        body.innerHTML=h;

        // 绑定：查看详情 / 返回对比
        const btnView=body.querySelector('#btnViewAlgoDetails');
        const btnBack=body.querySelector('#btnBackToCompare');
        const compSection=body.querySelector('#clusterComparisonSection');
        const detailSection=body.querySelector('#clusterDetailSection');
        const btnWrap=body.querySelector('#btnViewDetailsWrap');
        if(btnView){btnView.addEventListener('click',()=>{
            if(compSection)compSection.style.display='none';
            if(detailSection)detailSection.style.display='block';
            if(btnWrap)btnWrap.style.display='none';
        });}
        if(btnBack){btnBack.addEventListener('click',()=>{
            if(compSection)compSection.style.display='block';
            if(detailSection)detailSection.style.display='none';
            if(btnWrap)btnWrap.style.display='block';
        });}

        // 绑定算法详情Tab切换事件
        body.querySelectorAll('.cluster-tab-btn').forEach(btn=>{
            btn.addEventListener('click',()=>{
                body.querySelectorAll('.cluster-tab-btn').forEach(b=>b.classList.remove('active'));
                btn.classList.add('active');
                body.querySelectorAll('.cluster-tab-content').forEach(c=>c.style.display='none');
                const tab=document.getElementById('clusterTab-'+btn.dataset.clusterTab);
                if(tab)tab.style.display='block';
            });
        });
    },

    /* --- 单个聚类算法详情渲染 --- */
    _renderSingleClusterDetail(ar,name){
        let h='<h5 style="color:var(--text-primary);margin:0 0 8px;">'+name+' 详情</h5>';
        // 基本指标
        h+='<div class="analysis-summary" style="margin-bottom:8px;">';
        const metrics=[];
        if(ar.n_clusters!==undefined)metrics.push('聚类数: '+ar.n_clusters);
        if(ar.silhouette_score!==null&&ar.silhouette_score!==undefined)metrics.push('轮廓系数: '+ar.silhouette_score);
        if(ar.calinski_harabasz_score!==null&&ar.calinski_harabasz_score!==undefined)metrics.push('CH指数: '+ar.calinski_harabasz_score);
        if(ar.davies_bouldin_score!==null&&ar.davies_bouldin_score!==undefined)metrics.push('DB指数: '+ar.davies_bouldin_score);
        if(ar.inertia!==undefined)metrics.push('惯性: '+ar.inertia);
        if(ar.total_distance!==undefined)metrics.push('总距离: '+ar.total_distance);
        if(ar.n_noise!==undefined)metrics.push('噪声点: '+ar.n_noise);
        if(ar.bic!==undefined)metrics.push('BIC: '+ar.bic);
        if(ar.aic!==undefined)metrics.push('AIC: '+ar.aic);
        if(ar.weights)metrics.push('权重: '+ar.weights.join(', '));
        if(ar.linkage)metrics.push('链接: '+ar.linkage);
        if(ar.covariance_type)metrics.push('协方差: '+ar.covariance_type);
        h+=metrics.join(' · ')+'</div>';

        // 簇中心表
        if(ar.cluster_centers&&ar.cluster_centers.length>0){
            const features=ar.features||Object.keys(ar.cluster_centers[0]).filter(k=>k!=='cluster');
            h+='<div class="table-scroll"><table class="data-table"><thead><tr><th>簇</th>'+features.map(f=>'<th>'+f+'</th>').join('')+'<th>样本数</th></tr></thead><tbody>';
            for(let i=0;i<ar.cluster_centers.length;i++){
                const c=ar.cluster_centers[i];
                const clabel=c.cluster!==undefined?c.cluster:i;
                h+='<tr><td><strong>簇 '+clabel+'</strong></td>';
                for(const f of features)h+='<td>'+Number(c[f]||0).toFixed(4)+'</td>';
                h+='<td>'+(ar.cluster_sizes?.[clabel]||ar.cluster_sizes?.[i]||'--')+'</td>';
                h+='</tr>';
            }
            h+='</tbody></table></div>';
        }

        // 簇大小分布
        if(ar.cluster_sizes){
            h+='<div class="table-scroll" style="margin-top:8px;"><table class="data-table"><thead><tr><th>簇</th><th>样本数</th><th>占比</th></tr></thead><tbody>';
            const sizes=ar.cluster_sizes;
            const total=Object.values(sizes).reduce((a,b)=>a+b,0);
            for(const [k,v] of Object.entries(sizes)){
                h+='<tr><td>簇 '+k+'</td><td>'+v+'</td><td>'+(total>0?(v/total*100).toFixed(1)+'%':'--')+'</td></tr>';
            }
            h+='</tbody></table></div>';
        }
        return h;
    },

    /* --- 回归结果渲染 --- */
    _renderRegressionResult(r,body){
        if(!r.regression_result){body.innerHTML='<div class="empty-state-sm">回归结果为空</div>';return;}
        const rr=r.regression_result;
        const r2=rr.r2_score!==undefined?rr.r2_score:(rr.R2||null);
        let h='<div class="analysis-summary"><strong>线性回归完成</strong><br>';
        h+='R²: <em>'+(r2!==null?Number(r2).toFixed(4):'?')+'</em>（越接近1拟合越好）<br>';
        h+='截距: '+(rr.intercept!==undefined?Number(rr.intercept).toFixed(4):'?')+' · MSE: '+(rr.mse||'?')+' · RMSE: '+(rr.rmse||'?')+' · 训练R²: '+(rr.train_r2!==undefined?Number(rr.train_r2).toFixed(4):'?');
        h+='</div>';

        // 系数表
        if(rr.coefficients){
            h+='<h4 style="margin:16px 0 8px;color:var(--neon-primary);">📈 特征系数（对 '+rr.target+' 的影响）</h4>';
            h+='<div class="table-scroll"><table class="data-table"><thead><tr><th>特征</th><th>系数</th><th>重要性</th><th>影响方向</th></tr></thead><tbody>';
            const fi=rr.feature_importance||{};
            for(const [feat,coef] of Object.entries(rr.coefficients)){
                const imp=fi[feat]!==undefined?Number(fi[feat]).toFixed(4):'--';
                const dir=coef>0?'↑ 正影响':'↓ 负影响';
                h+='<tr><td>'+feat+'</td><td>'+Number(coef).toFixed(6)+'</td><td>'+imp+'</td><td>'+dir+'</td></tr>';
            }
            h+='</tbody></table></div>';
        }
        body.innerHTML=h;
    },

    /* --- 异常检测结果渲染 --- */
    _renderAnomalyResult(r,body){
        if(!r.anomaly_result){body.innerHTML='<div class="empty-state-sm">异常检测结果为空</div>';return;}
        const ar=r.anomaly_result;
        let h='<div class="analysis-summary"><strong>异常检测完成（Isolation Forest）</strong><br>';
        h+='总样本: <em>'+ar.total_samples+'</em> · 异常点: <em style="color:var(--danger);font-size:1.1em;">'+ar.anomaly_count+'</em> · 异常率: <em style="color:var(--warning);">'+ar.anomaly_ratio+'%</em>';
        h+='</div>';

        // 显示 IQR 边界信息
        if(ar.col_iqr_bounds&&Object.keys(ar.col_iqr_bounds).length>0){
            h+='<h4 style="margin:16px 0 8px;color:var(--neon-cyan);">📏 各列 IQR 正常范围（用于判断异常原因）</h4>';
            h+='<div class="table-scroll"><table class="data-table"><thead><tr><th>列名</th><th>Q1</th><th>Q3</th><th>IQR</th><th>正常下限</th><th>正常上限</th></tr></thead><tbody>';
            for(const [col,bounds] of Object.entries(ar.col_iqr_bounds)){
                h+='<tr><td><strong>'+col+'</strong></td><td>'+bounds.Q1+'</td><td>'+bounds.Q3+'</td><td>'+bounds.IQR+'</td><td>'+bounds.lower+'</td><td>'+bounds.upper+'</td></tr>';
            }
            h+='</tbody></table></div>';
        }

        // 显示异常行详情表（主视图）
        if(ar.anomaly_rows&&ar.anomaly_rows.length>0){
            h+='<h4 style="margin:16px 0 8px;color:var(--danger);">⚠️ 异常数据行详情（共 '+ar.anomaly_count+' 条异常，显示前 '+ar.anomaly_rows.length+' 条）</h4>';

            // 收集所有列名
            const allCols=new Set();
            for(const row of ar.anomaly_rows){
                if(row.data)Object.keys(row.data).forEach(c=>allCols.add(c));
            }
            const cols=Array.from(allCols);
            const displayCols=cols.slice(0,10); // 最多显示10列数据
            const hasMore=cols.length>10;

            // 构建表头：序号 | 原始索引 | 异常分数 | 数据列... | 异常原因
            h+='<div class="table-scroll"><table class="data-table anomaly-detail-table"><thead><tr>';
            h+='<th style="min-width:36px;">#</th>';
            h+='<th style="min-width:50px;">原始行号</th>';
            h+='<th style="min-width:70px;">异常分数</th>';
            for(const c of displayCols)h+='<th>'+c+'</th>';
            h+='<th style="min-width:200px;">🔍 异常原因</th></tr></thead><tbody>';

            for(let ri=0;ri<ar.anomaly_rows.length;ri++){
                const row=ar.anomaly_rows[ri];
                // 构建异常原因描述
                const reasons=[];
                if(row.outlier_columns&&row.outlier_columns.length>0){
                    for(const oc of row.outlier_columns){
                        const dir=oc.value>oc.upper_bound?'偏高':'偏低';
                        reasons.push('<span style="color:var(--danger);">'+oc.column+'</span>='+oc.value+' <span style="color:var(--warning);">'+dir+'</span> (正常范围['+oc.lower_bound+','+oc.upper_bound+'])');
                    }
                }
                if(reasons.length===0)reasons.push('<span style="color:var(--text-muted);">多维异常（综合偏离正常分布）</span>');

                // 分数颜色
                const score=row.score!==undefined?Number(row.score):0;
                const scoreColor=score>0.7?'var(--danger)':score>0.4?'var(--warning)':'var(--text-secondary)';

                h+='<tr style="background:rgba(239,68,68,'+(0.04+score*0.08)+');">';
                h+='<td style="color:var(--danger);font-weight:600;">'+(ri+1)+'</td>';
                h+='<td style="color:var(--danger);font-weight:600;">'+(row.index!==undefined?row.index:'--')+'</td>';
                h+='<td style="color:'+scoreColor+';font-weight:600;">'+score.toFixed(4)+'</td>';
                for(const c of displayCols){
                    const v=row.data?.[c];
                    if(v===null||v===undefined)h+='<td style="color:var(--text-muted);">--</td>';
                    else{
                        // 检查是否是异常列
                        const isOutlier=row.outlier_columns&&row.outlier_columns.some(o=>o.column===c);
                        const style=isOutlier?'color:var(--danger);font-weight:600;':'';
                        h+='<td style="'+style+'">'+String(v).slice(0,50)+'</td>';
                    }
                }
                h+='<td style="font-size:0.78em;line-height:1.5;max-width:280px;white-space:normal;">'+reasons.join('<br>')+'</td>';
                h+='</tr>';
            }
            h+='</tbody></table></div>';
            if(hasMore)h+='<p style="color:var(--text-muted);font-size:0.8em;">⚠ 仅显示前10列数据，完整数据含'+cols.length+'列。超出100条的异常仅显示前100条。</p>';
        }else if(ar.anomaly_indices&&ar.anomaly_indices.length>0){
            // 旧格式兼容：只有索引没有行数据
            h+='<h4 style="margin:16px 0 8px;color:var(--danger);">⚠️ 异常数据行索引（共 '+ar.anomaly_count+' 条）</h4>';
            h+='<div class="table-scroll"><table class="data-table"><thead><tr><th>#</th><th>原始行号</th><th>异常分数</th></tr></thead><tbody>';
            const indices=ar.anomaly_indices.slice(0,100);
            const scores=ar.anomaly_scores||[];
            for(let i=0;i<indices.length;i++){
                const score=scores[i]!==undefined?Number(scores[i]).toFixed(4):'--';
                h+='<tr style="background:rgba(239,68,68,0.06);"><td>'+(i+1)+'</td><td style="color:var(--danger);">'+indices[i]+'</td><td>'+score+'</td></tr>';
            }
            h+='</tbody></table></div>';
            if(ar.anomaly_indices.length>100)h+='<p style="color:var(--text-muted);font-size:0.8em;">仅显示前100条，共'+ar.anomaly_indices.length+'条异常</p>';
            h+='<p style="color:var(--text-muted);font-size:0.82em;margin-top:8px;">💡 提示：后端返回了旧格式数据，建议重新运行分析以获取详细异常信息。</p>';
        }else{
            h+='<div class="empty-state-sm">未检测到异常数据行</div>';
        }
        body.innerHTML=h;
    },

    _genStatsSummary(stats,cols){let h='<div class="analysis-summary"><strong>描述性统计结果</strong><br>';for(const c of cols.slice(0,8)){const s=stats[c];if(!s)continue;h+='<em>'+c+'</em>: 均值='+Number(s.mean||0).toFixed(2)+', 标准差='+Number(s.std||0).toFixed(2)+', 范围=['+s.min+', '+s.max+']<br>';}h+='</div>';return h;},
    _genCorrSummary(matrix,cols){let h='<div class="analysis-summary"><strong>相关性分析结果</strong><br>';const pairs=[];for(let i=0;i<cols.length;i++)for(let j=i+1;j<cols.length;j++){const v=matrix[cols[i]][cols[j]];pairs.push({a:cols[i],b:cols[j],v:Math.abs(v),raw:v});}pairs.sort((a,b)=>b.v-a.v);for(const p of pairs.slice(0,5)){const d=p.v>0.7?'强'+(p.raw>0?'正':'负')+'相关':p.v>0.4?'中等'+(p.raw>0?'正':'负')+'相关':'弱相关';h+='<em>'+p.a+'</em> 与 <em>'+p.b+'</em>: '+p.raw.toFixed(3)+' ('+d+')<br>';}h+='</div>';return h;},

    /* ========== 可视化 + CRUD ========== */
    _bindVisualizationEvents(){
        document.getElementById('chartType').addEventListener('change',()=>this._updateYColumnList());
        document.getElementById('btnGenerateChart').addEventListener('click',()=>this._handleVisualization());
        document.getElementById('btnClearChart').addEventListener('click',()=>this._clearChart());
        document.getElementById('btnVizExportChart').addEventListener('click',()=>this._exportChartPNG());
        document.getElementById('btnVizExportData').addEventListener('click',()=>this._handleExport('data'));
        document.getElementById('btnVizExportReport').addEventListener('click',()=>this._handleExport('report'));
        document.getElementById('showDataLabels').addEventListener('change',function(){Charts.toggleDataLabels(this.checked);});
        document.getElementById('btnAddRow').addEventListener('click',()=>this._vizAddRow());
        document.getElementById('btnSaveChanges').addEventListener('click',()=>this._vizSaveChanges());
        document.getElementById('tableFilterInput').addEventListener('input',()=>this._renderVizTable());
        document.getElementById('tableFilterCol').addEventListener('change',()=>this._renderVizTable());
        document.getElementById('btnApplyAxisDomain').addEventListener('click',()=>this._applyAxisDomain());
        document.addEventListener('click',(e)=>{const ed=document.getElementById('chartInlineEdit');if(ed&&!ed.contains(e.target))ed.remove();});
        document.addEventListener('click',(e)=>{const ed=document.getElementById('chartStyleEdit');if(ed&&!ed.contains(e.target))ed.remove();});
    },
    _updateYColumnList(){
        const aid=this._getActiveFileId();
        const cols=aid&&this.state.files[aid]?(this.state.files[aid].columns||[]):[];
        // X轴
        const xSel=document.getElementById('xColumn');
        xSel.innerHTML=cols.map(c=>'<option value="'+c+'">'+c+'</option>').join('');
        // Y轴（带颜色选择，选中时红色高亮边框）
        const list=document.getElementById('yColumnColorList');
        if(!list)return;
        const colors=Charts.getColors();
        list.innerHTML=cols.map((c,i)=>
            '<label class="ycol-item"><input type="checkbox" value="'+c+'" style="display:none;" onchange="this.parentElement.classList.toggle(\'selected\',this.checked)"><span class="ycol-color-dot" style="background:'+colors[i%colors.length]+';" data-col="'+c+'" title="点击修改颜色"></span><span style="flex:1;font-size:0.85em;">'+c+'</span></label>'
        ).join('');
        // 颜色点击事件
        list.querySelectorAll('.ycol-color-dot').forEach(dot=>{
            dot.addEventListener('click',(e)=>{
                e.stopPropagation();e.preventDefault();
                const inp=document.createElement('input');
                inp.type='color';inp.value=rgbToHex(dot.style.background)||dot.style.background;
                inp.style.position='absolute';inp.style.opacity='0';
                dot.appendChild(inp);
                inp.addEventListener('input',()=>{dot.style.background=inp.value;});
                inp.addEventListener('change',()=>inp.remove());
                inp.click();
            });
        });
        // 标签点击切换选中（选中时红色高亮）
        list.querySelectorAll('.ycol-item').forEach(item=>{
            item.addEventListener('click',()=>{
                const cb=item.querySelector('input');
                cb.checked=!cb.checked;
                item.classList.toggle('selected',cb.checked);
            });
        });
        function rgbToHex(c){if(!c||!c.startsWith('rgb'))return c;const m=c.match(/[\d.]+/g);if(!m||m.length<3)return c;return '#'+[m[0],m[1],m[2]].map(x=>{const h=parseInt(x).toString(16);return h.length===1?'0'+h:h;}).join('');}
    },
    async _handleVisualization(){
        const aid=this._getActiveFileId();if(!aid){Utils.toast('请先选择文件','warning');return;}
        const useId=this.state.files[aid]?.cleanedFileId||aid;
        const ct=document.getElementById('chartType').value;
        const xc=document.getElementById('xColumn').value;
        const yChecks=document.querySelectorAll('#yColumnColorList input:checked');
        const ys=Array.from(yChecks).map(cb=>cb.value);
        const title=document.getElementById('chartTitle').value||ct;
        if(!xc){Utils.toast('请选择X轴列','warning');return;}if(ys.length===0){Utils.toast('请选择Y轴列','warning');return;}
        // 收集每列颜色
        const seriesColors=[];
        document.querySelectorAll('#yColumnColorList .ycol-item').forEach((item,i)=>{
            const cb=item.querySelector('input');
            if(cb&&cb.checked){
                const dot=item.querySelector('.ycol-color-dot');
                const color=dot?dot.style.background:null;
                if(color)seriesColors.push({index:seriesColors.length,color:color});
            }
        });
        this._showLoading('生成图表...');
        try{
            const r=await API.generateChart(useId,{chart_type:ct,x_column:xc,y_columns:ys,title});
            document.getElementById('chartStage').innerHTML='';
            const mergeX=document.getElementById('mergeSameX').checked;
            const xRotate=document.getElementById('xLabelRotate').value;
            Charts._editCallback=(params,dom)=>{this._onChartClick(params,dom);};
            Charts._titleEditCallback=(params)=>{this._onChartTitleEdit(params);};
            Charts.renderChart('chartStage',r,{mergeSameX:mergeX,seriesColors,xLabelRotate:xRotate});
            if(document.getElementById('showDataLabels').checked)Charts.toggleDataLabels(true);
            this.state.currentChart=r;this._markProgress(aid,'visualization');
            this._updateStepper('visualization');this._refreshDashboard();
            await this._loadVizDataTable(useId);
        }catch(err){Utils.toast('图表生成失败: '+err.message,'error');}
        finally{this._hideLoading();}
    },

    /* --- 图表标题/图例双击编辑样式 --- */
    _onChartTitleEdit(params){
        const oldEd=document.getElementById('chartStyleEdit');
        if(oldEd)oldEd.remove();
        const isTitle=params.componentType==='title';
        const stage=document.getElementById('chartStage');
        const ed=document.createElement('div');
        ed.id='chartStyleEdit';
        ed.style.cssText='position:absolute;z-index:999;top:10px;right:10px;background:rgba(15,12,41,0.96);border:1px solid rgba(99,102,241,0.5);border-radius:8px;padding:12px;display:flex;flex-direction:column;gap:8px;box-shadow:0 4px 20px rgba(0,0,0,0.6);min-width:200px;';
        ed.innerHTML='<strong style="color:var(--neon-primary);font-size:0.85em;">'+(isTitle?'编辑标题样式':'编辑图例样式')+'</strong>'+
            (isTitle?'<label style="font-size:0.8em;color:var(--text-muted);">文字</label><input id="styleText" class="form-input" style="font-size:0.85em;" value="'+Utils.escapeHtml(params.text||'')+'">':'')+
            '<label style="font-size:0.8em;color:var(--text-muted);">颜色</label><input type="color" id="styleColor" value="#e2e8f0" style="width:100%;height:30px;border:none;cursor:pointer;background:transparent;">'+
            '<label style="font-size:0.8em;color:var(--text-muted);">字号</label><input type="number" id="styleSize" class="form-input" style="font-size:0.85em;" value="14" min="8" max="48">'+
            '<label style="font-size:0.8em;color:var(--text-muted);">水平位置</label><select id="styleLeft" class="form-select" style="font-size:0.82em;"><option value="left">左</option><option value="center" selected>中</option><option value="right">右</option></select>'+
            '<button class="btn-primary btn-block" id="styleApply" style="font-size:0.85em;">应用</button>';
        stage.style.position='relative';
        stage.appendChild(ed);
        document.getElementById('styleApply').addEventListener('click',()=>{
            const style={};
            const txt=document.getElementById('styleText');if(txt)style.text=txt.value;
            style.color=document.getElementById('styleColor').value;
            style.fontSize=parseInt(document.getElementById('styleSize').value)||14;
            style.left=document.getElementById('styleLeft').value;
            if(isTitle)Charts.editTitleStyle(style);
            else Charts.editLegendStyle(style);
            ed.remove();Utils.toast('样式已更新','success');
        });
    },

    /* --- 图表点击内联编辑 --- */
    _onChartClick(params,chartDom){
        const oldEd=document.getElementById('chartInlineEdit');
        if(oldEd)oldEd.remove();
        const seriesIndex=params.seriesIndex;
        const dataIndex=params.dataIndex;
        const currentVal=params.value;
        const seriesName=params.seriesName||('系列'+(seriesIndex+1));
        const ed=document.createElement('div');
        ed.id='chartInlineEdit';
        ed.style.cssText='position:absolute;z-index:998;background:rgba(15,12,41,0.95);border:1px solid rgba(99,102,241,0.5);border-radius:6px;padding:6px 10px;display:flex;align-items:center;gap:6px;box-shadow:0 4px 16px rgba(0,0,0,0.5);';
        ed.style.left=Math.min((params.event.offsetX||0),chartDom.offsetWidth-220)+'px';
        ed.style.top=Math.max(0,(params.event.offsetY||0)-40)+'px';
        ed.innerHTML='<span style="color:var(--text-muted);font-size:0.75em;white-space:nowrap;">'+seriesName+' #'+(dataIndex+1)+'</span><input type="number" id="chartEditInput" value="'+currentVal+'" style="width:90px;padding:4px 6px;border:1px solid rgba(255,255,255,0.2);border-radius:4px;background:rgba(255,255,255,0.08);color:#fff;font-size:0.85em;" step="any"><button class="btn-sm" id="chartEditOk" style="font-size:0.75em;padding:3px 8px;">✓</button><button class="btn-sm" id="chartEditCancel" style="font-size:0.75em;padding:3px 8px;color:var(--danger);">✕</button>';
        chartDom.style.position='relative';
        chartDom.appendChild(ed);
        const input=ed.querySelector('#chartEditInput');
        input.focus();input.select();
        const self=this;
        const applyEdit=()=>{
            const numVal=parseFloat(input.value);
            if(isNaN(numVal)){Utils.toast('请输入有效数值','warning');ed.remove();return;}
            if(Charts.updateDataPoint(seriesIndex,dataIndex,numVal)){
                Utils.toast('数据已更新（保存请用下方表格按钮）','success');
                if(self.state.editedData){
                    const series=Charts.getChartData();
                    if(series&&series[seriesIndex]){
                        const colName=series[seriesIndex].name;
                        if(colName&&self.state.editedData.rows[dataIndex]){
                            self.state.editedData.rows[dataIndex][colName]=numVal;
                            self._renderVizTable();
                        }
                    }
                }
            }
            ed.remove();
        };
        ed.querySelector('#chartEditOk').addEventListener('click',applyEdit);
        ed.querySelector('#chartEditCancel').addEventListener('click',()=>ed.remove());
        input.addEventListener('keydown',(e)=>{if(e.key==='Enter')applyEdit();if(e.key==='Escape')ed.remove();});
    },
    _exportChartPNG(){if(!this.state.currentChart){Utils.toast('没有可导出的图表','warning');return;}const dom=document.getElementById('chartStage').querySelector('div');if(!dom)return;const inst=echarts.getInstanceByDom(dom);if(inst){Utils.downloadFile(inst.getDataURL({type:'png',pixelRatio:2,backgroundColor:'#1a1645'}),'chart.png');Utils.toast('图表已导出','success');}},
    _applyAxisDomain(){
        const inst=Charts.getInstance();
        if(!inst||inst.isDisposed()){Utils.toast('请先生成图表','warning');return;}
        const xMin=document.getElementById('xAxisMin').value;
        const xMax=document.getElementById('xAxisMax').value;
        const yMin=document.getElementById('yAxisMin').value;
        const yMax=document.getElementById('yAxisMax').value;
        Charts.updateAxisDomain({
            xMin:xMin!==''?parseFloat(xMin):null,
            xMax:xMax!==''?parseFloat(xMax):null,
            yMin:yMin!==''?parseFloat(yMin):null,
            yMax:yMax!==''?parseFloat(yMax):null,
        });
        Utils.toast('轴定义域已更新','success');
    },
    _clearChart(){const stage=document.getElementById('chartStage');const dom=stage.querySelector('div');if(dom){const inst=echarts.getInstanceByDom(dom);if(inst)inst.dispose();}stage.innerHTML='<div class="empty-state-sm">配置参数后点击"生成图表"</div>';this.state.currentChart=null;this.state.editedData=null;document.getElementById('vizDataSection').style.display='none';const fi=document.getElementById('tableFilterInput');if(fi)fi.value='';},

    /* -- 数据表格 CRUD -- */
    async _loadVizDataTable(fileId){
        try{const r=await API.getAllData(fileId);if(r.data){
            this.state.editedData={fileId:fileId,columns:r.columns||[],rows:r.data||[],deletedRows:[],deletedCols:[],renamedCols:{},newCols:{},newRows:[]};
            // 填充筛选列下拉
            const fc=document.getElementById('tableFilterCol');
            if(fc){fc.innerHTML='<option value="">全部列</option>'+(r.columns||[]).map(c=>'<option value="'+c+'">'+c+'</option>').join('');}
            this._renderVizTable();document.getElementById('vizDataSection').style.display='block';
            // 滚动到表格顶部
            const wrap=document.getElementById('vizDataTableWrap');
            if(wrap)wrap.scrollTop=0;
        }}catch(e){console.warn('Load viz data failed:',e);}
    },
    _renderVizTable(){
        if(!this.state.editedData)return;const d=this.state.editedData;
        const cols=d.columns.filter(c=>!d.deletedCols.includes(c));
        const filterVal=(document.getElementById('tableFilterInput')?.value||'').toLowerCase();
        const filterCol=document.getElementById('tableFilterCol')?.value||'';

        // 筛选函数
        const matchFilter=(row)=>{
            if(!filterVal)return true;
            if(filterCol){const v=row[filterCol];return v!==null&&v!==undefined&&String(v).toLowerCase().includes(filterVal);}
            return Object.values(row).some(v=>v!==null&&v!==undefined&&String(v).toLowerCase().includes(filterVal));
        };

        // 序号从1开始
        let rowNum=0;
        const renderRow=(row,ri,isNew)=>{
            if(!isNew&&d.deletedRows.includes(ri))return'';
            if(!matchFilter(row))return'';
            rowNum++;
            return'<tr'+(isNew?' style="background:rgba(16,185,129,0.08);"':'')+'>'+
                '<td class="row-num">'+rowNum+'</td>'+
                cols.map(c=>'<td data-row="'+(isNew?'new_'+ri:ri)+'" data-col="'+c+'" ondblclick="App._editCell(this)">'+(row[c]!==null&&row[c]!==undefined?String(row[c]).slice(0,80):'')+'</td>').join('')+
                '<td class="row-delete-btn" data-row="'+(isNew?'new_'+ri:ri)+'">删除</td></tr>';
        };

        let h='<thead><tr><th class="row-num" style="position:sticky;top:0;z-index:10;">#</th>'+
            cols.map(c=>'<th data-col="'+c+'" title="双击重命名" style="position:sticky;top:0;z-index:10;">'+c+'</th>').join('')+
            '<th style="position:sticky;top:0;z-index:10;width:60px;text-align:center;">操作</th></tr></thead>';
        h+='<tbody>';
        // 新增行（显示在最前面）
        d.newRows.forEach((row,ni)=>{h+=renderRow(row,ni,true);});
        // 原有行
        d.rows.forEach((row,i)=>{h+=renderRow(row,i,false);});
        h+='</tbody>';
        document.getElementById('vizDataTable').innerHTML=h;

        // 绑定列头重命名
        document.querySelectorAll('#vizDataTable th[data-col]').forEach(th=>{
            th.addEventListener('dblclick',()=>this._renameCol(th.dataset.col));
        });
        // 绑定删除按钮
        document.querySelectorAll('#vizDataTable .row-delete-btn').forEach(btn=>{
            btn.addEventListener('click',e=>{
                e.stopPropagation();
                const dr=btn.dataset.row;
                if(dr!==undefined){
                    if(dr.startsWith('new_')){
                        this._vizRemoveNewRow(parseInt(dr.replace('new_','')));
                    }else{
                        this._showConfirm('确定删除第 '+(parseInt(dr)+1)+' 行吗？',()=>{this._vizDeleteRow(parseInt(dr));});
                    }
                }
            });
        });
    },
    _editCell(td){
        if(td.querySelector('input'))return;
        const old=td.textContent;td.classList.add('editing');
        td.innerHTML='<input value="'+Utils.escapeHtml(old)+'">';
        const inp=td.querySelector('input');inp.focus();inp.select();
        const save=()=>{
            const val=inp.value;td.classList.remove('editing');td.textContent=val;
            const dr=td.dataset.row,ci=td.dataset.col;
            if(!dr||!ci||!this.state.editedData)return;
            if(dr.startsWith('new_')){
                const ni=parseInt(dr.replace('new_',''));
                this.state.editedData.newRows[ni][ci]=val;
            }else{
                const ri=parseInt(dr);
                if(!this.state.editedData.rows[ri])this.state.editedData.rows[ri]={};
                this.state.editedData.rows[ri][ci]=val;
            }
        };
        inp.addEventListener('blur',save);
        inp.addEventListener('keydown',e=>{
            if(e.key==='Enter')inp.blur();
            if(e.key==='Escape'){td.textContent=old;td.classList.remove('editing');}
        });
    },
    _vizDeleteRow(i){if(!this.state.editedData)return;this.state.editedData.deletedRows.push(i);this._renderVizTable();},
    _vizRemoveNewRow(i){if(!this.state.editedData)return;this.state.editedData.newRows.splice(i,1);this._renderVizTable();},
    _vizAddRow(){
        if(!this.state.editedData)return;
        const row={};this.state.editedData.columns.forEach(c=>row[c]='');
        // 插入到 newRows 开头
        this.state.editedData.newRows.unshift(row);
        this._renderVizTable();
        // 滚动到表格顶部
        const wrap=document.getElementById('vizDataTableWrap');
        if(wrap)wrap.scrollTop=0;
    },
    _vizAddCol(){
        if(!this.state.editedData)return;
        const name=prompt('输入新列名:');if(!name)return;
        if(this.state.editedData.columns.includes(name)&&!this.state.editedData.deletedCols.includes(name)){Utils.toast('列名已存在','warning');return;}
        this.state.editedData.newCols[name]='';
        this.state.editedData.columns.push(name);
        this.state.editedData.rows.forEach(row=>{row[name]='';});
        this.state.editedData.newRows.forEach(row=>{row[name]='';});
        this._renderVizTable();
        // 更新筛选列下拉
        const fc=document.getElementById('tableFilterCol');
        if(fc){const opt=document.createElement('option');opt.value=name;opt.textContent=name;fc.appendChild(opt);}
    },
    _renameCol(oldName){
        const n=prompt('重命名列 "'+oldName+'":',oldName);
        if(!n||n===oldName)return;
        if(!this.state.editedData)return;
        const idx=this.state.editedData.columns.indexOf(oldName);
        if(idx>=0)this.state.editedData.columns[idx]=n;
        this.state.editedData.renamedCols[oldName]=n;
        this.state.editedData.rows.forEach(row=>{if(row[oldName]!==undefined){row[n]=row[oldName];delete row[oldName];}});
        this.state.editedData.newRows.forEach(row=>{if(row[oldName]!==undefined){row[n]=row[oldName];delete row[oldName];}});
        this._renderVizTable();
        // 更新筛选列下拉
        const fc=document.getElementById('tableFilterCol');
        if(fc){const opt=fc.querySelector('option[value="'+oldName+'"]');if(opt)opt.value=n;opt.textContent=n;}
    },
    async _vizSaveChanges(){
        if(!this.state.editedData)return;const d=this.state.editedData;this._showLoading('保存修改...');
        try{
            const fileId=d.fileId;
            // 处理重命名
            for(const [old,neu] of Object.entries(d.renamedCols)){await API.renameColumn(fileId,old,neu);}
            // 处理删除列
            for(const col of d.deletedCols){try{await API.deleteColumn(fileId,col);}catch(e){}}
            // 处理新增列
            for(const [col,defVal] of Object.entries(d.newCols)){try{await API.addColumn(fileId,col,defVal);}catch(e){}}
            // 处理删除行（从后往前删）
            const sortedDel=[...d.deletedRows].sort((a,b)=>b-a);
            for(const ri of sortedDel){try{await API.deleteRow(fileId,ri);}catch(e){}}
            // 更新单元格
            for(let i=0;i<d.rows.length;i++){for(const col of d.columns){const val=d.rows[i][col];if(val!==undefined){try{await API.updateCell(fileId,i,col,val);}catch(e){}}}}
            // 添加新行
            for(const row of d.newRows){try{await API.addRow(fileId,row);}catch(e){}}
            Utils.toast('修改已保存','success');
            // 重新加载
            await this._loadVizDataTable(fileId);
            // 更新缓存的列信息
            const fid=this._getActiveFileId();if(fid&&this.state.files[fid]){const r=await API.getAllData(fileId);this.state.files[fid].columns=r.columns||[];this.state.files[fid].numericColumns=r.columns.filter(c=>{const sample=r.data[0];return sample&&typeof sample[c]==='number';})||[];}
        }catch(err){Utils.toast('保存失败: '+err.message,'error');}
        finally{this._hideLoading();}
    },

    /* ========== 导出 ========== */
    _bindExportEvents(){},
    async _handleExport(type){const aid=this._getActiveFileId();if(!aid){Utils.toast('请先选择文件','warning');return;}const useId=this.state.files[aid]?.cleanedFileId||aid;this._showLoading('导出中...');try{switch(type){case'data':await API.exportData(useId);break;case'report':await API.exportReport(useId);break;}this._markProgress(aid,'export');this._refreshDashboard();Utils.toast('导出成功','success');}catch(err){Utils.toast('导出失败: '+err.message,'error');}finally{this._hideLoading();}},

    /* ========== AI ========== */
    _bindAIEvents(){document.getElementById('btnAISend').addEventListener('click',()=>this._sendAIMessage());document.getElementById('aiInput').addEventListener('keydown',e=>{if(e.key==='Enter')this._sendAIMessage();});},
    async _sendAIMessage(){const inp=document.getElementById('aiInput');const msg=inp.value.trim();if(!msg)return;this._addAIMessage('user',msg);inp.value='';const aid=this._getActiveFileId();const useId=aid?(this.state.files[aid]?.cleanedFileId||aid):null;try{const r=await API.askAI(msg,useId);if(r.reply)this._addAIMessage('bot',r.reply);if(r.chart_data){this.state.currentChart=r.chart_data;this.switchView('visualization');setTimeout(()=>{document.getElementById('chartStage').innerHTML='';Charts.renderChart('chartStage',r.chart_data);},400);}}catch(err){this._addAIMessage('bot','抱歉: '+err.message);}},
    _addAIMessage(role,text){const area=document.getElementById('aiChatArea');const div=document.createElement('div');div.className='ai-msg '+role;div.innerHTML='<div class="ai-avatar">'+(role==='user'?'You':'AI')+'</div><div class="ai-bubble"><p>'+text.replace(/\n/g,'<br>')+'</p></div>';area.appendChild(div);area.scrollTop=area.scrollHeight;},

    /* ========== 工具 ========== */
    _showConfirm(msg,onOk){
        const overlay=document.getElementById('confirmOverlay');
        document.getElementById('confirmMsg').textContent=msg;
        overlay.style.display='flex';
        const ok=document.getElementById('confirmOk');
        const cancel=document.getElementById('confirmCancel');
        const close=()=>{overlay.style.display='none';ok.onclick=null;cancel.onclick=null;};
        ok.onclick=()=>{close();if(onOk)onOk();};
        cancel.onclick=close;
        overlay.onclick=(e)=>{if(e.target===overlay)close();};
    },
    _showLoading(t){document.getElementById('loadingOverlay').style.display='flex';document.getElementById('loadingText').textContent=t||'处理中...';},
    _hideLoading(){document.getElementById('loadingOverlay').style.display='none';},
    async _checkServerHealth(){try{await API.healthCheck();}catch(e){}},
};
document.addEventListener('DOMContentLoaded',()=>App.init());
