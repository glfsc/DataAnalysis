/**
 * Data Analysis System - 用户认证模块
 * 登录、注册、密码找回、用户设置、免登录记忆、头像上传裁剪
 */
const Auth = {
    state: {
        loggedIn: false,
        user: null,
        token: null,
    },

    init() {
        const saved = this._loadToken();
        if (saved) {
            this.state.token = saved;
            this._checkAndRestore();
        }
        this._renderWelcomeAuth();
        this._initTopbarAvatarDelegation();
        this._initWelcomeAvatarDelegation();
    },

    /* ========== 令牌持久化 ========== */
    _loadToken() {
        try {
            const data = localStorage.getItem('da_auth');
            if (data) {
                const parsed = JSON.parse(data);
                if (parsed.token && parsed.expires) {
                    if (new Date(parsed.expires).getTime() > Date.now()) {
                        return parsed.token;
                    }
                    localStorage.removeItem('da_auth');
                }
            }
        } catch (e) { /* ignore */ }
        return null;
    },

    _saveToken(token, rememberDays = 30) {
        const expires = new Date(Date.now() + rememberDays * 24 * 60 * 60 * 1000);
        try {
            localStorage.setItem('da_auth', JSON.stringify({ token, expires: expires.toISOString() }));
        } catch (e) { /* ignore */ }
    },

    _clearToken() {
        try { localStorage.removeItem('da_auth'); } catch (e) { /* ignore */ }
    },

    /* ========== 自动恢复登录 ========== */
    async _checkAndRestore() {
        try {
            const result = await API.authCheck();
            if (result.logged_in && result.user) {
                this.state.loggedIn = true;
                this.state.user = result.user;
                this._renderAll();
            } else {
                this._clearToken();
                this.state.token = null;
            }
        } catch (e) {
            console.warn('Auth check failed:', e);
        }
    },

    /* ========== 登录 / 注册 / 找回密码 ========== */
    async login(username, password, remember = false) {
        const result = await API.authLogin(username, password, remember);
        this.state.token = result.token;
        this.state.user = result.user;
        this.state.loggedIn = true;
        this._saveToken(result.token, remember ? 365 : 30);
        this._renderAll();
        this._hideAuthModal();
        return result;
    },

    async register(username, password, passwordConfirm) {
        const result = await API.authRegister(username, password, passwordConfirm);
        this.state.token = result.token;
        this.state.user = result.user;
        this.state.loggedIn = true;
        this._saveToken(result.token, 30);
        this._renderAll();
        this._hideAuthModal();
        return result;
    },

    async recoverPassword(username) {
        return await API.authRecover(username);
    },

    /* ========== 退出登录 ========== */
    async logout() {
        try {
            if (this.state.token) { await API.authLogout(); }
        } catch (e) { /* ignore */ }
        this.state.loggedIn = false;
        this.state.user = null;
        this.state.token = null;
        this._clearToken();
        this._renderAll();
        // 返回欢迎页
        this._goToWelcome();
    },

    /** 回到欢迎界面 */
    _goToWelcome() {
        const welcome = document.getElementById('welcomeScreen');
        const appWrapper = document.getElementById('appWrapper');
        if (welcome) {
            welcome.classList.remove('fade-out');
        }
        if (appWrapper) {
            appWrapper.style.display = 'none';
        }
        // 重置 App 状态
        if (typeof App !== 'undefined' && App.state) {
            App.state.files = {};
            App.state.fileOrder = [];
            App.state.selectedIds = [];
            App.state.currentFileId = null;
            App.state.currentChart = null;
            App.state.editedData = null;
            App._refreshDashboard();
        }
    },

    /* ========== 更新用户信息 ========== */
    async updateProfile(data) {
        const result = await API.authUpdateMe(data);
        this.state.user = result;
        this._renderAll();
        return result;
    },

    /* ========== UI 渲染 ========== */
    _renderAll() {
        this._renderWelcomeAuth();
        this._renderTopbarAvatar();
    },

    /* ========== 欢迎页认证区域 ========== */
    _renderWelcomeAuth() {
        const container = document.getElementById('welcomeAuthArea');
        if (!container) return;

        if (this.state.loggedIn && this.state.user) {
            const userData = this.state.user;
            const avatarHtml = this._avatarImgOrInitial(userData, 'welcome-avatar-img');
            container.innerHTML = `
                <div class="welcome-avatar logged-in welcome-avatar-clickable" id="welcomeAvatarMenu"
                     title="${Utils.escapeHtml(userData.display_name || userData.username)}">
                    ${avatarHtml}
                </div>
                <span class="welcome-user-name">${Utils.escapeHtml(userData.display_name || userData.username)}</span>
                <div class="welcome-dropdown" id="welcomeDropdown" style="display:none;">
                    <div class="user-dropdown-item" data-welcome-action="settings">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
                        <span>设置</span>
                    </div>
                    <div class="user-dropdown-item user-dropdown-item-danger" data-welcome-action="logout">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
                        <span>退出登录</span>
                    </div>
                </div>
            `;
        } else {
            container.innerHTML = `
                <button class="welcome-auth-btn" id="btnWelcomeLogin">登录</button>
                <button class="welcome-auth-btn welcome-auth-btn-outline" id="btnWelcomeRegister">注册</button>
                <div class="welcome-avatar default" title="未登录">?</div>
            `;
            setTimeout(() => {
                const btnLogin = document.getElementById('btnWelcomeLogin');
                const btnRegister = document.getElementById('btnWelcomeRegister');
                if (btnLogin) btnLogin.addEventListener('click', () => this._showAuthModal('login'));
                if (btnRegister) btnRegister.addEventListener('click', () => this._showAuthModal('register'));
            }, 0);
        }
    },

    /** 欢迎页头像——事件委托（只绑定一次） */
    _initWelcomeAvatarDelegation() {
        const container = document.getElementById('welcomeAuthArea');
        if (!container) return;
        container.addEventListener('click', (e) => {
            // 头像菜单切换
            const avatarBtn = e.target.closest('#welcomeAvatarMenu');
            if (avatarBtn) {
                e.stopPropagation();
                const dd = document.getElementById('welcomeDropdown');
                if (dd) dd.style.display = dd.style.display === 'block' ? 'none' : 'block';
                return;
            }
            // 下拉菜单项
            const actionEl = e.target.closest('[data-welcome-action]');
            if (actionEl) {
                const dd = document.getElementById('welcomeDropdown');
                if (dd) dd.style.display = 'none';
                const action = actionEl.dataset.welcomeAction;
                if (action === 'settings') this._showSettingsModal();
                else if (action === 'logout') this.logout();
                return;
            }
        });
        // 点击外部关闭
        document.addEventListener('click', (e) => {
            if (!container.contains(e.target)) {
                const dd = document.getElementById('welcomeDropdown');
                if (dd) dd.style.display = 'none';
            }
        });
    },

    /* ========== 仪表盘顶栏头像 ========== */
    _initTopbarAvatarDelegation() {
        const container = document.getElementById('topbarUserAvatar');
        if (!container) return;
        container.addEventListener('click', (e) => {
            const target = e.target.closest('[data-action]');
            if (!target) return;
            const action = target.dataset.action;
            const dropdown = document.getElementById('userDropdown');

            if (action === 'menu') {
                e.stopPropagation();
                if (dropdown) dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
            } else if (action === 'settings') {
                if (dropdown) dropdown.style.display = 'none';
                this._showSettingsModal();
            } else if (action === 'logout') {
                if (dropdown) dropdown.style.display = 'none';
                this.logout();
            }
        });
        document.addEventListener('click', (e) => {
            if (!container.contains(e.target)) {
                const dd = document.getElementById('userDropdown');
                if (dd) dd.style.display = 'none';
            }
        });
    },

    _renderTopbarAvatar() {
        const avatarEl = document.getElementById('topbarUserAvatar');
        if (!avatarEl) return;

        if (this.state.loggedIn && this.state.user) {
            const userData = this.state.user;
            const avatarHtml = this._avatarImgOrInitial(userData, 'topbar-avatar-img');
            avatarEl.innerHTML = `
                <div class="user-avatar logged-in-avatar" data-action="menu"
                     title="${Utils.escapeHtml(userData.display_name || userData.username)}">
                    ${avatarHtml}
                </div>
                <div class="user-dropdown" id="userDropdown" style="display:none;">
                    <div class="user-dropdown-header">
                        <div class="user-dropdown-avatar">${this._avatarImgOrInitial(userData)}</div>
                        <div>
                            <div class="user-dropdown-name">${Utils.escapeHtml(userData.display_name || userData.username)}</div>
                            <div class="user-dropdown-username">@${Utils.escapeHtml(userData.username)}</div>
                        </div>
                    </div>
                    <div class="user-dropdown-item" data-action="settings">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
                        <span>设置</span>
                    </div>
                    <div class="user-dropdown-item user-dropdown-item-danger" data-action="logout">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
                        <span>退出登录</span>
                    </div>
                </div>
            `;
        } else {
            avatarEl.innerHTML = `
                <div class="user-avatar default-avatar" title="未登录">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                </div>
            `;
        }
    },

    /** 生成头像 HTML：有自定义头像显示图片，否则显示首字母 */
    _avatarImgOrInitial(userData, className) {
        if (userData.avatar_url) {
            const cls = className ? ` class="${className}"` : '';
            return `<img src="${Utils.escapeHtml(userData.avatar_url)}"${cls} alt="" onerror="this.style.display='none';this.nextElementSibling.style.display='flex';" /><span class="avatar-initial" style="display:none;">${(userData.display_name || userData.username)[0].toUpperCase()}</span>`;
        }
        return `<span class="avatar-initial">${(userData.display_name || userData.username)[0].toUpperCase()}</span>`;
    },

    /* ========== 认证弹窗（登录/注册/找回密码） ========== */
    _showAuthModal(tab = 'login') {
        this._hideAuthModal();
        const overlay = document.createElement('div');
        overlay.className = 'auth-modal-overlay';
        overlay.id = 'authModalOverlay';
        overlay.innerHTML = `
            <div class="auth-modal glass-card">
                <button class="auth-modal-close" id="btnAuthClose">&times;</button>
                <div class="auth-tabs">
                    <button class="auth-tab ${tab==='login'?'active':''}" data-auth-tab="login">登录</button>
                    <button class="auth-tab ${tab==='register'?'active':''}" data-auth-tab="register">注册</button>
                    <button class="auth-tab ${tab==='recover'?'active':''}" data-auth-tab="recover">找回密码</button>
                </div>
                <div class="auth-panel" id="authPanelLogin" style="display:${tab==='login'?'block':'none'};">
                    <div class="auth-input-group"><label class="form-label">用户名</label><input type="text" class="form-input" id="loginUsername" placeholder="请输入用户名" autocomplete="username"></div>
                    <div class="auth-input-group"><label class="form-label">密码</label><input type="password" class="form-input" id="loginPassword" placeholder="请输入密码" autocomplete="current-password"></div>
                    <div class="auth-options"><label class="checkbox-label"><input type="checkbox" id="loginRemember"> <span>记住登录（免登录）</span></label></div>
                    <div class="auth-error" id="loginError" style="display:none;"></div>
                    <button class="btn-primary btn-block" id="btnLogin">登 录</button>
                </div>
                <div class="auth-panel" id="authPanelRegister" style="display:${tab==='register'?'block':'none'};">
                    <div class="auth-input-group"><label class="form-label">用户名</label><input type="text" class="form-input" id="regUsername" placeholder="2-50个字符，支持中英文" autocomplete="off"></div>
                    <div class="auth-input-group"><label class="form-label">密码</label><input type="password" class="form-input" id="regPassword" placeholder="至少6位密码" autocomplete="new-password"></div>
                    <div class="auth-input-group"><label class="form-label">确认密码</label><input type="password" class="form-input" id="regPasswordConfirm" placeholder="再次输入密码" autocomplete="new-password"></div>
                    <div class="auth-error" id="regError" style="display:none;"></div>
                    <button class="btn-primary btn-block" id="btnRegister">注 册</button>
                </div>
                <div class="auth-panel" id="authPanelRecover" style="display:${tab==='recover'?'block':'none'};">
                    <p style="color:var(--text-muted);font-size:0.85em;margin-bottom:14px;">输入用户名，系统将为您重置密码</p>
                    <div class="auth-input-group"><label class="form-label">用户名</label><input type="text" class="form-input" id="recoverUsername" placeholder="请输入用户名"></div>
                    <div class="auth-error" id="recoverError" style="display:none;"></div>
                    <div class="auth-success" id="recoverSuccess" style="display:none;"></div>
                    <button class="btn-primary btn-block" id="btnRecover">找回密码</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        overlay.querySelector('#btnAuthClose').addEventListener('click', () => this._hideAuthModal());
        overlay.addEventListener('click', (e) => { if (e.target === overlay) this._hideAuthModal(); });
        overlay.querySelectorAll('.auth-tab').forEach(btn => {
            btn.addEventListener('click', () => {
                overlay.querySelectorAll('.auth-tab').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                ['Login','Register','Recover'].forEach(t => {
                    const p = overlay.querySelector('#authPanel'+t);
                    if (p) p.style.display = t.toLowerCase() === btn.dataset.authTab ? 'block' : 'none';
                });
                overlay.querySelectorAll('.auth-error,.auth-success').forEach(el => { el.style.display = 'none'; el.textContent = ''; });
            });
        });
        overlay.querySelector('#btnLogin').addEventListener('click', () => this._handleLogin(overlay));
        overlay.querySelector('#btnRegister').addEventListener('click', () => this._handleRegister(overlay));
        overlay.querySelector('#btnRecover').addEventListener('click', () => this._handleRecover(overlay));
        overlay.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const t = overlay.querySelector('.auth-tab.active')?.dataset.authTab;
                if (t === 'login') this._handleLogin(overlay);
                else if (t === 'register') this._handleRegister(overlay);
                else if (t === 'recover') this._handleRecover(overlay);
            }
        });
        setTimeout(() => {
            const fi = overlay.querySelector('.auth-panel[style*="block"] input');
            if (fi) fi.focus();
        }, 100);
    },

    _hideAuthModal() {
        const o = document.getElementById('authModalOverlay');
        if (o) o.remove();
    },

    _showError(overlay, panelId, errorId, message) {
        const el = overlay.querySelector('#' + errorId);
        if (el) { el.textContent = message; el.style.display = 'block'; }
    },

    async _handleLogin(overlay) {
        const username = overlay.querySelector('#loginUsername').value.trim();
        const password = overlay.querySelector('#loginPassword').value;
        const remember = overlay.querySelector('#loginRemember').checked;
        if (!username || !password) { this._showError(overlay, 'authPanelLogin', 'loginError', '请输入用户名和密码'); return; }
        const btn = overlay.querySelector('#btnLogin'); btn.disabled = true; btn.textContent = '登录中...';
        try {
            await this.login(username, password, remember);
            Utils.toast('登录成功', 'success');
            if (typeof App !== 'undefined' && App._enterApp) App._enterApp();
        } catch (err) { this._showError(overlay, 'authPanelLogin', 'loginError', err.message); }
        finally { btn.disabled = false; btn.textContent = '登 录'; }
    },

    async _handleRegister(overlay) {
        const username = overlay.querySelector('#regUsername').value.trim();
        const password = overlay.querySelector('#regPassword').value;
        const pc = overlay.querySelector('#regPasswordConfirm').value;
        if (!username || !password) { this._showError(overlay, 'authPanelRegister', 'regError', '请输入用户名和密码'); return; }
        if (password !== pc) { this._showError(overlay, 'authPanelRegister', 'regError', '两次输入的密码不一致'); return; }
        if (password.length < 6) { this._showError(overlay, 'authPanelRegister', 'regError', '密码长度至少6位'); return; }
        const btn = overlay.querySelector('#btnRegister'); btn.disabled = true; btn.textContent = '注册中...';
        try {
            await this.register(username, password, pc);
            Utils.toast('注册成功，已自动登录', 'success');
            if (typeof App !== 'undefined' && App._enterApp) App._enterApp();
        } catch (err) { this._showError(overlay, 'authPanelRegister', 'regError', err.message); }
        finally { btn.disabled = false; btn.textContent = '注 册'; }
    },

    async _handleRecover(overlay) {
        const username = overlay.querySelector('#recoverUsername').value.trim();
        if (!username) { this._showError(overlay, 'authPanelRecover', 'recoverError', '请输入用户名'); return; }
        const btn = overlay.querySelector('#btnRecover'); btn.disabled = true; btn.textContent = '处理中...';
        try {
            const result = await this.recoverPassword(username);
            const se = overlay.querySelector('#recoverSuccess');
            const ee = overlay.querySelector('#recoverError');
            if (ee) ee.style.display = 'none';
            if (se) {
                se.innerHTML = `<strong>密码已重置</strong><br>新密码：<code style="background:rgba(99,102,241,0.2);padding:2px 8px;border-radius:4px;font-size:1.1em;">${result.new_password}</code><br><span style="font-size:0.85em;color:var(--text-muted);">请妥善保管，登录后可修改密码</span>`;
                se.style.display = 'block';
            }
        } catch (err) { this._showError(overlay, 'authPanelRecover', 'recoverError', err.message); }
        finally { btn.disabled = false; btn.textContent = '找回密码'; }
    },

    /* ========== 用户设置弹窗 ========== */
    _showSettingsModal() {
        this._hideSettingsModal();
        const user = this.state.user;
        if (!user) return;

        const avatarHtml = user.avatar_url
            ? `<img src="${Utils.escapeHtml(user.avatar_url)}" alt="" style="width:100%;height:100%;object-fit:cover;" />`
            : `<span style="font-size:1.6em;font-weight:700;">${(user.display_name || user.username)[0].toUpperCase()}</span>`;

        const overlay = document.createElement('div');
        overlay.className = 'auth-modal-overlay';
        overlay.id = 'settingsModalOverlay';
        overlay.innerHTML = `
            <div class="auth-modal settings-modal glass-card">
                <button class="auth-modal-close" id="btnSettingsClose">&times;</button>
                <h2 style="margin-bottom:20px;text-align:center;color:#fff;">用户设置</h2>

                <!-- 头像编辑 -->
                <div class="settings-avatar-section">
                    <div class="settings-avatar-preview" id="settingsAvatarPreview">
                        ${avatarHtml}
                    </div>
                    <div class="settings-avatar-actions">
                        <button class="btn-sm" id="btnUploadAvatar">📷 上传头像</button>
                        ${user.avatar_url ? '<button class="btn-sm btn-sm-danger" id="btnRemoveAvatar">移除头像</button>' : ''}
                    </div>
                    <span class="settings-avatar-label">@${Utils.escapeHtml(user.username)}</span>
                    <input type="file" id="avatarFileInput" accept="image/png,image/jpeg,image/gif,image/webp" style="display:none;">
                </div>

                <!-- 基本信息 -->
                <div class="settings-section-title">基本信息</div>
                <div class="auth-input-group">
                    <label class="form-label">显示名称</label>
                    <input type="text" class="form-input" id="settingsDisplayName" value="${Utils.escapeHtml(user.display_name || '')}" placeholder="设置显示名称">
                </div>
                <div class="auth-input-group">
                    <label class="form-label">邮箱</label>
                    <input type="email" class="form-input" id="settingsEmail" value="${Utils.escapeHtml(user.email || '')}" placeholder="请输入邮箱">
                </div>

                <!-- 修改密码 -->
                <div class="settings-section-title">修改密码</div>
                <div class="auth-input-group">
                    <label class="form-label">新密码</label>
                    <input type="password" class="form-input" id="settingsNewPassword" placeholder="输入新密码（至少6位，留空不修改）" autocomplete="new-password">
                </div>
                <div class="auth-input-group">
                    <label class="form-label">确认新密码</label>
                    <input type="password" class="form-input" id="settingsNewPasswordConfirm" placeholder="再次输入新密码" autocomplete="new-password">
                </div>

                <div class="auth-error" id="settingsError" style="display:none;"></div>
                <div class="auth-success" id="settingsSuccess" style="display:none;"></div>
                <button class="btn-primary btn-block" id="btnSaveSettings">保存设置</button>
                <p style="text-align:center;margin-top:12px;font-size:0.78em;color:var(--text-muted);">
                    注册时间：${user.created_at ? new Date(user.created_at).toLocaleString('zh-CN') : '--'}
                </p>
            </div>
        `;
        document.body.appendChild(overlay);

        // 绑定关闭
        overlay.querySelector('#btnSettingsClose').addEventListener('click', () => this._hideSettingsModal());
        overlay.addEventListener('click', (e) => { if (e.target === overlay) this._hideSettingsModal(); });

        // 头像上传
        const fileInput = overlay.querySelector('#avatarFileInput');
        overlay.querySelector('#btnUploadAvatar').addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', () => {
            if (fileInput.files && fileInput.files[0]) {
                this._showAvatarCropUI(overlay, fileInput.files[0]);
            }
        });

        // 移除头像
        const btnRemove = overlay.querySelector('#btnRemoveAvatar');
        if (btnRemove) {
            btnRemove.addEventListener('click', async () => {
                try {
                    // 设为空头像
                    await API.authUpdateMe({ avatar_url: '' });
                    this.state.user.avatar_url = '';
                    this._renderAll();
                    this._hideSettingsModal();
                    Utils.toast('头像已移除', 'success');
                } catch (err) {
                    Utils.toast('移除失败: ' + err.message, 'error');
                }
            });
        }

        // 保存设置
        overlay.querySelector('#btnSaveSettings').addEventListener('click', async () => {
            const displayName = overlay.querySelector('#settingsDisplayName').value.trim();
            const email = overlay.querySelector('#settingsEmail').value.trim();
            const newPassword = overlay.querySelector('#settingsNewPassword').value;
            const newPasswordConfirm = overlay.querySelector('#settingsNewPasswordConfirm').value;

            const errorEl = overlay.querySelector('#settingsError');
            const successEl = overlay.querySelector('#settingsSuccess');
            errorEl.style.display = 'none';
            successEl.style.display = 'none';

            if (newPassword) {
                if (newPassword.length < 6) {
                    errorEl.textContent = '新密码长度至少6位';
                    errorEl.style.display = 'block';
                    return;
                }
                if (newPassword !== newPasswordConfirm) {
                    errorEl.textContent = '两次输入的密码不一致';
                    errorEl.style.display = 'block';
                    return;
                }
            }

            const btn = overlay.querySelector('#btnSaveSettings');
            btn.disabled = true; btn.textContent = '保存中...';
            try {
                const data = { display_name: displayName, email };
                if (newPassword) { data.password = newPassword; data.password_confirm = newPasswordConfirm; }
                await this.updateProfile(data);
                successEl.textContent = '设置已保存';
                successEl.style.display = 'block';
                setTimeout(() => this._hideSettingsModal(), 1000);
                Utils.toast('用户设置已更新', 'success');
            } catch (err) {
                errorEl.textContent = err.message;
                errorEl.style.display = 'block';
            } finally {
                btn.disabled = false; btn.textContent = '保存设置';
            }
        });

        overlay.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') overlay.querySelector('#btnSaveSettings').click();
        });
    },

    _hideSettingsModal() {
        const o = document.getElementById('settingsModalOverlay');
        if (o) o.remove();
        // 同时清理裁剪UI
        const crop = document.getElementById('avatarCropOverlay');
        if (crop) crop.remove();
    },

    /* ========== 头像裁剪上传 ========== */
    _showAvatarCropUI(settingsOverlay, file) {
        // 移除旧裁剪UI
        const old = document.getElementById('avatarCropOverlay');
        if (old) old.remove();

        const reader = new FileReader();
        reader.onload = (ev) => {
            const imgSrc = ev.target.result;
            const cropOverlay = document.createElement('div');
            cropOverlay.className = 'avatar-crop-overlay';
            cropOverlay.id = 'avatarCropOverlay';
            cropOverlay.innerHTML = `
                <div class="avatar-crop-modal glass-card">
                    <h3 style="text-align:center;color:#fff;margin-bottom:12px;">裁剪头像</h3>
                    <p style="text-align:center;color:var(--text-muted);font-size:0.82em;margin-bottom:14px;">拖动图片调整位置 · 滑块缩放大小</p>
                    <div class="avatar-crop-stage" id="avatarCropStage">
                        <canvas id="avatarCropCanvas"></canvas>
                        <div class="avatar-crop-mask"></div>
                    </div>
                    <div class="avatar-crop-controls">
                        <label class="form-label" style="margin:0;">缩放</label>
                        <input type="range" id="avatarCropZoom" min="50" max="200" value="100" step="1">
                        <span id="avatarCropZoomVal" style="color:var(--text-muted);font-size:0.82em;">100%</span>
                    </div>
                    <div class="avatar-crop-btns">
                        <button class="btn-sm" id="btnCropCancel">取消</button>
                        <button class="btn-primary" id="btnCropConfirm">确认裁剪</button>
                    </div>
                </div>
            `;
            document.body.appendChild(cropOverlay);

            const canvas = cropOverlay.querySelector('#avatarCropCanvas');
            const stage = cropOverlay.querySelector('#avatarCropStage');
            const zoomSlider = cropOverlay.querySelector('#avatarCropZoom');
            const zoomVal = cropOverlay.querySelector('#avatarCropZoomVal');
            const ctx = canvas.getContext('2d');

            // 裁剪区域大小（圆的直径）
            const CROP_SIZE = 200;
            let scale = 1.0;
            let offsetX = 0, offsetY = 0;
            let dragging = false, dragStartX = 0, dragStartY = 0, startOffsetX = 0, startOffsetY = 0;

            const img = new Image();
            img.onload = () => {
                canvas.width = CROP_SIZE;
                canvas.height = CROP_SIZE;

                // 初始缩放：使图片短边填满裁剪区域
                const minDim = Math.min(img.width, img.height);
                scale = CROP_SIZE / minDim;
                // 居中
                offsetX = (img.width * scale - CROP_SIZE) / 2;
                offsetY = (img.height * scale - CROP_SIZE) / 2;

                zoomSlider.value = Math.round(scale * 100);
                zoomVal.textContent = zoomSlider.value + '%';
                draw();

                // 拖拽
                const getPos = (e) => {
                    const rect = canvas.getBoundingClientRect();
                    return { x: (e.touches ? e.touches[0].clientX : e.clientX) - rect.left,
                             y: (e.touches ? e.touches[0].clientY : e.clientY) - rect.top };
                };
                const onDown = (e) => {
                    e.preventDefault();
                    dragging = true;
                    const p = getPos(e);
                    dragStartX = p.x; dragStartY = p.y;
                    startOffsetX = offsetX; startOffsetY = offsetY;
                };
                const onMove = (e) => {
                    if (!dragging) return;
                    e.preventDefault();
                    const p = getPos(e);
                    offsetX = startOffsetX - (p.x - dragStartX);
                    offsetY = startOffsetY - (p.y - dragStartY);
                    draw();
                };
                const onUp = () => { dragging = false; };

                canvas.addEventListener('mousedown', onDown);
                canvas.addEventListener('mousemove', onMove);
                canvas.addEventListener('mouseup', onUp);
                canvas.addEventListener('mouseleave', onUp);
                canvas.addEventListener('touchstart', onDown, { passive: false });
                canvas.addEventListener('touchmove', onMove, { passive: false });
                canvas.addEventListener('touchend', onUp);

                // 缩放
                zoomSlider.addEventListener('input', () => {
                    const newScale = parseInt(zoomSlider.value) / 100;
                    // 以中心为基准调整偏移
                    const cx = offsetX + CROP_SIZE / 2;
                    const cy = offsetY + CROP_SIZE / 2;
                    offsetX = cx - (cx / scale) * newScale;
                    offsetY = cy - (cy / scale) * newScale;
                    scale = newScale;
                    zoomVal.textContent = zoomSlider.value + '%';
                    draw();
                });
            };
            img.src = imgSrc;

            function draw() {
                ctx.clearRect(0, 0, CROP_SIZE, CROP_SIZE);
                // 绘制图片
                ctx.save();
                ctx.beginPath();
                ctx.arc(CROP_SIZE / 2, CROP_SIZE / 2, CROP_SIZE / 2, 0, Math.PI * 2);
                ctx.clip();
                ctx.drawImage(img, -offsetX, -offsetY, img.width * scale, img.height * scale);
                ctx.restore();
                // 边框
                ctx.beginPath();
                ctx.arc(CROP_SIZE / 2, CROP_SIZE / 2, CROP_SIZE / 2 - 1, 0, Math.PI * 2);
                ctx.strokeStyle = 'rgba(99,102,241,0.6)';
                ctx.lineWidth = 2;
                ctx.stroke();
            }

            // 取消
            cropOverlay.querySelector('#btnCropCancel').addEventListener('click', () => cropOverlay.remove());
            cropOverlay.addEventListener('click', (e) => { if (e.target === cropOverlay) cropOverlay.remove(); });

            // 确认裁剪
            cropOverlay.querySelector('#btnCropConfirm').addEventListener('click', async () => {
                // 从 canvas 导出裁剪后的圆形图片
                const outCanvas = document.createElement('canvas');
                outCanvas.width = CROP_SIZE;
                outCanvas.height = CROP_SIZE;
                const outCtx = outCanvas.getContext('2d');
                outCtx.beginPath();
                outCtx.arc(CROP_SIZE / 2, CROP_SIZE / 2, CROP_SIZE / 2, 0, Math.PI * 2);
                outCtx.clip();
                outCtx.drawImage(img, -offsetX, -offsetY, img.width * scale, img.height * scale);

                outCanvas.toBlob(async (blob) => {
                    if (!blob) {
                        Utils.toast('裁剪失败', 'error');
                        return;
                    }
                    try {
                        const formData = new FormData();
                        formData.append('file', blob, 'avatar.png');
                        // 使用 fetch 直接发送（API.uploadAvatar 需要 multipart）
                        const url = '/api/auth/avatar';
                        const resp = await fetch(url, {
                            method: 'POST',
                            headers: { 'Authorization': 'Bearer ' + this.state.token },
                            body: formData,
                        });
                        if (!resp.ok) {
                            const err = await resp.json().catch(() => ({}));
                            throw new Error(err.detail || '上传失败');
                        }
                        const result = await resp.json();
                        this.state.user.avatar_url = result.avatar_url;
                        this._renderAll();
                        // 更新设置弹窗中的预览
                        const preview = settingsOverlay.querySelector('#settingsAvatarPreview');
                        if (preview) {
                            preview.innerHTML = `<img src="${result.avatar_url}?t=${Date.now()}" alt="" style="width:100%;height:100%;object-fit:cover;" />`;
                        }
                        cropOverlay.remove();
                        Utils.toast('头像已更新', 'success');
                    } catch (err) {
                        Utils.toast('头像上传失败: ' + err.message, 'error');
                    }
                }, 'image/png');
            });
        };
        reader.readAsDataURL(file);
    },

    /* ========== 公共方法 ========== */
    getToken() { return this.state.token; },
    isLoggedIn() { return this.state.loggedIn; },
};

window.Auth = Auth;
