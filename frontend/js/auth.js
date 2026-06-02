/**
 * Data Analysis System - 用户认证模块
 * 登录、注册、密码找回、用户设置、免登录记忆
 */
const Auth = {
    state: {
        loggedIn: false,
        user: null,
        token: null,
    },

    init() {
        // 检查本地存储中的令牌，尝试自动登录
        const saved = this._loadToken();
        if (saved) {
            this.state.token = saved;
            this._checkAndRestore();
        }
        this._renderWelcomeAuth();
    },

    /* ========== 令牌持久化 ========== */
    _loadToken() {
        try {
            const data = localStorage.getItem('da_auth');
            if (data) {
                const parsed = JSON.parse(data);
                if (parsed.token && parsed.expires) {
                    // 检查是否过期
                    if (new Date(parsed.expires).getTime() > Date.now()) {
                        return parsed.token;
                    }
                    // 过期则清除
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
        try {
            localStorage.removeItem('da_auth');
        } catch (e) { /* ignore */ }
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
            // 网络错误时不清除令牌，下次再试
            console.warn('Auth check failed:', e);
        }
    },

    /* ========== 登录 ========== */
    async login(username, password, remember = false) {
        const result = await API.authLogin(username, password, remember);
        this.state.token = result.token;
        this.state.user = result.user;
        this.state.loggedIn = true;
        const rememberDays = remember ? 365 : 30;
        this._saveToken(result.token, rememberDays);
        this._renderAll();
        this._hideAuthModal();
        return result;
    },

    /* ========== 注册 ========== */
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

    /* ========== 找回密码 ========== */
    async recoverPassword(username) {
        const result = await API.authRecover(username);
        return result;
    },

    /* ========== 退出登录 ========== */
    async logout() {
        try {
            if (this.state.token) {
                await API.authLogout();
            }
        } catch (e) { /* ignore */ }
        this.state.loggedIn = false;
        this.state.user = null;
        this.state.token = null;
        this._clearToken();
        this._renderAll();
    },

    /* ========== 更新用户信息 ========== */
    async updateProfile(data) {
        const result = await API.authUpdateMe(data);
        this.state.user = result;
        this._renderAll();
        return result;
    },

    /* ========== UI 渲染 ========== */

    /** 渲染所有 auth 相关 UI */
    _renderAll() {
        this._renderWelcomeAuth();
        this._renderTopbarAvatar();
    },

    /** 欢迎页右上方：注册/登录按钮 + 头像 */
    _renderWelcomeAuth() {
        const container = document.getElementById('welcomeAuthArea');
        if (!container) return;

        if (this.state.loggedIn && this.state.user) {
            const initial = (this.state.user.display_name || this.state.user.username)[0].toUpperCase();
            container.innerHTML = `
                <div class="welcome-avatar logged-in" title="${Utils.escapeHtml(this.state.user.display_name || this.state.user.username)}">
                    ${initial}
                </div>
                <span class="welcome-user-name">${Utils.escapeHtml(this.state.user.display_name || this.state.user.username)}</span>
            `;
        } else {
            container.innerHTML = `
                <button class="welcome-auth-btn" id="btnWelcomeLogin">登录</button>
                <button class="welcome-auth-btn welcome-auth-btn-outline" id="btnWelcomeRegister">注册</button>
                <div class="welcome-avatar default" title="未登录">?</div>
            `;
            // 绑定事件
            setTimeout(() => {
                const btnLogin = document.getElementById('btnWelcomeLogin');
                const btnRegister = document.getElementById('btnWelcomeRegister');
                if (btnLogin) btnLogin.addEventListener('click', () => this._showAuthModal('login'));
                if (btnRegister) btnRegister.addEventListener('click', () => this._showAuthModal('register'));
            }, 0);
        }
    },

    /** 仪表盘顶栏：头像 + 下拉菜单 */
    _renderTopbarAvatar() {
        const avatarEl = document.getElementById('topbarUserAvatar');
        if (!avatarEl) return;

        if (this.state.loggedIn && this.state.user) {
            const initial = (this.state.user.display_name || this.state.user.username)[0].toUpperCase();
            avatarEl.innerHTML = `
                <div class="user-avatar logged-in-avatar" id="btnUserMenu" title="${Utils.escapeHtml(this.state.user.display_name || this.state.user.username)}">
                    ${initial}
                </div>
                <div class="user-dropdown" id="userDropdown" style="display:none;">
                    <div class="user-dropdown-header">
                        <div class="user-dropdown-avatar">${initial}</div>
                        <div>
                            <div class="user-dropdown-name">${Utils.escapeHtml(this.state.user.display_name || this.state.user.username)}</div>
                            <div class="user-dropdown-username">@${Utils.escapeHtml(this.state.user.username)}</div>
                        </div>
                    </div>
                    <div class="user-dropdown-item" id="btnUserSettings">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
                        <span>设置</span>
                    </div>
                    <div class="user-dropdown-item user-dropdown-item-danger" id="btnUserLogout">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
                        <span>退出登录</span>
                    </div>
                </div>
            `;
            // 绑定事件
            setTimeout(() => this._bindAvatarEvents(), 0);
        } else {
            avatarEl.innerHTML = `
                <div class="user-avatar default-avatar" title="未登录">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                </div>
            `;
        }
    },

    _bindAvatarEvents() {
        const btnMenu = document.getElementById('btnUserMenu');
        const dropdown = document.getElementById('userDropdown');
        const btnSettings = document.getElementById('btnUserSettings');
        const btnLogout = document.getElementById('btnUserLogout');

        if (btnMenu && dropdown) {
            btnMenu.addEventListener('click', (e) => {
                e.stopPropagation();
                dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
            });
            document.addEventListener('click', () => {
                if (dropdown) dropdown.style.display = 'none';
            });
        }
        if (btnSettings) {
            btnSettings.addEventListener('click', (e) => {
                e.stopPropagation();
                if (dropdown) dropdown.style.display = 'none';
                this._showSettingsModal();
            });
        }
        if (btnLogout) {
            btnLogout.addEventListener('click', async (e) => {
                e.stopPropagation();
                if (dropdown) dropdown.style.display = 'none';
                await this.logout();
                // 不跳回欢迎页，只更新头像
            });
        }
    },

    /* ========== 认证弹窗（登录/注册/找回密码） ========== */
    _showAuthModal(tab = 'login') {
        // 如果已存在弹窗则先移除
        this._hideAuthModal();

        const overlay = document.createElement('div');
        overlay.className = 'auth-modal-overlay';
        overlay.id = 'authModalOverlay';
        overlay.innerHTML = `
            <div class="auth-modal glass-card">
                <button class="auth-modal-close" id="btnAuthClose">&times;</button>
                <div class="auth-tabs">
                    <button class="auth-tab ${tab === 'login' ? 'active' : ''}" data-auth-tab="login">登录</button>
                    <button class="auth-tab ${tab === 'register' ? 'active' : ''}" data-auth-tab="register">注册</button>
                    <button class="auth-tab ${tab === 'recover' ? 'active' : ''}" data-auth-tab="recover">找回密码</button>
                </div>
                <!-- 登录表单 -->
                <div class="auth-panel" id="authPanelLogin" style="display:${tab === 'login' ? 'block' : 'none'};">
                    <div class="auth-input-group">
                        <label class="form-label">用户名</label>
                        <input type="text" class="form-input" id="loginUsername" placeholder="请输入用户名" autocomplete="username">
                    </div>
                    <div class="auth-input-group">
                        <label class="form-label">密码</label>
                        <input type="password" class="form-input" id="loginPassword" placeholder="请输入密码" autocomplete="current-password">
                    </div>
                    <div class="auth-options">
                        <label class="checkbox-label">
                            <input type="checkbox" id="loginRemember"> <span>记住登录（免登录）</span>
                        </label>
                    </div>
                    <div class="auth-error" id="loginError" style="display:none;"></div>
                    <button class="btn-primary btn-block" id="btnLogin">登 录</button>
                </div>
                <!-- 注册表单 -->
                <div class="auth-panel" id="authPanelRegister" style="display:${tab === 'register' ? 'block' : 'none'};">
                    <div class="auth-input-group">
                        <label class="form-label">用户名</label>
                        <input type="text" class="form-input" id="regUsername" placeholder="2-50个字符，支持中英文" autocomplete="off">
                    </div>
                    <div class="auth-input-group">
                        <label class="form-label">密码</label>
                        <input type="password" class="form-input" id="regPassword" placeholder="至少6位密码" autocomplete="new-password">
                    </div>
                    <div class="auth-input-group">
                        <label class="form-label">确认密码</label>
                        <input type="password" class="form-input" id="regPasswordConfirm" placeholder="再次输入密码" autocomplete="new-password">
                    </div>
                    <div class="auth-error" id="regError" style="display:none;"></div>
                    <button class="btn-primary btn-block" id="btnRegister">注 册</button>
                </div>
                <!-- 找回密码表单 -->
                <div class="auth-panel" id="authPanelRecover" style="display:${tab === 'recover' ? 'block' : 'none'};">
                    <p style="color:var(--text-muted);font-size:0.85em;margin-bottom:14px;">输入用户名，系统将为您重置密码</p>
                    <div class="auth-input-group">
                        <label class="form-label">用户名</label>
                        <input type="text" class="form-input" id="recoverUsername" placeholder="请输入用户名">
                    </div>
                    <div class="auth-error" id="recoverError" style="display:none;"></div>
                    <div class="auth-success" id="recoverSuccess" style="display:none;"></div>
                    <button class="btn-primary btn-block" id="btnRecover">找回密码</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        // 绑定关闭
        overlay.querySelector('#btnAuthClose').addEventListener('click', () => this._hideAuthModal());
        overlay.addEventListener('click', (e) => { if (e.target === overlay) this._hideAuthModal(); });

        // 绑定 Tab 切换
        overlay.querySelectorAll('.auth-tab').forEach(btn => {
            btn.addEventListener('click', () => {
                overlay.querySelectorAll('.auth-tab').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const targetTab = btn.dataset.authTab;
                ['Login', 'Register', 'Recover'].forEach(t => {
                    const panel = overlay.querySelector('#authPanel' + t);
                    if (panel) panel.style.display = t.toLowerCase() === targetTab ? 'block' : 'none';
                });
                // 清除错误信息
                overlay.querySelectorAll('.auth-error').forEach(el => { el.style.display = 'none'; el.textContent = ''; });
                const successEl = overlay.querySelector('#recoverSuccess');
                if (successEl) { successEl.style.display = 'none'; successEl.textContent = ''; }
            });
        });

        // 绑定表单提交
        overlay.querySelector('#btnLogin').addEventListener('click', () => this._handleLogin(overlay));
        overlay.querySelector('#btnRegister').addEventListener('click', () => this._handleRegister(overlay));
        overlay.querySelector('#btnRecover').addEventListener('click', () => this._handleRecover(overlay));

        // Enter 键提交
        overlay.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const activeTab = overlay.querySelector('.auth-tab.active');
                if (activeTab) {
                    const t = activeTab.dataset.authTab;
                    if (t === 'login') this._handleLogin(overlay);
                    else if (t === 'register') this._handleRegister(overlay);
                    else if (t === 'recover') this._handleRecover(overlay);
                }
            }
        });

        // 聚焦第一个输入框
        setTimeout(() => {
            const firstInput = overlay.querySelector('.auth-panel[style*="block"] input');
            if (firstInput) firstInput.focus();
        }, 100);
    },

    _hideAuthModal() {
        const overlay = document.getElementById('authModalOverlay');
        if (overlay) overlay.remove();
    },

    _showError(overlay, panelId, errorId, message) {
        const panel = overlay.querySelector('#' + panelId);
        const errorEl = overlay.querySelector('#' + errorId);
        if (panel && errorEl) {
            errorEl.textContent = message;
            errorEl.style.display = 'block';
        }
    },

    async _handleLogin(overlay) {
        const username = overlay.querySelector('#loginUsername').value.trim();
        const password = overlay.querySelector('#loginPassword').value;
        const remember = overlay.querySelector('#loginRemember').checked;

        if (!username || !password) {
            this._showError(overlay, 'authPanelLogin', 'loginError', '请输入用户名和密码');
            return;
        }

        const btn = overlay.querySelector('#btnLogin');
        btn.disabled = true;
        btn.textContent = '登录中...';

        try {
            await this.login(username, password, remember);
            Utils.toast('登录成功', 'success');
            // 登录后自动进入仪表盘
            if (typeof App !== 'undefined' && App._enterApp) {
                App._enterApp();
            }
        } catch (err) {
            this._showError(overlay, 'authPanelLogin', 'loginError', err.message);
        } finally {
            btn.disabled = false;
            btn.textContent = '登 录';
        }
    },

    async _handleRegister(overlay) {
        const username = overlay.querySelector('#regUsername').value.trim();
        const password = overlay.querySelector('#regPassword').value;
        const passwordConfirm = overlay.querySelector('#regPasswordConfirm').value;

        if (!username || !password) {
            this._showError(overlay, 'authPanelRegister', 'regError', '请输入用户名和密码');
            return;
        }
        if (password !== passwordConfirm) {
            this._showError(overlay, 'authPanelRegister', 'regError', '两次输入的密码不一致');
            return;
        }
        if (password.length < 6) {
            this._showError(overlay, 'authPanelRegister', 'regError', '密码长度至少6位');
            return;
        }

        const btn = overlay.querySelector('#btnRegister');
        btn.disabled = true;
        btn.textContent = '注册中...';

        try {
            await this.register(username, password, passwordConfirm);
            Utils.toast('注册成功，已自动登录', 'success');
            if (typeof App !== 'undefined' && App._enterApp) {
                App._enterApp();
            }
        } catch (err) {
            this._showError(overlay, 'authPanelRegister', 'regError', err.message);
        } finally {
            btn.disabled = false;
            btn.textContent = '注 册';
        }
    },

    async _handleRecover(overlay) {
        const username = overlay.querySelector('#recoverUsername').value.trim();

        if (!username) {
            this._showError(overlay, 'authPanelRecover', 'recoverError', '请输入用户名');
            return;
        }

        const btn = overlay.querySelector('#btnRecover');
        btn.disabled = true;
        btn.textContent = '处理中...';

        try {
            const result = await this.recoverPassword(username);
            const successEl = overlay.querySelector('#recoverSuccess');
            const errorEl = overlay.querySelector('#recoverError');
            if (errorEl) errorEl.style.display = 'none';
            if (successEl) {
                successEl.innerHTML = `<strong>密码已重置</strong><br>新密码：<code style="background:rgba(99,102,241,0.2);padding:2px 8px;border-radius:4px;font-size:1.1em;">${result.new_password}</code><br><span style="font-size:0.85em;color:var(--text-muted);">请妥善保管，登录后可修改密码</span>`;
                successEl.style.display = 'block';
            }
        } catch (err) {
            this._showError(overlay, 'authPanelRecover', 'recoverError', err.message);
        } finally {
            btn.disabled = false;
            btn.textContent = '找回密码';
        }
    },

    /* ========== 用户设置弹窗 ========== */
    _showSettingsModal() {
        this._hideSettingsModal();

        const user = this.state.user;
        if (!user) return;

        const overlay = document.createElement('div');
        overlay.className = 'auth-modal-overlay';
        overlay.id = 'settingsModalOverlay';
        overlay.innerHTML = `
            <div class="auth-modal settings-modal glass-card">
                <button class="auth-modal-close" id="btnSettingsClose">&times;</button>
                <h2 style="margin-bottom:20px;text-align:center;color:#fff;">用户设置</h2>
                <div class="settings-avatar-section">
                    <div class="settings-avatar-preview">${(user.display_name || user.username)[0].toUpperCase()}</div>
                    <span class="settings-avatar-label">${Utils.escapeHtml(user.username)}</span>
                </div>
                <div class="auth-input-group">
                    <label class="form-label">显示名称</label>
                    <input type="text" class="form-input" id="settingsDisplayName" value="${Utils.escapeHtml(user.display_name || '')}" placeholder="设置显示名称">
                </div>
                <div class="auth-input-group">
                    <label class="form-label">邮箱</label>
                    <input type="email" class="form-input" id="settingsEmail" value="${Utils.escapeHtml(user.email || '')}" placeholder="请输入邮箱">
                </div>
                <div class="auth-input-group">
                    <label class="form-label">新密码</label>
                    <input type="password" class="form-input" id="settingsNewPassword" placeholder="留空不修改密码" autocomplete="new-password">
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

        overlay.querySelector('#btnSettingsClose').addEventListener('click', () => this._hideSettingsModal());
        overlay.addEventListener('click', (e) => { if (e.target === overlay) this._hideSettingsModal(); });

        overlay.querySelector('#btnSaveSettings').addEventListener('click', async () => {
            const displayName = overlay.querySelector('#settingsDisplayName').value.trim();
            const email = overlay.querySelector('#settingsEmail').value.trim();
            const newPassword = overlay.querySelector('#settingsNewPassword').value;
            const newPasswordConfirm = overlay.querySelector('#settingsNewPasswordConfirm').value;

            const errorEl = overlay.querySelector('#settingsError');
            const successEl = overlay.querySelector('#settingsSuccess');
            errorEl.style.display = 'none';
            successEl.style.display = 'none';

            if (newPassword && newPassword !== newPasswordConfirm) {
                errorEl.textContent = '两次输入的密码不一致';
                errorEl.style.display = 'block';
                return;
            }

            const btn = overlay.querySelector('#btnSaveSettings');
            btn.disabled = true;
            btn.textContent = '保存中...';

            try {
                const data = { display_name: displayName, email };
                if (newPassword) {
                    data.password = newPassword;
                    data.password_confirm = newPasswordConfirm;
                }
                await this.updateProfile(data);
                successEl.textContent = '设置已保存';
                successEl.style.display = 'block';
                setTimeout(() => this._hideSettingsModal(), 1000);
                Utils.toast('用户设置已更新', 'success');
            } catch (err) {
                errorEl.textContent = err.message;
                errorEl.style.display = 'block';
            } finally {
                btn.disabled = false;
                btn.textContent = '保存设置';
            }
        });

        overlay.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                overlay.querySelector('#btnSaveSettings').click();
            }
        });
    },

    _hideSettingsModal() {
        const overlay = document.getElementById('settingsModalOverlay');
        if (overlay) overlay.remove();
    },

    /** 获取当前 token（供 API 调用使用） */
    getToken() {
        return this.state.token;
    },

    /** 是否已登录 */
    isLoggedIn() {
        return this.state.loggedIn;
    },
};

window.Auth = Auth;
