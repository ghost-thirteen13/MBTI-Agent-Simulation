# MBTI-Agent-Simulation · 基于大模型的多 Agent 人格博弈仿真

> 通过将 16 种 MBTI 人格注入大模型，让它们在博弈论场景中两两对战，用 **284 局真实 LLM 对局 / 13000+ 轮** 量化「人格如何影响合作与决策行为」。

## 项目要点

- **真大模型驱动**：每个 Agent 都由 DeepSeek 大模型实时推理决策（非本地算法模拟），思考过程为中文 LLM 推理，决策可完整追溯。
- **全量人格覆盖**：16 种 MBTI 两两对局全覆盖，数据全量开源（`data/rounds_detail.csv`）。
- **可复现的量化结论**：F 型（情感型）合作率 **88.6%** vs T 型（思考型）**66.9%**，差 **21.7 个百分点**；ENFP / INFJ 合作率 90%+，ESTP / ENTP 仅 35–41%。
- **RAG 记忆增强**：基于 Milvus 向量库 + 中文句向量模型，让 Agent 拥有跨轮次经验记忆，支持「有记忆 vs 无记忆」对照实验。

## 技术栈

| 层级 | 技术 |
|---|---|
| 大模型调用 | DeepSeek API（OpenAI SDK 兼容协议） |
| 记忆检索（RAG） | Milvus 向量库 + sentence-transformers（`bge-small-zh-v1.5`） |
| 博弈环境 | 囚徒困境（信任的进化）、沙漠困境（数学建模场景） |
| 前端可视化 | PixiJS 引擎（8 模块状态机动画，AI实现） |
| 后端接口 | Flask（`api_server.py`） |
| 数据 | 284 局全量对战日志（CSV） |

## 博弈场景

1. **囚徒困境 / 信任的进化**：两 Agent 每轮在「合作 C / 背叛 D」间抉择，研究人格对信任、报复与长期合作的影响。
2. **沙漠困境**：网格地图上的生存博弈，Agent 需在移动 / 挖矿 / 购买补给间做资源权衡决策，考察理性规划能力。

## 核心实验结论

在囚徒困境（信任的进化）场景下，对 16 种 MBTI 两两组合各跑 50 轮：

| 维度 | 结果 |
|---|---|
| F 型（情感型）合作率 | **88.6%** |
| T 型（思考型）合作率 | **66.9%** |
| 合作率最高 | ENFP / INFJ（90%+） |
| 合作率最低 | ESTP / ENTP（35–41%） |

> 情感型人格更倾向于建立与维持合作，思考型人格更理性但更警惕背叛——这与「信任的进化」理论中「合作需要情感与信任支撑」的预期一致。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
cp .env.example .env   # 然后编辑 .env，填入 DEEPSEEK_API_KEY
```

代码统一通过 `os.environ.get("DEEPSEEK_API_KEY")` 读取，**不再硬编码任何 key**。

### 3. 启动 Milvus（记忆检索需要）

```bash
docker compose up -d          # 启动 etcd + minio + milvus standalone
python init_milvus.py         # 初始化 game_memory 集合
```

> 句向量模型 `bge-small-zh-v1.5` 会从本地缓存加载（强制离线模式），首次运行前请确保已下载。

### 4. 运行实验

```bash
python main.py          # 囚徒困境：单组对战（INTJ vs ENTJ）
python main1.py         # 囚徒困境：16 种 MBTI 两两全量对战
python main_desert.py   # 沙漠困境：网格生存博弈
```

## 📁 目录结构

```
├── core/                    # 核心逻辑
│   ├── agent.py             # MBTIAgent：大模型 Agent（调 LLM API 决策）
│   ├── runner.py            # ExperimentRunner：实验主循环
│   └── memory.py            # 轻量内存记忆（按 Agent 隔离）
├── memory/                  # RAG 记忆（Milvus + 句向量）
├── environments/            # 博弈环境
│   ├── prisoner_dilemma/    # 囚徒困境
│   └── desert/              # 沙漠困境
├── config/                  # MBTI 人格配置（16 种人格 system prompt）
├── data/                    # 实验数据（rounds_detail.csv / summary.csv）
├── visualization/           # PixiJS 前端可视化（8 模块）
├── main.py / main1.py       # 囚徒困境入口（单组 / 批量）
├── main_desert.py           # 沙漠困境入口
├── api_server.py            # Flask 后端接口
└── init_milvus.py           # Milvus 集合初始化
```

## 🖥️ 前端可视化（PixiJS）

网页端用 PixiJS 引擎实现博弈过程的图形化回放，按职责拆为 8 个模块，由状态机（`sceneManager`）驱动：

`agentPanel`（Agent 面板）→ `app`（主入口）→ `centerStage`（对峙动画）→ `config`（全局常量）→ `controlBar`（控制栏）→ `dataLoader`（数据加载）→ `historyBar`（历史轨迹）→ `sceneManager`（状态机导演）

联动流程：`config` 提供常量 → `dataLoader` 加载数据 → `app` 创建图层 → `sceneManager` 按轮次调度 → `controlBar` 响应用户操作 → 画布呈现完整博弈动画。
