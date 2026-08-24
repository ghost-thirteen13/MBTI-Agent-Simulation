/**
 * centerStage.js - 中央对峙区动画
 * 
 * 职责：
 * - 接收双方决策及收益，在画布中央播放碰撞动画。
 * - 不参与状态管理，提供 playRound 方法返回 Promise。
 * - 内部使用 PIXI.Ticker.shared 驱动动画，无需传入 app 引用。
 */

(function() {
    class CenterStage {
        constructor() {
            // 主容器
            this.container = new PIXI.Container();
            this.container.x = CONFIG.LAYOUT.CENTER_X;
            this.container.y = CONFIG.LAYOUT.CENTER_Y;

            // 绘制静态背景元素（中央监狱铁窗暗示）
            this._drawBackground();

            // 动画用临时容器（每轮清空）
            this.animContainer = new PIXI.Container();
            this.container.addChild(this.animContainer);
        }

        /** 绘制中央静态背景：抽象的铁窗网格 + 碰撞区域标记 */
        _drawBackground() {
            const bg = new PIXI.Graphics();
            
            // 中央区域暗色底
            bg.beginFill(0x0a0a1a, 0.5);
            bg.drawRoundedRect(-120, -80, 240, 160, 8);
            bg.endFill();

            // 铁窗竖线
            for (let i = -80; i <= 80; i += 40) {
                bg.lineStyle(1, 0x333355, 0.6);
                bg.moveTo(i, -80);
                bg.lineTo(i, 80);
            }
            // 铁窗横线
            for (let j = -60; j <= 60; j += 40) {
                bg.lineStyle(1, 0x333355, 0.6);
                bg.moveTo(-120, j);
                bg.lineTo(120, j);
            }
            this.container.addChild(bg);
        }

        /**
         * 对外接口：播放一轮碰撞动画
         * @param {string} decA - 左侧决策 ('C' 或 'D')
         * @param {string} decB - 右侧决策 ('C' 或 'D')
         * @param {number} payoffA - 左侧收益
         * @param {number} payoffB - 右侧收益
         * @returns {Promise} 动画完成时 resolve
         */
        playRound(decA, decB, payoffA, payoffB) {
            return new Promise((resolve) => {
                // 清空上一轮动画残留
                this.animContainer.removeChildren();

                // 起点坐标（面板中心相对中央容器偏移）
                const leftStartX = CONFIG.LAYOUT.LEFT_PANEL_X - CONFIG.LAYOUT.CENTER_X;
                const leftStartY = CONFIG.LAYOUT.LEFT_PANEL_Y - CONFIG.LAYOUT.CENTER_Y;
                const rightStartX = CONFIG.LAYOUT.RIGHT_PANEL_X - CONFIG.LAYOUT.CENTER_X;
                const rightStartY = CONFIG.LAYOUT.RIGHT_PANEL_Y - CONFIG.LAYOUT.CENTER_Y;
                const endX = 0; // 碰撞点（容器中心）
                const endY = 0;

                // 创建两个飞行图标
                const iconA = this._createDecisionIcon(decA, leftStartX, leftStartY);
                const iconB = this._createDecisionIcon(decB, rightStartX, rightStartY);
                this.animContainer.addChild(iconA);
                this.animContainer.addChild(iconB);

                // 动画状态
                let elapsed = 0;
                const totalDuration = 1.2; // 秒
                const flyDuration = 0.5;    // 飞行阶段时长
                const flashTime = 0.1;      // 闪光时长

                // 碰撞特效元素（预创建，先隐藏）
                const flash = new PIXI.Graphics();
                flash.visible = false;
                this.animContainer.addChild(flash);

                // 收益文字
                const payoffTextA = new PIXI.Text(payoffA >= 0 ? `+${payoffA}` : `${payoffA}`, {
                    fontFamily: 'Arial', fontSize: 24, fontWeight: 'bold',
                    fill: payoffA >= 0 ? '#4caf50' : '#f44336', align: 'center'
                });
                payoffTextA.anchor.set(0.5);
                payoffTextA.x = endX;
                payoffTextA.y = endY;
                payoffTextA.alpha = 0;
                this.animContainer.addChild(payoffTextA);

                const payoffTextB = new PIXI.Text(payoffB >= 0 ? `+${payoffB}` : `${payoffB}`, {
                    fontFamily: 'Arial', fontSize: 24, fontWeight: 'bold',
                    fill: payoffB >= 0 ? '#4caf50' : '#f44336', align: 'center'
                });
                payoffTextB.anchor.set(0.5);
                payoffTextB.x = endX;
                payoffTextB.y = endY;
                payoffTextB.alpha = 0;
                this.animContainer.addChild(payoffTextB);

                // 动画更新函数
                const update = (delta) => {
                    // delta 是时间因子（60fps 时约为 1），转成秒
                    const dt = delta / PIXI.Ticker.shared.FPS;
                    elapsed += dt;

                    // ---- 飞行阶段 ----
                    if (elapsed <= flyDuration) {
                        const t = elapsed / flyDuration; // 0~1 进度
                        // 使用缓动函数（ease-out cubic）
                        const eased = 1 - Math.pow(1 - t, 3);
                        iconA.x = leftStartX + (endX - leftStartX) * eased;
                        iconA.y = leftStartY + (endY - leftStartY) * eased - Math.sin(t * Math.PI) * 30; // 弧线
                        iconB.x = rightStartX + (endX - rightStartX) * eased;
                        iconB.y = rightStartY + (endY - rightStartY) * eased - Math.sin(t * Math.PI) * 30;

                        // 缩放：由大变小
                        const scale = 1.5 - t * 0.5;
                        iconA.scale.set(scale);
                        iconB.scale.set(scale);
                    }
                    // ---- 碰撞闪光 ----
                    else if (elapsed <= flyDuration + flashTime) {
                        // 移除飞行图标
                        if (iconA.parent) iconA.parent.removeChild(iconA);
                        if (iconB.parent) iconB.parent.removeChild(iconB);

                        // 绘制闪光
                        flash.clear();
                        flash.visible = true;
                        
                        // 根据结果确定光晕颜色
                        let glowColor;
                        if (decA === 'C' && decB === 'C') glowColor = CONFIG.COLORS.COOPERATE;
                        else if (decA === 'D' && decB === 'D') glowColor = CONFIG.COLORS.MUTUAL_BETRAY;
                        else glowColor = CONFIG.COLORS.HISTORY_CD_DC; // 一方背叛

                        flash.beginFill(glowColor, 0.6);
                        flash.drawCircle(0, 0, 40 + Math.random() * 10); // 带随机半径的闪光
                        flash.endFill();

                        // 显示收益文字
                        payoffTextA.alpha = 1;
                        payoffTextB.alpha = 1;
                    }
                    // ---- 结算文字飘动 ----
                    else if (elapsed <= totalDuration) {
                        flash.clear();
                        flash.visible = false;

                        // 文字分别向左右两侧飘动并渐隐
                        const settleProgress = (elapsed - flyDuration - flashTime) / (totalDuration - flyDuration - flashTime);
                        payoffTextA.x = endX - settleProgress * 60;
                        payoffTextA.y = endY - settleProgress * 40;
                        payoffTextA.alpha = 1 - settleProgress * 0.8;
                        payoffTextB.x = endX + settleProgress * 60;
                        payoffTextB.y = endY - settleProgress * 40;
                        payoffTextB.alpha = 1 - settleProgress * 0.8;
                    }
                    // ---- 动画结束 ----
                    else {
                        // 清理所有临时元素
                        this.animContainer.removeChildren();
                        PIXI.Ticker.shared.remove(update);
                        resolve();
                    }
                };

                // 注册 ticker 更新
                PIXI.Ticker.shared.add(update);
            });
        }

        /** 创建决策图标图形（不添加到容器，由调用者添加） */
        _createDecisionIcon(decision, x, y) {
            const icon = new PIXI.Graphics();
            icon.x = x;
            icon.y = y;
            const size = CONFIG.SIZES.DECISION_ICON_SIZE / 2;
            if (decision === 'C') {
                icon.beginFill(CONFIG.COLORS.COOPERATE);
                icon.drawCircle(0, 0, size);
                icon.endFill();
                // 内部勾的简略
                icon.lineStyle(2, 0xffffff);
                icon.moveTo(-5, 0);
                icon.lineTo(-1, 5);
                icon.lineTo(6, -4);
            } else {
                icon.beginFill(CONFIG.COLORS.BETRAY);
                icon.moveTo(0, -size);
                icon.lineTo(size, size);
                icon.lineTo(-size, size);
                icon.closePath();
                icon.endFill();
                // 内部叉
                icon.lineStyle(2, 0xffffff);
                icon.moveTo(-5, -5);
                icon.lineTo(5, 5);
                icon.moveTo(5, -5);
                icon.lineTo(-5, 5);
            }
            return icon;
        }

        /** 添加到指定父容器 */
        addTo(parent) {
            parent.addChild(this.container);
        }
    }

    window.CenterStage = CenterStage;
})();