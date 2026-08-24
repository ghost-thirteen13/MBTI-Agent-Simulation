/**
 * agentPanel.js - 单个 Agent 面板绘制与状态更新
 * 
 * 职责：
 * - 根据左右方位，在指定坐标绘制头像、MBTI 标签、决策图标、理由气泡、累计得分。
 * - 提供 showThinking、revealDecision、updateScore、reset 等控制接口。
 * - 所有图形使用 PIXI.Graphics / Text，零外部图片依赖。
 * - 每个面板为一个独立的 PIXI.Container，方便添加到场景中。
 */

(function() {
    class AgentPanel {
        /**
         * @param {string} side - 'left' 或 'right'，决定面板位置和 MBTI 类型
         * @param {string} mbti  - MBTI 类型字符串（如 'INTJ'）
         */
        constructor(side, mbti) {
            this.side = side;
            this.mbti = mbti;

            // 从 CONFIG 获取该侧的布局坐标
            const isLeft = (side === 'left');
            this.centerX = isLeft ? CONFIG.LAYOUT.LEFT_PANEL_X : CONFIG.LAYOUT.RIGHT_PANEL_X;
            this.centerY = CONFIG.LAYOUT.LEFT_PANEL_Y;  // 左右 Y 坐标相同，但未来可独立调整

            // 创建主容器，所有子元素都添加到这里
            this.container = new PIXI.Container();
            this.container.x = this.centerX;
            this.container.y = this.centerY;

            // ---- 子元素 ----
            this._drawAvatar();        // 头像及背景
            this._drawLabel();         // MBTI 标签
            this._drawDecisionIcon();  // 决策图标（初始隐藏）
            this._drawBubble();        // 理由气泡（初始隐藏）
            this._drawScore();         // 累计得分

            // 初始状态
            this.reset();
        }

        // ---------- 绘制方法 (内部) ----------

        /** 绘制头像：一个圆形 + 内部简写字幕 */
        _drawAvatar() {
            this.avatar = new PIXI.Graphics();
            // 头像圆背景
            this.avatar.beginFill(CONFIG.COLORS.PANEL_BG);
            this.avatar.drawCircle(0, 0, CONFIG.SIZES.AVATAR_RADIUS);
            this.avatar.endFill();
            // 头像边框
            this.avatar.lineStyle(2, CONFIG.COLORS.TEXT_LIGHT);
            this.avatar.drawCircle(0, 0, CONFIG.SIZES.AVATAR_RADIUS);
            this.container.addChild(this.avatar);

            // 头像内部的文字（MBTI 缩写首字母）
            this.avatarText = new PIXI.Text(this.mbti.charAt(0), {
                fontFamily: 'Arial',
                fontSize: 30,
                fontWeight: 'bold',
                fill: '#ffffff',
                align: 'center'
            });
            this.avatarText.anchor.set(0.5, 0.5);
            this.avatarText.x = 0;
            this.avatarText.y = 0;
            this.avatar.addChild(this.avatarText);
        }

        /** 绘制 MBTI 类型标签（头像下方） */
        _drawLabel() {
            this.label = new PIXI.Text(this.mbti, CONFIG.FONT_STYLE.LABEL);
            this.label.anchor.set(0.5, 0);
            this.label.x = 0;
            this.label.y = CONFIG.SIZES.AVATAR_RADIUS + 10;
            this.container.addChild(this.label);
        }

        /** 绘制决策图标区(初始隐藏)，包含图形和文字 */
        _drawDecisionIcon() {
            this.decisionContainer = new PIXI.Container();
            this.decisionContainer.visible = false; // 初始不显示
            this.container.addChild(this.decisionContainer);

            // 决策图标用 Graphics 动态绘制（占位，具体形状在 revealDecision 中重绘）
            this.decisionGraphic = new PIXI.Graphics();
            this.decisionContainer.addChild(this.decisionGraphic);

            // 决策文字说明（如 "C" / "D"）
            this.decisionText = new PIXI.Text('', {
                fontFamily: 'Arial',
                fontSize: 18,
                fontWeight: 'bold',
                fill: '#ffffff',
                align: 'center'
            });
            this.decisionText.anchor.set(0.5, 0.5);
            this.decisionText.y = -CONFIG.SIZES.AVATAR_RADIUS - 25; // 放在头像上方
            this.decisionContainer.addChild(this.decisionText);
        }

        /** 绘制理由气泡（初始隐藏） */
        _drawBubble() {
            this.bubbleContainer = new PIXI.Container();
            this.bubbleContainer.visible = false;
            this.container.addChild(this.bubbleContainer);

            // 气泡背景
            this.bubbleBg = new PIXI.Graphics();
            this.bubbleContainer.addChild(this.bubbleBg);

            // 气泡内文字
            this.bubbleText = new PIXI.Text('', CONFIG.FONT_STYLE.REASON);
            this.bubbleText.anchor.set(0, 0);
            this.bubbleText.x = -CONFIG.SIZES.BUBBLE_WIDTH / 2;
            this.bubbleText.y = -CONFIG.SIZES.BUBBLE_HEIGHT / 2;
            this.bubbleContainer.addChild(this.bubbleText);

            // 设置气泡位置（头像侧下方偏移，左右不同避免遮挡）
            const offsetX = (this.side === 'left') ? -120 : 120;
            this.bubbleContainer.x = offsetX;
            this.bubbleContainer.y = CONFIG.SIZES.AVATAR_RADIUS + 30;
        }

        /** 绘制累计得分数字（初始为0） */
        _drawScore() {
            this.scoreText = new PIXI.Text('0', CONFIG.FONT_STYLE.SCORE);
            this.scoreText.anchor.set(0.5, 0.5);
            this.scoreText.x = 0;
            this.scoreText.y = CONFIG.LAYOUT.SCORE_Y_OFFSET + CONFIG.SIZES.AVATAR_RADIUS;
            this.container.addChild(this.scoreText);

            // 分数标签
            const scoreLabel = new PIXI.Text('得分', {
                fontFamily: 'Arial',
                fontSize: 14,
                fill: '#aaaaaa',
                align: 'center'
            });
            scoreLabel.anchor.set(0.5, 0.5);
            scoreLabel.x = 0;
            scoreLabel.y = this.scoreText.y - 25;
            this.container.addChild(scoreLabel);
        }

        // ---------- 公共接口 ----------

        /** 显示思考中状态（省略号动画先简单用静态文字表示） */
        showThinking() {
            this.decisionContainer.visible = true;
            this.decisionGraphic.clear();
            // 绘制三个闪烁的小点（简化：先画三个灰色圆点）
            const dotRadius = 4;
            const spacing = 12;
            this.decisionGraphic.beginFill(CONFIG.COLORS.THINKING_BUBBLE);
            this.decisionGraphic.drawCircle(-spacing, -CONFIG.SIZES.AVATAR_RADIUS - 25, dotRadius);
            this.decisionGraphic.drawCircle(0, -CONFIG.SIZES.AVATAR_RADIUS - 25, dotRadius);
            this.decisionGraphic.drawCircle(spacing, -CONFIG.SIZES.AVATAR_RADIUS - 25, dotRadius);
            this.decisionGraphic.endFill();
            this.decisionText.text = '';
            this.bubbleContainer.visible = false;
            // 注：真正的跳动动画将在 SceneManager 驱动 ticker 时实现，这里仅做静态展示
        }

        /**
         * 揭示本轮决策
         * @param {string} decision - 'C' 或 'D'
         * @param {string} reason   - 决策理由文本
         */
        revealDecision(decision, reason) {
            this.decisionContainer.visible = true;
            this.decisionGraphic.clear();

            // 根据决策绘制不同图标
            const iconSize = CONFIG.SIZES.DECISION_ICON_SIZE / 2;
            if (decision === 'C') {
                // 合作：绿色圆形+勾
                this.decisionGraphic.beginFill(CONFIG.COLORS.COOPERATE);
                this.decisionGraphic.drawCircle(0, -CONFIG.SIZES.AVATAR_RADIUS - 25, iconSize);
                this.decisionGraphic.endFill();
                this.decisionText.text = 'C';
            } else {
                // 背叛：红色三角形+叉
                this.decisionGraphic.beginFill(CONFIG.COLORS.BETRAY);
                this.decisionGraphic.moveTo(0, -CONFIG.SIZES.AVATAR_RADIUS - 25 - iconSize);
                this.decisionGraphic.lineTo(iconSize, -CONFIG.SIZES.AVATAR_RADIUS - 25 + iconSize);
                this.decisionGraphic.lineTo(-iconSize, -CONFIG.SIZES.AVATAR_RADIUS - 25 + iconSize);
                this.decisionGraphic.closePath();
                this.decisionGraphic.endFill();
                this.decisionText.text = 'D';
            }

            // 更新理由气泡
            this.bubbleText.text = reason || '';
            // 重新绘制气泡背景以适应文本尺寸
            const textWidth = this.bubbleText.width;
            const textHeight = this.bubbleText.height;
            const padding = 10;
            this.bubbleBg.clear();
            this.bubbleBg.beginFill(0xffffff, 0.9);
            this.bubbleBg.drawRoundedRect(
                -textWidth / 2 - padding,
                -textHeight / 2 - padding,
                textWidth + padding * 2,
                textHeight + padding * 2,
                8
            );
            this.bubbleBg.endFill();
            this.bubbleContainer.visible = true;
        }

        /**
         * 更新累计得分
         * @param {number} newScore - 新的总分
         */
        updateScore(newScore) {
            // 简单的直接更新（后续可添加数字滚动动画）
            this.scoreText.text = newScore.toString();
            // 微量缩放弹跳效果可在此后续添加，现在先硬更新
        }

        /** 重置面板到初始状态（隐藏决策、气泡，分数归零） */
        reset() {
            this.decisionContainer.visible = false;
            this.bubbleContainer.visible = false;
            this.scoreText.text = '0';
            this.decisionGraphic.clear();
            this.decisionText.text = '';
            this.bubbleText.text = '';
        }

        /** 将面板容器添加到指定父容器 */
        addTo(parent) {
            parent.addChild(this.container);
        }
    }

    // 暴露给全局
    window.AgentPanel = AgentPanel;
})();