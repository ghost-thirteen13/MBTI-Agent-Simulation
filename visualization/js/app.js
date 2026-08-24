/**
 * app.js - PixiJS 应用主入口
 * 
 * 职责：
 * 1. 使用 CONFIG 常量创建 PIXI.Application 实例。
 * 2. 建立画布元素层级（背景层、博弈层、UI 层）。
 * 3. 启动动画循环 (ticker)，为后续模块提供帧更新基础。
 */

// 立即执行函数，避免污染全局作用域（但会挂载 app 实例到 window，方便调试）
(function() {
    // ---------- 创建 PixiJS 应用 ----------
    const app = new PIXI.Application({
        width: CONFIG.WIDTH,                       // 画布宽度
        height: CONFIG.HEIGHT,                     // 画布高度
        backgroundColor: CONFIG.BACKGROUND_COLOR,  // 深色背景
        antialias: true,                           // 开启抗锯齿
        resolution: window.devicePixelRatio || 1,  // 适配高清屏
        autoDensity: true                          // 自动调整 CSS 尺寸
    });

    // 将 PixiJS 的 Canvas 添加到页面
    document.body.appendChild(app.view);
    // 方便在浏览器控制台中直接访问应用实例（调试用）
    window.__PIXI_APP__ = app;
    window.app = app;   // 方便调试时直接使用

    // ---------- 构建场景层级 ----------
    // 创建三个容器，按从下到上的顺序添加，确保正确的覆盖关系
    const layers = {
        background: new PIXI.Container(),  // 最底层：背景装饰（静态）
        game: new PIXI.Container(),        // 中间层：Agent 面板、中央动画、历史条
        ui: new PIXI.Container()           // 最上层：控制按钮、轮次信息覆盖
    };
    // 将容器依次添加到舞台
    app.stage.addChild(layers.background);
    app.stage.addChild(layers.game);
    app.stage.addChild(layers.ui);
    // 把层级对象也挂到 app 上，方便后续模块引用
    app.layers = layers;

    // 打印成功信息到控制台
    console.log('✅ PixiJS 应用初始化完成');
    console.log('画布尺寸:', CONFIG.WIDTH + 'x' + CONFIG.HEIGHT);
    
    // ---------- 加载博弈数据 ----------
    DataLoader.load()
        .then((gameData) => {   
            console.log('✅ 博弈数据已就绪，游戏数据对象:', gameData);
            
            // 1 创建两个Agent面板
            const leftPanel = new AgentPanel('left', 'INTJ');
            const rightPanel = new AgentPanel('right', 'ENTJ');
            // 将面板添加到游戏层
            leftPanel.addTo(app.layers.game);
            rightPanel.addTo(app.layers.game);
            // 保存引用到app上，方便后续状态机或其它模块调用
            app.leftPanel = leftPanel;
            app.rightPanel = rightPanel;

            // 2 创建历史轨迹条，挂载到游戏层，点击圆点暂时仅打印轮次
            const historyBar = new HistoryBar((roundIndex) => {
                console.log('点击了第', roundIndex + 1, '轮');
                // 点击历史圆点时跳转
                if (app.sceneManager) {
                    app.sceneManager.gotoRound(roundIndex);
                }
            });
            historyBar.addTo(layers.game);
            app.historyBar = historyBar;

            // 3 创建中央舞台
            const centerStage = new CenterStage();
            centerStage.addTo(layers.game);
            app.centerStage = centerStage;

            //  4 创建场景管理器（导演） - [MODIFIED] 传入总轮数，不再依赖静态决策数据
            const totalRounds = gameData.rounds.length
            const sceneManager = new SceneManager({
                leftPanel,
                rightPanel,
                centerStage,
                historyBar
            }, totalRounds);
            app.sceneManager = sceneManager;

            // 5. UI 控制栏（添加到 UI 层）
            const controlBar = new ControlBar(sceneManager);
            controlBar.addTo(layers.ui);
            app.controlBar = controlBar;
            
            // 默认不自动播放，等待用户点击 ▶
            // 但我们仍然启动 ticker（SceneManager.play() 会注册 ticker，不调用则 ticker 为空）
            // 添加一个简单的 ticker 更新：刷新控制栏状态
            app.ticker.add(() => {
                controlBar.refresh();
            });

            // 自动开始播放（可以取消注释这行，自动播放）
            // sceneManager.play();
            // 后续在此初始化其他模块
        })
        .catch((err) => {
            console.error('❌ 数据加载失败:', err);
        });
})();