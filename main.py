import json
import os
from environments.prisoner_dilemma.engine import PrisonerDilemmaEnv
from core.agent import MBTIAgent
from core.runner import run_experiment
from memory.memory import init_memory

# 初始化记忆模块
init_memory()

# API Key
API_KEY = os.environ.get("DEEPSEEK_API_KEY")


def run_prisoner_dilemma(mbti_a, mbti_b, total_rounds=50, use_rag=True):
    """运行一组囚徒困境对战"""
    with open('config/mbti_profiles.json', 'r', encoding='utf-8') as f:
        profiles = json.load(f)

    env = PrisonerDilemmaEnv(config={"total_rounds": total_rounds})
    agent_a = MBTIAgent(mbti_a, profiles[mbti_a], API_KEY)
    agent_b = MBTIAgent(mbti_b, profiles[mbti_b], API_KEY)

    run_experiment(
        env=env,
        agent_a=agent_a,
        agent_b=agent_b,
        total_rounds=total_rounds,
        use_rag=use_rag,
        environment_name="prisoner_dilemma"
    )


if __name__ == "__main__":
    # 单组测试
    run_prisoner_dilemma("INTJ", "ENTJ", total_rounds=10, use_rag=True)

    # 批量 240 组（需要时取消注释）
    # with open('config/mbti_profiles.json', 'r', encoding='utf-8') as f:
    #     profiles = json.load(f)
    # all_types = list(profiles.keys())
    # for fixed_type in all_types:
    #     for opp_type in [t for t in all_types if t != fixed_type]:
    #         run_prisoner_dilemma(fixed_type, opp_type, total_rounds=50, use_rag=True)