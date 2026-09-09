# main1.py
# 囚徒困境：16 种 MBTI 两两全量对战入口（有序对，共 16×15=240 组）
# 用法：
#   py -3.11 main1.py          # 有 RAG
#   py -3.11 main1.py --no-rag # 无 RAG
import os
import sys
import json

from dotenv import load_dotenv

load_dotenv()

from core.agent import MBTIAgent
from main import run_experiment, _load_profiles

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_completed_pairs() -> set:
    """从 logs/ 下已生成的 JSON 日志中提取已完成的 (mbti_a, mbti_b) 有序对。"""
    completed = set()
    logs_dir = os.path.join(BASE_DIR, "logs")
    if not os.path.exists(logs_dir):
        return completed
    for fname in os.listdir(logs_dir):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(logs_dir, fname), "r", encoding="utf-8") as f:
                data = json.load(f)
            s = data.get("summary", {})
            if s.get("mbti_a") and s.get("mbti_b"):
                completed.add((s["mbti_a"], s["mbti_b"]))
        except Exception:
            continue
    return completed


if __name__ == "__main__":
    use_rag = "--no-rag" not in sys.argv[1:]
    profiles = _load_profiles()
    all_types = list(profiles.keys())
    total_pairs = len(all_types) * (len(all_types) - 1)  # 16 × 15 = 240

    completed_pairs = _load_completed_pairs()
    print(f"已完成的组合数: {len(completed_pairs)} / {total_pairs}")

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    for fixed_type in all_types:
        for opp_type in [t for t in all_types if t != fixed_type]:
            pair = (fixed_type, opp_type)
            if pair in completed_pairs:
                print(f"[跳过] 已完成: {pair[0]} vs {pair[1]}")
                continue
            print(f"\n===== {pair[0]} vs {pair[1]} =====")
            agent_a = MBTIAgent(pair[0], profiles.get(pair[0]), api_key)
            agent_b = MBTIAgent(pair[1], profiles.get(pair[1]), api_key)
            run_experiment(agent_a, agent_b, total_rounds=50, use_rag=use_rag)

    print("\n[完成] 全量对战已跑完！")
