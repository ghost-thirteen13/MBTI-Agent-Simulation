/**
 * dataLoader.js - 数据加载与解析
 * 
 * 职责：
 * 1. 加载博弈数据（优先内嵌 JSON 变量，备选 fetch 外部文件）。
 * 2. 校验数据字段完整性。
 * 3. 将标准化数据存入全局 __GAME_DATA__，返回 Promise，便于后续模块调用。
 */

const DataLoader = (function() {
    /**
     * 内部校验函数：检查单轮数据是否包含必要字段
     * @param {Object} round - 单轮数据
     * @param {number} index - 轮次索引（从1开始）
     * @returns {boolean} 校验通过返回 true
     */
    function _validateRound(round, index) {
        const requiredFields = [
            'round', 
            'decision_intj', 
            'decision_entj', 
            'payoff_intj', 
            'payoff_entj'
        ];
        for (let field of requiredFields) {
            if (round[field] === undefined) {
                console.warn(`⚠️ 第 ${index} 轮数据缺少字段: ${field}`);
                return false;
            }
        }
        // 决策字段必须是 'C' 或 'D'
        if (!['C', 'D'].includes(round.decision_intj) || !['C', 'D'].includes(round.decision_entj)) {
            console.warn(`⚠️ 第 ${index} 轮决策字段必须为 'C' 或 'D'`);
            return false;
        }
        return true;
    }

    /**
     * 对原始数据做标准化处理，补充可选字段默认值，并过滤无效轮次
     * @param {Object} rawData - 原始 JSON 数据
     * @returns {Object} 标准化后的数据
     */
    function _normalizeData(rawData) {
        // 确保 rounds 是数组
        const rounds = Array.isArray(rawData.rounds) ? rawData.rounds : [];
        
        const validRounds = [];
        for (let i = 0; i < rounds.length; i++) {
            const round = rounds[i];
            // 校验通过则保留，并补充可选字段默认值
            if (_validateRound(round, i + 1)) {
                validRounds.push({
                    round: round.round,
                    intj: {
                        decision: round.decision_intj,
                        reason: round.reason_intj || '(无记录)'
                    },
                    entj: {
                        decision: round.decision_entj,
                        reason: round.reason_entj || '(无记录)'
                    },
                    payoff: {
                        intj: round.payoff_intj,
                        entj: round.payoff_entj
                    }
                });
            }
        }

        return {
            agents: rawData.agents || ['INTJ', 'ENTJ'],
            rounds: validRounds
        };
    }

    /**
     * 主加载函数：尝试从内嵌变量或外部 JSON 获取数据
     * @returns {Promise<Object>} 返回标准化后的游戏数据
     */
    async function loadData() {
        let rawData = null;

        // 优先使用内嵌数据（在 HTML 的 <script> 中预先定义）
        if (typeof __EMBEDDED_ROUNDS_DATA__ !== 'undefined') {
            console.log('📦 使用内嵌博弈数据');
            rawData = __EMBEDDED_ROUNDS_DATA__;
        } else {
            // 备选：从外部文件加载
            console.log('📂 尝试加载外部数据文件 data/sample_rounds.json');
            try {
                const response = await fetch('data/sample_rounds.json');
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                rawData = await response.json();
            } catch (err) {
                console.error('❌ 数据加载失败:', err.message);
                throw new Error('无法获取博弈数据，请检查内嵌变量或数据文件路径');
            }
        }

        // 标准化并校验
        const gameData = _normalizeData(rawData);
        if (gameData.rounds.length === 0) {
            throw new Error('没有有效的博弈轮次数据');
        }

        // 暴露到全局，供其他模块直接引用
        window.__GAME_DATA__ = gameData;
        console.log(`✅ 数据加载完成，共 ${gameData.rounds.length} 轮，Agent: ${gameData.agents.join(' vs ')}`);
        return gameData;
    }

    // 对外暴露公共方法
    return {
        load: loadData
    };
})();