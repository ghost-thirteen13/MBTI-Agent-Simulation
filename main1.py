import json
import os
import uuid
import itertools
from environments.prisoner_dilemma.engine import TrustEngine
from core.agent import MBTIAgent
from environments.prisoner_dilemma.engine import TrustEngine
from memory.memory import init_memory, store_experience, retrieve_similar
from datetime import datetime

# 初始化（加载模型 + 连接 Milvus，各一次）
init_memory()

# 配置 API Key
# 后续改为通过环境变量设置
API_KEY = os.environ.get("DEEPSEEK_API_KEY")

def format_memories(memories: list) -> str:
    """
    将检索到的记忆列表转换为自然语言文本。
    输入：[{"context": ..., "round": ..., "my_action": ..., "opponent_action": ..., "my_payoff": ..., "score": ...}, ...]
    输出：格式化的多行文本，用于注入 prompt。
    """
    if not memories:
        return "无相关记忆。"
    lines = []
    for i, mem in enumerate(memories, 1):
        lines.append(
            f"{i}. 第{mem['round']}轮：我{mem['my_action']}，对方{mem['opponent_action']}，收益{mem['my_payoff']}。"
        )
    return "\n".join(lines)

# 从 mbti_profiles.json 中读取所有人格类型，随机对战
def get_all_pairs():
    with open('config/mbti_profiles.json', 'r', encoding='utf-8') as f:
        profiles = json.load(f)
    mbti_types = list(profiles.keys())
    return list(itertools.combinations(mbti_types, 2))

# 测试轮数，以及调整是否使用rag
def run_experiment(agent_a, agent_b, total_rounds=50, use_rag = True):
    """
    运行一次完整的博弈实验
    参数：
        total_rounds : 博弈轮数
        use_rag      : 是否启用 RAG 记忆（True 时每轮检索并存储经验；False 时为纯人格决策）
    流程：
        1 加载MBTI人格配置文件
        2 初始化博弈引擎与两个不同人格的Agent（此处为INTJ与ENTJ）
        3 进入主循环，每轮两个Agent分别作出决策
        4 引擎结算双方得分并更新历史
        5 记录本轮的决策，思考过程与得分
        6 循环结束后将完整的日志保存为JSON文件，并打印最终总分
    """

    # 生成唯一实验 ID，用于隔离本实验的记忆
    experiment_id = str(uuid.uuid4())

    # 1. 动态获取人格类型
    mbti_a = agent_a.mbti_type
    mbti_b = agent_b.mbti_type
    

    # 2. 初始化环境与 Agent
    # 创建博弈引擎实例，负责计算收益与历史管理
    engine = TrustEngine()

    mode = "有 RAG" if use_rag else "无 RAG"
    print(f"--- 开始博弈: {mbti_a} vs {mbti_b} ({mode},共 {total_rounds} 轮) ---")
    
    # 用于收集每轮完整日志，实验结束后一次性写入文件
    experiment_logs = []

    # 主轮次：按照轮次进行博弈
    for r in range(total_rounds):
        # 3.1 决策前检索记忆
        if use_rag:
            # 构建当前局势的查询文本（可根据需要调整）
            # 使用引擎的简要历史描述
            history_summary = ""
            if engine.history:
                # 只取最近3轮作为上下文，用 enumerate 给出轮次（从当前轮次往前数）
                #后续要改为本轮全局
                recent = engine.history[-3:]
                start_round = len(engine.history) - len(recent) + 1
                entries = []
                for i, h in enumerate(recent, start=start_round):
                    entries.append(
                        f"轮{i}: A选{h['move_a']} B选{h['move_b']} 得分{h['score_a']}:{h['score_b']}"
                    )
                history_summary = "；".join(entries)

            # 查询文本：隐藏对手人格，只写“对手未知”
            query_a = (
                f"第{r+1}轮，我是{mbti_a}，对手未知。最近局势：{history_summary}"
                if history_summary
                else f"第{r+1}轮开始。"
            )
            query_b = (
                f"第{r+1}轮，我是{mbti_b}，对手未知。最近局势：{history_summary}"
                if history_summary
                else f"第{r+1}轮开始。"
            )

            mem_a = retrieve_similar(experiment_id, mbti_a, query_a, top_k=3)
            mem_b = retrieve_similar(experiment_id, mbti_b, query_b, top_k=3)
            mem_text_a = format_memories(mem_a)
            mem_text_b = format_memories(mem_b)
        else:
            mem_text_a = ""
            mem_text_b = ""


        # ----- 3.2 Agent 决策 -----
        state_desc_a = env.render(self_role='A')
        move_a, thought_a = agent_a.decide(
            state_description=state_desc_a,
            memory_context=mem_text
        )
        move_b, thought_b = agent_b.decide(
            mbti_a, engine.history, self_role='B', memory_context=mem_text_b
        )

        # 3.3 环境结算
        # 将双方的动作提交给引擎，引擎根据收益矩阵计算得分并记录历史
        # ----- 3.3 环境结算 -----
        score_a, score_b = engine.record_round(move_a, move_b)
        agent_a.total_score += score_a
        agent_b.total_score += score_b

        # 3.4 实验记录（对应你的 Experimental Testing 习惯）
        # 创建本轮日志条目，包含轮次，决策，思考过程，得分等完整信息
        log_entry = {
            "round": r + 1,
            f"{mbti_a}_decision": move_a,
            f"{mbti_b}_decision": move_b,
            f"{mbti_a}_thought": thought_a,
            f"{mbti_b}_thought": thought_b,
            "scores": (score_a, score_b)
        }
        experiment_logs.append(log_entry)

        # 控制台简要输出，方便实时观察
        print(f"第 {r+1} 轮: {mbti_a}({move_a}) | {mbti_b}({move_b}) -> 本轮得分: {score_a}:{score_b}")

        # 3.5 决策后存储本轮经验（仅 use_rag 时，且绑定实验 ID）
        if use_rag:
            context_a = (
                f"第{r+1}轮，我是{mbti_a}，对手未知，我选择{move_a}，对方选择{move_b}，收益{score_a}。"
            )
            store_experience(
                experiment_id, mbti_a, mbti_b, r+1, move_a, move_b,
                float(score_a), float(score_b), context_a
            )

            context_b = (
                f"第{r+1}轮，我是{mbti_b}，对手未知，我选择{move_b}，对方选择{move_a}，收益{score_b}。"
            )
            store_experience(
                experiment_id, mbti_b, mbti_a, r+1, move_b, move_a,
                float(score_b), float(score_a), context_b
            )

    # 4. 保存数据用于后续 Error/Unexpected 分析
    # 将完整的实验日志写入logs目录下的JSON文件，便于后续的分析和排查意外结果
    # 4.1 确保数据存在
    os.makedirs('logs',exist_ok=True)
    # 4.2 用时间戳生成唯一文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    tag = "rag" if use_rag else "norag"
    filename = f'logs/experiment_{mbti_a}_vs_{mbti_b}_{tag}_{timestamp}.json'
       
    # 构建包含总得分的完整数据
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

    # 4.3 写入文件，异常时给出明确提示
    try:
        with open(filename,'w',encoding='utf-8') as f:
            json.dump(full_data, f, ensure_ascii=False, indent=4)
        print(f'实验数据保存至：{filename}')
    except Exception as e:
        print(f'保存失败: {e}')    
    
    # 5. 输出最终得分
    print(f"最终得分 - {mbti_a}: {agent_a.total_score} | {mbti_b}: {agent_b.total_score}\n")

# 程序入口
# 这样每次只测一对，换人时改人格即可
"""if __name__ == "__main__":
    with open('config/mbti_profiles.json', 'r', encoding='utf-8') as f:
        profiles = json.load(f)

    agent_a = MBTIAgent("INTJ", profiles["INTJ"], API_KEY)
    agent_b = MBTIAgent("ENTJ", profiles["ENTJ"], API_KEY)
    run_experiment(agent_a, agent_b, total_rounds=50, use_rag=True)
    """
if __name__ == "__main__":
    with open('config/mbti_profiles.json', 'r', encoding='utf-8') as f:
        profiles = json.load(f)

    all_types = list(profiles.keys())
    total_pairs = len(all_types) * (len(all_types) - 1)   # 16 × 15 = 240

    # ----- 从现有日志文件中提取已完成的“有序”组合 -----
    completed_pairs = set()   # 存储已完成的有序对 (mbti_a, mbti_b)

    if os.path.exists("logs"):
        for fname in os.listdir("logs"):
            if fname.endswith(".json"):
                filepath = os.path.join("logs", fname)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    summary = data.get("summary", {})
                    a = summary.get("mbti_a")
                    b = summary.get("mbti_b")
                    if a and b:
                        # 注意：这里不排序，保留原始顺序（A vs B 和 B vs A 是不同的）
                        completed_pairs.add((a, b))
                except Exception as e:
                    print(f"⚠️ 无法读取文件 {fname}: {e}")
                    continue

    print(f"已完成的组合数: {len(completed_pairs)} / {total_pairs}")

    # ----- 遍历所有有序组合（固定一个人格，对战其余人格）-----
    for fixed_type in all_types:
        other_types = [t for t in all_types if t != fixed_type]
        for opp_type in other_types:
            pair = (fixed_type, opp_type)   # 有序对
            if pair in completed_pairs:
                print(f"⏭️ 跳过已完成的: {pair[0]} vs {pair[1]}")
                continue

            print(f"\n===== {pair[0]} vs {pair[1]} =====")
            agent_a = MBTIAgent(pair[0], profiles[pair[0]], API_KEY)
            agent_b = MBTIAgent(pair[1], profiles[pair[1]], API_KEY)
            run_experiment(agent_a, agent_b, total_rounds=50, use_rag=True)

    print("\n🎉 全测试已跑完（240组）！")