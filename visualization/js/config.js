/**
 * CONFIG - 全局配置常量
 * 
 * 集中定义所有与视觉、动画、布局相关的参数。
 * 所有其他模块都引用这里的常量，保证一致性，方便一站式调整。
 */

const CONFIG = {
    // ==================== 画布基础 ====================
    WIDTH: 960,                    // 画布宽度（px）
    HEIGHT: 640,                   // 画布高度（px）
    BACKGROUND_COLOR: 0x1a1a2e,    // 深色背景（十六进制颜色值）

    // ==================== 全局色板 ====================
    COLORS: {
        COOPERATE: 0x4caf50,       // 合作 - 绿色
        BETRAY: 0xf44336,          // 背叛 - 红色
        MUTUAL_BETRAY: 0x757575,   // 双方背叛 - 灰色
        TEXT_LIGHT: 0xffffff,      // 浅色文字
        TEXT_DARK: 0x222222,       // 深色文字
        PANEL_BG: 0x16213e,        // Agent 面板背景色
        HIGHLIGHT: 0xffc107,       // 高亮 / 当前轮次标记色
        THINKING_BUBBLE: 0xcccccc, // 思考气泡颜色
        HISTORY_CC: 0x4caf50,      // 历史标记：双方合作 (C,C)
        HISTORY_CD_DC: 0xff9800,   // 历史标记：一方背叛 (C,D) 或 (D,C)
        HISTORY_DD: 0xf44336       // 历史标记：双方背叛 (D,D)
    },

    // ==================== 动画时长（秒） ====================
    ANIM_SPEED: {
        THINKING: 1.0,             // 思考阶段持续时长
        REVEAL: 0.6,               // 揭示决策动画时长
        SETTLE: 1.2,               // 结算阶段持续时长
        SCORE_ROLL: 0.5,           // 分数数字滚动动画时长
        TRAIL_FADE: 0.3            // 飞行拖尾渐隐时长
    },

    // ==================== 布局坐标（相对于画布左上角） ====================
    LAYOUT: {
        // 左侧 Agent 面板中心点
        LEFT_PANEL_X: 160,
        LEFT_PANEL_Y: 200,
        // 右侧 Agent 面板中心点
        RIGHT_PANEL_X: 800,
        RIGHT_PANEL_Y: 200,
        // 中央碰撞点
        CENTER_X: 480,
        CENTER_Y: 300,
        // 底部历史条纵坐标（圆点中心所在水平线）
        HISTORY_BAR_Y: 560,
        // 历史条第一个圆点的起始 x，以及圆点之间的间距
        HISTORY_DOT_START_X: 60,
        HISTORY_DOT_SPACING: 40,
        // 顶部控制条的纵坐标
        CONTROL_BAR_Y: 30,
        // 累计得分相对于头像中心的垂直偏移量（正值表示向下）
        SCORE_Y_OFFSET: 80
    },

    // ==================== 文字样式 ====================
    FONT_STYLE: {
        LABEL: {
            fontFamily: 'Arial',
            fontSize: 18,
            fill: '#ffffff'
        },
        SCORE: {
            fontFamily: 'Arial',
            fontSize: 32,
            fontWeight: 'bold',
            fill: '#ffffff'
        },
        REASON: {
            fontFamily: 'Arial',
            fontSize: 14,
            fill: '#222222',
            wordWrap: true,
            wordWrapWidth: 200
        },
        ROUND_INFO: {
            fontFamily: 'Arial',
            fontSize: 24,
            fill: '#ffffff'
        }
    },

    // ==================== 图形尺寸 ====================
    SIZES: {
        AVATAR_RADIUS: 40,         // 头像圆形半径
        DECISION_ICON_SIZE: 28,    // 决策图标（合作/背叛符号）的外接正方形边长
        HISTORY_DOT_RADIUS: 10,    // 历史圆点半径
        BUBBLE_WIDTH: 180,         // 理由气泡宽度
        BUBBLE_HEIGHT: 60          // 理由气泡高度
    }
};