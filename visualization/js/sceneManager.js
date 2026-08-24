/**
 * sceneManager.js - 场景状态机（动画导演）
 * 
 * 职责：
 * 1. 读取全局博弈数据，按轮次驱动动画阶段。
 * 2. 在 THINKING / REVEAL / SETTLE 阶段调用各模块接口。
 * 3. 提供播放、暂停、跳转等控制方法。
 */

(function() {
    class SceneManager {
        /**
         * @param {Object} modules - 需要调用的各模块实例
         * @param {AgentPanel} modules.leftPanel
         * @param {AgentPanel} modules.rightPanel
         * @param {CenterStage} modules.centerStage
         * @param {HistoryBar} modules.historyBar
         * @param {number} totalRounds - 总论次数（从数据加载器中获取）
         */
        constructor(modules, totalRounds) {
            this.leftPanel = modules.leftPanel;
            this.rightPanel = modules.rightPanel;
            this.centerStage = modules.centerStage;
            this.historyBar = modules.historyBar;

            //[MODIFIED] 不在依赖外部静态数据，自己维护 rounds 数据
            this.totalRounds = totalRounds;
            this. rounds = new Array(totalRounds).fill(null).map(() => ({
                intj: { decision: null, raeson: null },
                entj: { decision: null, raeson: null },
                payoff: { intj: null, entj: null }
            }));

            // 当前轮索引（0-based）
            this.currentRoundIndex = -1;
            // 当前阶段状态
            this.state = 'IDLE';  // IDLE | THINKING | REVEAL | SETTLE | FINISHED

            // 阶段内计时
            this.stageTimer = 0;
            // 是否自动播放
            this.autoPlay = false;
            // 是否暂停
            this.paused = false;
            // 防止并发请求
            this._isFetching = false;

            // 绑定 ticker 更新函数
            this.tickerUpdate = this._update.bind(this);
            this._addedToTicker = false;
        }

        /** 启动播放（从当前轮或第一轮开始） */
        play() {
            if (this.state === 'FINISHED') {
                this.reset();
            }
            if (this.state === 'IDLE') {
                this._nextRound(); // 进入第一轮
            }
            this.autoPlay = true;
            this.paused = false;
            // 注册到主 ticker（后续在 app.js 中调用 app.ticker.add(this._tickerUpdate)）
            if (!this._addedToTicker) {
                window.__PIXI_APP__.ticker.add(this._tickerUpdate);
                this._addedToTicker = true;
            }
        }

        /** 暂停播放 */
        pause() {
            this.paused = true;
        }

        /** 恢复播放 */
        resume() {
            if (this.paused) {
                this.paused = false;
                // 如果当前阶段处于等待时间结束，无需特殊处理，ticker会继续
            }
        }

        /** 跳转到指定轮并显示 */
        gotoRound(index) {
            // 边界检查
            if (index < 0 || index >= this.totalRounds) return;
            //[MODIFIED] 只有决策已存在时才允许跳转
            if(!this.rounds[index].intj.decision){
                console.warn(`第${index+1}轮数据未获取，无法跳转`);
                return;
            }
            // 重置状态
            this._resetRound();
            // 手动设置当前轮
            this.currentRoundIndex = index;
            // 显示该轮静止状态：直接展示决策和收益，不播放动画（或快速设置）
            const round = this.rounds[index];
            this.leftPanel.revealDecision(round.intj.decision, round.intj.reason);
            this.rightPanel.revealDecision(round.entj.decision, round.entj.reason);
            this.leftPanel.updateScore(this._getCumulativeScore(0, index)); // 需要累计得分计算
            this.rightPanel.updateScore(this._getCumulativeScore(1, index));
            this.historyBar.highlightRound(index);
            // 处于暂停状态
            this.autoPlay = false;
            this.state = 'IDLE';
        }

        /** 重置到初始状态 */
        reset() {
            this._resetRound();
            this.currentRoundIndex = -1;
            this.state = 'IDLE';
            this.autoPlay = false;
            this.paused = false;
            this.leftPanel.reset();
            this.rightPanel.reset();
            this.historyBar.reset();
            //[MODIFIED] 重置rounds数组
            this.rounds = new Array(this.totalRounds).fill(null).map(() => ({
                intj: { decision: null, reason: null },
                entj: { decision: null, raeson: null },
                payoff: { intj: null, entj: null }
            }));
            this._isFetching = false;
        }

        // ---------- 内部方法 ----------

        /** 进入下一轮（内部,异步获取真实决策） */
        _nextRound() {
            console.log("_nextRound 调用, currentRoundIndex:", this.currentRoundIndex+1, "state:", this.state);
            this.currentRoundIndex++;
            if (this.currentRoundIndex >= this.totalRounds) {
                this.state = 'FINISHED';
                this.autoPlay = false;
                console.log('所有轮次播放完毕');
                return;
            }
            // 开始思考阶段
            // [MODIFIED]进入获取数据状态
            this.state = 'FETCHING';
            this.stageTimer = 0;

            // 只调用一次 _fetchAndOverrideRoundData，并用.then/ .catch处理返回的 Promise
            this._fetchAndOverrideRoundData(this.currentRoundIndex)
                .then(() => {
                    if (this.state === 'FETCHING') {
                        this.state = 'THINKING';
                        this.stageTimer = 0;
                        this.leftPanel.showThinking();
                        this.rightPanel.showThinking();
                    }
                })
                .catch(err => {
                    console.error('获取决策失败', err);
                    if (this.state === 'FETCHING') {
                        this.state = 'THINKING';
                        this.leftPanel.showThinking();
                        this.rightPanel.showThinking();
                    }
                });
        }

        /** 揭示决策并触发中心动画 */
        async _revealAndAnimate() {
            console.log("_revealAndAnimate 被调用, 当前轮:", this.currentRoundIndex+1);
            const round = this.rounds[this.currentRoundIndex];
            // 面板揭示
            this.leftPanel.revealDecision(round.intj.decision, round.intj.reason);
            this.rightPanel.revealDecision(round.entj.decision, round.entj.reason);

            // 播放中心动画（返回Promise）
            await this.centerStage.playRound(
                round.intj.decision,
                round.entj.decision,
                round.payoff.intj,
                round.payoff.entj
            );

            // 动画完成，进入结算阶段
            this.state = 'SETTLE';
            this.stageTimer = 0;

            // 更新得分（基于累计得分）
            const cumulativeIntj = this._getCumulativeScore(0, this.currentRoundIndex);
            const cumulativeEntj = this._getCumulativeScore(1, this.currentRoundIndex);
            this.leftPanel.updateScore(cumulativeIntj);
            this.rightPanel.updateScore(cumulativeEntj);

            // 添加历史标记
            const decA = round.intj.decision;
            const decB = round.entj.decision;
            let resultType;
            if (decA === 'C' && decB === 'C') resultType = 'CC';
            else if (decA === 'C' && decB === 'D') resultType = 'CD';
            else if (decA === 'D' && decB === 'C') resultType = 'DC';
            else resultType = 'DD';
            this.historyBar.addRoundMarker(this.currentRoundIndex, resultType, round);
            this.historyBar.highlightRound(this.currentRoundIndex);
        }

        /** 计算某一方到指定轮（包含）的累计得分 */
        _getCumulativeScore(agentIdx, upToRound) {
            let sum = 0;
            for (let i = 0; i <= upToRound; i++) {
                const r = this.rounds[i];
                sum += (agentIdx === 0) ? r.payoff.intj : r.payoff.entj;
            }
            return sum;
        }

        /** 重置当前轮次内部状态（暂停/计时器） */
        _resetRound() {
            // 不做具体轮次重置，主要是为了gotoRound时清理标志
        }

        /** 每帧更新，由 pixi ticker 调用 */
        _update(delta) {
            if (this.paused || this.state === 'IDLE' || this.state === 'FINISHED') return;

            const dt = delta / PIXI.Ticker.shared.FPS; // 转换为秒
            this.stageTimer += dt;
            console.log("更新中 state:", this.state, "timer:", this.stageTimer);

            switch (this.state) {
                case 'FETCHING': // [MODIFIED]等待后端返回，不做动画
                    // 不做任何计时动作，等待异步回调
                    break;
                case 'THINKING':
                    if (this.stageTimer >= CONFIG.ANIM_SPEED.THINKING) {
                        // 思考结束，进入揭示阶段（代码由异步方法处理，这里切换状态防止重复触发）
                        this.state = 'REVEAL';
                        this.stageTimer = 0;
                        // 调用揭示（注意：此函数为async，但ticker中我们不await，而是通过状态阻止再次进入）
                        this._revealAndAnimate();
                    }
                    break;
                case 'REVEAL':
                    // 此阶段由 _revealAndAnimate 内的中心动画控制，动画通过 Promise 结束后才切换到 SETTLE
                    // 这里不做时间判断，避免冲突
                    break;
                case 'SETTLE':
                    if (this.stageTimer >= CONFIG.ANIM_SPEED.SETTLE) {
                        // 结算完成，如果自动播放则进入下一轮
                        if (this.autoPlay) {
                            this._nextRound();
                        } else {
                            this.state = 'IDLE'; // 等待手动操作
                        }
                    }
                    break;
            }
        }


        // [MODIFIED]新增API交互函数
        // 构建传递给后端的历史记录（格式兼容engine.history）
        _buildHistoryForAPI(upToRound){
            const history = [];
            for (let i = 0; i < upToRound; i++ ){
                const r = this.rounds[i];
                if (r.intj.decision && r.entj.decision){
                    history.push({
                        move_a: r.intj.decision,
                        move_b: r.entj.decision,
                        score_a: r.payoff.intj,
                        score_b: r.payoff.entj
                    });
                }
            }
            return history;
        }
        
        // 收益矩阵（与后端engine.py一致）
        _computePayoff(moveA, moveB){
            const matrix = {
                'CC': [2, 2],
                'CD': [-1, 3],
                'DC': [3, -1],
                'DD': [0, 0],
            };
            const key = moveA + moveB;
            return matrix[key] || [0, 0];
        }

        /** 请求后端获取单个 Agent 的决策 */
        async _fetchAgentDecision(agentType, opponentType, history) {
            const url = 'http://localhost:5000/decide';
            const payload = {
                agent_type: agentType,
                opponent_mbti: opponentType,
                history: history
            };
            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                const data = await response.json();
                return { action: data.action, thought: data.thought };
            } catch (err) {
                console.error(`请求 ${agentType} 决策失败:`, err);
                return { action: 'C', thought: '[Fallback] 请求失败，默认合作' };
            }
        }

        /** 获取当前轮的双方决策，并更新 this.rounds[currentRoundIndex] */
        async _fetchAndOverrideRoundData(roundIndex) {
            console.log("_fetchAndOverrideRoundData 被调用, roundIndex:", roundIndex, "_isFetching =", this._isFetching);
                    
            // 如果正在请求，返回一个 rejected Promise，而不是 false
            if (this._isFetching) {
                console.warn(`第 ${roundIndex+1} 轮请求已在途中，拒绝重复请求`);
                return Promise.reject(new Error("Already fetching"));
            }

            this._isFetching = true;
            console.log("开始请求第", roundIndex+1, "轮数据, 历史长度:", this._buildHistoryForAPI(roundIndex).length);
                    
            try {
                const history = this._buildHistoryForAPI(roundIndex);
                const [intjResult, entjResult] = await Promise.all([
                    this._fetchAgentDecision('INTJ', 'ENTJ', history),
                    this._fetchAgentDecision('ENTJ', 'INTJ', history)
                ]);

                const moveA = intjResult.action;
                const moveB = entjResult.action;

                // const [scoreA, scoreB] = this._computePayoff(moveA, moveB);
                // 报错修改
                // 内联收益矩阵
                const matrix = {
                    'CC': [2, 2],
                    'CD': [-1, 3],
                    'DC': [3, -1],
                    'DD': [0, 0],
                };
                const key = moveA + moveB;
                const [scoreA, scoreB] = matrix[key] || [0, 0];

                this.rounds[roundIndex] = {
                    intj: { decision: moveA, reason: intjResult.thought },
                    entj: { decision: moveB, reason: entjResult.thought },
                    payoff: { intj: scoreA, entj: scoreB }
                };

                console.log("第", roundIndex+1, "轮数据获取完成, 动作:", moveA, moveB);
                return true;
            } catch (err) {
                console.error("获取决策数据时出错:", err);
                // 设置 fallback 数据，避免完全卡死
                this.rounds[roundIndex] = {
                    intj: { decision: 'C', reason: '[Error] 使用默认合作' },
                    entj: { decision: 'C', reason: '[Error] 使用默认合作' },
                    payoff: { intj: 2, entj: 2 }
                };
                throw err;  // 继续向上抛出错误
            } finally {
                this._isFetching = false;
            }
        }
    }
})

// 修改至 line 308
