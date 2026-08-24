/**
 * historyBar.js - 底部历史轨迹条
 * 
 * 职责：
 * - 绘制一条时间轴，用彩色圆点表示每一轮的结果。
 * - 当前轮次高亮显示。
 * - 支持点击圆点跳转到对应轮次（通过回调通知外部）。
 */

(function() {
    class HistoryBar {
        /**
         * @param {Function} onRoundClick - 可选回调，参数为轮次索引(0开始)
         */
        constructor(onRoundClick) {
            this.onRoundClick = onRoundClick || null;

            // 创建主容器
            this.container = new PIXI.Container();
            this.container.x = 0;
            this.container.y = CONFIG.LAYOUT.HISTORY_BAR_Y;

            // 数据
            this.rounds = [];           // 存储每轮记录 { roundIndex, resultType, data }
            this.currentRoundIndex = -1;

            // 绘制背景横线
            this._drawBaseline();

            // 圆点容器（用来统一管理子元素）
            this.dotsContainer = new PIXI.Container();
            this.container.addChild(this.dotsContainer);

            // 高亮指示器
            this.highlight = new PIXI.Graphics();
            this.container.addChild(this.highlight);
        }

        /** 绘制底部横线背景 */
        _drawBaseline() {
            const lineY = 0; // 圆点中心所在 Y
            const startX = CONFIG.LAYOUT.HISTORY_DOT_START_X - 20;
            const endX = CONFIG.WIDTH - 40;
            const baseline = new PIXI.Graphics();
            baseline.lineStyle(1, 0x555555, 0.5);
            baseline.moveTo(startX, lineY);
            baseline.lineTo(endX, lineY);
            this.container.addChild(baseline);
        }

        /**
         * 添加一个历史轮次标记
         * @param {number} roundIndex - 轮次索引（从0开始）    
         * @param {string} resultType - 结果类型: 'CC', 'CD', 'DC', 'DD'
         * @param {Object} data       - 该轮完整数据（可选，用于tooltip或跳转）
         */
        addRoundMarker(roundIndex, resultType, data) {
            // 确定圆点颜色
            let color;
            switch (resultType) {
                case 'CC': color = CONFIG.COLORS.HISTORY_CC; break;
                case 'CD':
                case 'DC': color = CONFIG.COLORS.HISTORY_CD_DC; break;
                case 'DD': color = CONFIG.COLORS.HISTORY_DD; break;
                default: color = 0x888888;
            }

            // 计算圆点 X 坐标
            const x = CONFIG.LAYOUT.HISTORY_DOT_START_X + roundIndex * CONFIG.LAYOUT.HISTORY_DOT_SPACING;
            const y = 0; // 与基线对齐

            // 绘制圆点
            const dot = new PIXI.Graphics();
            dot.beginFill(color);
            dot.drawCircle(x, y, CONFIG.SIZES.HISTORY_DOT_RADIUS);
            dot.endFill();
            dot.interactive = true;
            dot.cursor = 'pointer';

            // 存储自定义属性以便事件处理
            dot.__roundIndex = roundIndex;
            dot.__data = data;

            // 点击事件
            dot.on('pointerdown', () => {
                if (this.onRoundClick) {
                    this.onRoundClick(roundIndex);
                }
            });

            this.dotsContainer.addChild(dot);

            // 存储记录
            this.rounds.push({ roundIndex, resultType, data, dot });
        }

        /**
         * 高亮指定轮次的圆点
         * @param {number} roundIndex - 轮次索引
         */
        highlightRound(roundIndex) {
            this.currentRoundIndex = roundIndex;
            this.highlight.clear();

            if (roundIndex < 0 || roundIndex >= this.rounds.length) return;

            const dot = this.rounds[roundIndex].dot;
            const x = dot.x;
            const y = dot.y;
            const r = CONFIG.SIZES.HISTORY_DOT_RADIUS + 4;

            // 绘制一个金色高亮圆环
            this.highlight.lineStyle(2, CONFIG.COLORS.HIGHLIGHT, 1);
            this.highlight.drawCircle(x, y, r);
        }

        /**
         * 重置整个历史条（清空所有圆点和高亮）
         */
        reset() {
            this.dotsContainer.removeChildren();
            this.highlight.clear();
            this.rounds = [];
            this.currentRoundIndex = -1;
        }

        /** 将历史条添加到指定父容器 */
        addTo(parent) {
            parent.addChild(this.container);
        }
    }

    // 暴露全局
    window.HistoryBar = HistoryBar;
})();