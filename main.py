# main.py
# 囚徒困境：单组对战入口（默认 INTJ vs ENTJ）
# 用法：
#   py -3.11 main.py               # 有 RAG（需先启动 Milvus 并装 pymilvus）
#   py -3.11 main.py --no-rag      # 无 RAG（纯 LLM 人格决策，无需 Milvus）
#   py -3.11 main.py --rounds 20   # 指定轮数
import os
import sys
import json
import uuid
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()  # 加载 .env 中的 DEEPSEEK_API_KEY

from environments.prisoner_dilemma.engine import PrisonerDilemmaEnv
from core.agent import MBTIAgent

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_profiles() -> dict:
    with open(os.path.join(BASE_DIR, "config", "mbti_profiles.json"),
              "r", encoding="utf-8") as f:
        return json.load(f)


def format_memories(memories: list) -> str:
    """把检索到的记忆列表转成自然语言文本，注入 prompt。"""
    if not memories:
        return "无相关记忆。"
    lines = []
    for i, mem in enumerate(memories, 1):
        lines.append(
            f"{i}. 第{mem['round']}轮：我{mem['my_action']}，对方{mem['opponent_action']}，"
            f"收益{mem['my_payoff']}。"
        )
    return "\n".join(lines)


def _history_summary(engine) -> str:
    """把最近 3 轮历史转成一句话摘要，用作记忆检索的 query。"""
    if not engine.history:
        return ""
    recent = engine.history[-3:]
    start_round = len(engine.history) - len(recent) + 1
    entries = []
    for i, h in enumerate(recent, start=start_round):
        entries.append(
            f"轮{i}: A选{h['move_a']} B选{h['move_b']} 得分{h['score_a']}:{h['score_b']}"
        )
    return "；".join(entries)


def run_experiment(agent_a, agent_b, total_rounds=50, use_rag=True):
    """
    运行一场囚徒困境博弈。
    参数：
        agent_a/agent_b: 两个 MBTIAgent 实例
        total_rounds:    博弈轮数
        use_rag:         是否启用 RAG 记忆（True 需先启动 Milvus 并 init_memory）
    返回：完整实验数据 dict（summary + rounds）
    """
    # 可选：use_rag 时初始化记忆模块（延迟导入，无 RAG 时不强依赖 pymilvus）
    if use_rag:
        from memory.memory import init_memory, retrieve_similar, store_experience
        init_memory()

    mbti_a = agent_a.mbti_type
    mbti_b = agent_b.mbti_type
    experiment_id = str(uuid.uuid4())

    engine = PrisonerDilemmaEnv(config={"total_rounds": total_rounds})

    mode = "有 RAG" if use_rag else "无 RAG"
    print(f"--- 开始博弈: {mbti_a} vs {mbti_b} ({mode}, 共 {total_rounds} 轮) ---")

    experiment_logs = []

    for r in range(total_rounds):
        # 1) 检索记忆
        mem_text_a = ""
        mem_text_b = ""
        if use_rag:
            history_summary = _history_summary(engine)
            query_a = (f"第{r+1}轮，我是{mbti_a}，对手未知。最近局势：{history_summary}"
                       if history_summary else f"第{r+1}轮开始。")
            query_b = (f"第{r+1}轮，我是{mbti_b}，对手未知。最近局势：{history_summary}"
                       if history_summary else f"第{r+1}轮开始。")
            mem_a = retrieve_similar(agent_mbti=mbti_a, experiment_id=experiment_id,
                                     query_text=query_a, top_k=3)
            mem_b = retrieve_similar(agent_mbti=mbti_b, experiment_id=experiment_id,
                                     query_text=query_b, top_k=3)
            mem_text_a = format_memories(mem_a)
            mem_text_b = format_memories(mem_b)

        # 2) 双方决策
        state_desc_a = engine.render(self_role='A')
        state_desc_b = engine.render(self_role='B')
        move_a, thought_a = agent_a.decide(state_desc_a, memory_context=mem_text_a)
        move_b, thought_b = agent_b.decide(state_desc_b, memory_context=mem_text_b)

        # 3) 环境结算（record_round 返回 (state, reward, done, info)）
        state, reward, done, info = engine.record_round(move_a, move_b)
        score_a, score_b = reward
        agent_a.total_score += score_a
        agent_b.total_score += score_b

        # 4) 记录本轮
        log_entry = {
            "round": r + 1,
            f"{mbti_a}_decision": move_a,
            f"{mbti_b}_decision": move_b,
            f"{mbti_a}_thought": thought_a,
            f"{mbti_b}_thought": thought_b,
            "scores": (score_a, score_b)
        }
        experiment_logs.append(log_entry)
        print(f"第 {r+1:>2} 轮: {mbti_a}({move_a}) | {mbti_b}({move_b}) -> 得分 {score_a}:{score_b}")

        # 5) 存储本轮经验
        if use_rag:
            context_a = (f"第{r+1}轮，我是{mbti_a}，对手未知，我选择{move_a}，"
                         f"对方选择{move_b}，收益{score_a}。")
            store_experience(experiment_id=experiment_id, agent_mbti=mbti_a,
                             opponent_mbti=mbti_b, round_num=r + 1,
                             my_action=move_a, opponent_action=move_b,
                             my_payoff=float(score_a), opponent_payoff=float(score_b),
                             context_text=context_a)
            context_b = (f"第{r+1}轮，我是{mbti_b}，对手未知，我选择{move_b}，"
                         f"对方选择{move_a}，收益{score_b}。")
            store_experience(experiment_id=experiment_id, agent_mbti=mbti_b,
                             opponent_mbti=mbti_a, round_num=r + 1,
                             my_action=move_b, opponent_action=move_a,
                             my_payoff=float(score_b), opponent_payoff=float(score_a),
                             context_text=context_b)

    # 保存 JSON 日志
    os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tag = "rag" if use_rag else "norag"
    filename = os.path.join(
        BASE_DIR, "logs",
        f"experiment_{mbti_a}_vs_{mbti_b}_{tag}_{timestamp}.json"
    )
    full_data = {
        "summary": {
            "total_rounds": total_rounds,
            "mbti_a": mbti_a,
            "mbti_b": mbti_b,
            "final_score_a": agent_a.total_score,
            "final_score_b": agent_b.total_score,
            "use_rag": use_rag,
            "experiment_id": experiment_id
        },
        "rounds": experiment_logs
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(full_data, f, ensure_ascii=False, indent=2)
    print(f"实验数据保存至：{filename}")
    print(f"最终得分 - {mbti_a}: {agent_a.total_score} | {mbti_b}: {agent_b.total_score}\n")

    return full_data


if __name__ == "__main__":
    args = sys.argv[1:]
    use_rag = "--no-rag" not in args
    total_rounds = 10
    if "--rounds" in args:
        idx = args.index("--rounds")
        if idx + 1 < len(args):
            total_rounds = int(args[idx + 1])

    mbti_a = "INTJ"
    mbti_b = "ENTJ"
    profiles = _load_profiles()

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    agent_a = MBTIAgent(mbti_a, profiles.get(mbti_a), api_key)
    agent_b = MBTIAgent(mbti_b, profiles.get(mbti_b), api_key)

    run_experiment(agent_a, agent_b, total_rounds=total_rounds, use_rag=use_rag)
