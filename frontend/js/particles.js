/**
 * DataVision Pro - 粒子背景效果模块
 * Canvas动态星空粒子背景
 */

const ParticleBackground = {
    canvas: null,
    ctx: null,
    particles: [],
    animationId: null,

    config: {
        particleCount: 80,
        minRadius: 1,
        maxRadius: 3,
        minSpeed: 0.2,
        maxSpeed: 0.8,
        lineDistance: 120,
        lineOpacity: 0.15,
        colors: ['#6366f1', '#8b5cf6', '#ec4899', '#38bdf8', '#ffffff'],
    },

    /**
     * 初始化粒子背景
     */
    init() {
        this.canvas = document.getElementById('particleCanvas');
        if (!this.canvas) return;

        this.ctx = this.canvas.getContext('2d');
        this.resize();
        this.createParticles();
        this.animate();

        window.addEventListener('resize', Utils.debounce(() => this.resize(), 200));
    },

    /**
     * 调整画布大小
     */
    resize() {
        if (!this.canvas) return;
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    },

    /**
     * 创建粒子
     */
    createParticles() {
        this.particles = [];
        const count = Math.floor(
            this.config.particleCount * (window.innerWidth / 1920)
        );

        for (let i = 0; i < count; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                radius: this.config.minRadius + Math.random() * (this.config.maxRadius - this.config.minRadius),
                speedX: (Math.random() - 0.5) * this.config.maxSpeed * 2,
                speedY: (Math.random() - 0.5) * this.config.maxSpeed * 2,
                color: this.config.colors[Math.floor(Math.random() * this.config.colors.length)],
                opacity: 0.3 + Math.random() * 0.7,
                twinkleSpeed: 0.005 + Math.random() * 0.02,
                twinkleOffset: Math.random() * Math.PI * 2,
            });
        }
    },

    /**
     * 动画循环
     */
    animate() {
        if (!this.ctx || !this.canvas) return;

        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // 更新和绘制粒子
        for (let i = 0; i < this.particles.length; i++) {
            const p = this.particles[i];

            // 更新位置
            p.x += p.speedX;
            p.y += p.speedY;

            // 边界环绕
            if (p.x < -10) p.x = this.canvas.width + 10;
            if (p.x > this.canvas.width + 10) p.x = -10;
            if (p.y < -10) p.y = this.canvas.height + 10;
            if (p.y > this.canvas.height + 10) p.y = -10;

            // 闪烁效果
            const twinkle = Math.sin(Date.now() * p.twinkleSpeed + p.twinkleOffset) * 0.3 + 0.7;
            const currentOpacity = p.opacity * twinkle;

            // 绘制粒子
            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
            this.ctx.fillStyle = p.color;
            this.ctx.globalAlpha = currentOpacity;
            this.ctx.fill();
            this.ctx.globalAlpha = 1;

            // 添加光晕
            if (p.radius > 2) {
                this.ctx.beginPath();
                this.ctx.arc(p.x, p.y, p.radius * 2.5, 0, Math.PI * 2);
                this.ctx.fillStyle = p.color;
                this.ctx.globalAlpha = currentOpacity * 0.15;
                this.ctx.fill();
                this.ctx.globalAlpha = 1;
            }
        }

        // 绘制连线
        this.ctx.strokeStyle = 'rgba(99, 102, 241, 0.06)';
        this.ctx.lineWidth = 0.5;

        for (let i = 0; i < this.particles.length; i++) {
            for (let j = i + 1; j < this.particles.length; j++) {
                const dx = this.particles[i].x - this.particles[j].x;
                const dy = this.particles[i].y - this.particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < this.config.lineDistance) {
                    const opacity = (1 - dist / this.config.lineDistance) * this.config.lineOpacity;
                    this.ctx.strokeStyle = `rgba(99, 102, 241, ${opacity})`;
                    this.ctx.beginPath();
                    this.ctx.moveTo(this.particles[i].x, this.particles[i].y);
                    this.ctx.lineTo(this.particles[j].x, this.particles[j].y);
                    this.ctx.stroke();
                }
            }
        }

        this.animationId = requestAnimationFrame(() => this.animate());
    },

    /**
     * 停止动画
     */
    stop() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
    },
};

// 由 App.init() 显式调用 Particles.init()，避免重复初始化
window.ParticleBackground = ParticleBackground;
window.Particles = ParticleBackground;
