# main.py
from core.agent import MBTIAgent
from core.runner import ExperimentRunner
from environments.desert.env import MultiAgentDesertCrossingEnv

# 1. 创建环境，可指定智能体数量、MBTI 等
env = MultiAgentDesertCrossingEnv(
    n_agents=2,
    agent_mbtis=['INTJ', 'ENTP'],  # 按你的需求配置
    max_steps=30,
    weather_random_seed=42
)

# 2. 创建对应数量的 Agent
agents = [MBTIAgent(mbti) for mbti in env.agent_mbtis]

# 3. 创建运行器（是否启用记忆模块）
runner = ExperimentRunner(
    env=env,
    agents=agents,
    environment_name="desert",
    use_rag=True   # 设为 False 可关闭记忆
)

# 4. 开始实验
runner.run(max_steps=30)
