/**
 * controlBar.js - UI 控制栏
 * 
 * 职责：
 * - 提供“播放/暂停”、“下一轮”、“上一轮”、“重置”按钮。
 * - 显示当前轮次信息（如 “Round 3 / 20”）。
 * - 绑定 SceneManager 的对应方法，实现交互控制。
 * 
 * 特点：
 * - 纯 PixiJS 绘图，无需外部图片。
 * - 所有元素放到一个容器，方便统一显示/隐藏。
 */

(function() {
    class ControlBar {
        /**
         * @param {SceneManager} sceneManager - 状态机实例，用于调用控制方法
         */
        constructor(sceneManager) {
            this.sceneManager = sceneManager;

            // 主容器
            this.container = new PIXI.Container();
            this.container.x = 0;
            this.container.y = CONFIG.LAYOUT.CONTROL_BAR_Y; // 顶部位置

            // 按钮引用
            this.btnPlayPause = null;
            this.btnNext = null;
            this.btnPrev = null;
            this.btnReset = null;
            this.roundInfo = null;

            this._drawButtons();
            this._drawRoundInfo();
        }

        /** 绘制四个控制按钮 */
        _drawButtons() {
            const btnY = 0;
            const btnSize = 30;  // 按钮方形边长
            const gap = 10;
            // 从左到右依次：播放暂停、上一轮、下一轮、重置
            const startX = CONFIG.WIDTH / 2 - 140; // 居中偏左

            // --- 播放/暂停按钮 ---
            this.btnPlayPause = this._createButton(startX, btnY, btnSize, '▶');
            this.btnPlayPause.on('pointerdown', () => {
                if (this.sceneManager.autoPlay && !this.sceneManager.paused) {
                    this.sceneManager.pause();
                } else {
                    if (this.sceneManager.state === 'IDLE' || this.sceneManager.state === 'FINISHED') {
                        this.sceneManager.play();
                    } else {
                        this.sceneManager.resume();
                    }
                }
            });
            this.container.addChild(this.btnPlayPause);

            // --- 上一轮按钮 ---
            this.btnPrev = this._createButton(startX + (btnSize + gap), btnY, btnSize, '◀◀');
            this.btnPrev.on('pointerdown', () => {
                const target = this.sceneManager.currentRoundIndex - 1;
                if (target >= 0) {
                    this.sceneManager.gotoRound(target);
                }
            });
            this.container.addChild(this.btnPrev);

            // --- 下一轮按钮 ---
            this.btnNext = this._createButton(startX + 2*(btnSize + gap), btnY, btnSize, '▶▶');
            this.btnNext.on('pointerdown', () => {
                const target = this.sceneManager.currentRoundIndex + 1;
                if (target < this.sceneManager.totalRounds) {
                    this.sceneManager.gotoRound(target);
                }
            });
            this.container.addChild(this.btnNext);

            // --- 重置按钮 ---
            this.btnReset = this._createButton(startX + 3*(btnSize + gap), btnY, btnSize, '↺');
            this.btnReset.on('pointerdown', () => {
                this.sceneManager.reset();
            });
            this.container.addChild(this.btnReset);
        }

        /** 创建单个按钮图形（方形背景+文字） */
        _createButton(x, y, size, label) {
            const btn = new PIXI.Container();
            btn.x = x;
            btn.y = y;
            btn.interactive = true;
            btn.cursor = 'pointer';

            // 按钮背景
            const bg = new PIXI.Graphics();
            bg.beginFill(0x333366);
            bg.drawRoundedRect(0, 0, size, size, 6);
            bg.endFill();
            btn.addChild(bg);

            // 按钮文字
            const text = new PIXI.Text(label, {
                fontFamily: 'Arial',
                fontSize: 12,
                fill: '#ffffff',
                align: 'center'
            });
            text.anchor.set(0.5);
            text.x = size / 2;
            text.y = size / 2;
            btn.addChild(text);

            return btn;
        }

        /** 绘制轮次信息文本（右上角） */
        _drawRoundInfo() {
            this.roundInfo = new PIXI.Text('Round 0 / 0', CONFIG.FONT_STYLE.ROUND_INFO);
            this.roundInfo.anchor.set(1, 0); // 右对齐
            this.roundInfo.x = CONFIG.WIDTH - 20;
            this.roundInfo.y = 0;
            this.container.addChild(this.roundInfo);
        }

        /**
         * 更新按钮状态和轮次信息
         * 此方法应在 ticker 或 SceneManager 状态变化时调用
         */
        refresh() {
            const sm = this.sceneManager;
            const current = sm.currentRoundIndex + 1;
            const total = sm.totalRounds;

            // 更新轮次文本
            this.roundInfo.text = `Round ${current} / ${total}`;

            // 更新播放暂停按钮文字
            const label = (sm.autoPlay && !sm.paused) ? '⏸' : '▶';
            if (this.btnPlayPause.children[1]) {
                this.btnPlayPause.children[1].text = label;
            }
        }

        /** 将控制栏添加到父容器 */
        addTo(parent) {
            parent.addChild(this.container);
        }
    }

    window.ControlBar = ControlBar;
})();