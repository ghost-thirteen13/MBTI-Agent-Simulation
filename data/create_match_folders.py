"""
按人格组合归类所有 1v1 对战，生成独立文件
输出结构：
data/
  ALL/
    INTJ_vs_ENTJ/
      match_20260521_164425.csv
      match_20260522_093000.csv
      ...
    INFP_vs_ESTJ/
      ...
用法：在 data 文件夹下运行 python create_match_folders.py
"""

import pandas as pd
import os

# ==================== 配置 ====================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROUNDS_FILE = os.path.join(SCRIPT_DIR, "rounds_detail.csv")
SUMMARY_FILE = os.path.join(SCRIPT_DIR, "summary.csv")
OUTPUT_ROOT = os.path.join(SCRIPT_DIR, "ALL")   # 所有对战文件夹的总目录
# ==============================================

def get_matchup_folder(mbti_a, mbti_b):
    """生成统一的组合文件夹名（字母排序，避免 INTJ_vs_ENTJ / ENTJ_vs_INTJ 不一致）"""
    types = sorted([mbti_a, mbti_b])   # 按字母排序
    return f"{types[0]}_vs_{types[1]}"

def create_all_folders():
    df_rounds = pd.read_csv(ROUNDS_FILE, encoding='utf-8-sig')
    df_summary = pd.read_csv(SUMMARY_FILE, encoding='utf-8-sig')

    # 按 experiment_id 分组（每场唯一）
    grouped = df_rounds.groupby('experiment_id')
    os.makedirs(OUTPUT_ROOT, exist_ok=True)

    generated_count = 0

    for exp_id, round_rows in grouped:
        # 从 summary 获取该场信息
        match_info = df_summary[df_summary['experiment_id'] == exp_id]
        if match_info.empty:
            continue
        info = match_info.iloc[0]

        mbti_a = info['mbti_a']
        mbti_b = info['mbti_b']
        file_stem = info['file']          # 原始文件名，含时间戳
        final_a = info['final_score_a']
        final_b = info['final_score_b']
        total_rounds = info['total_rounds']
        use_rag = info['use_rag']

        # 确定组合文件夹
        matchup_dir = get_matchup_folder(mbti_a, mbti_b)
        full_dir = os.path.join(OUTPUT_ROOT, matchup_dir)
        os.makedirs(full_dir, exist_ok=True)

        # 输出文件名：match_时间戳部分.csv
        # 假设 file_stem 格式为 experiment_results_20260521_164425
        ts_part = file_stem.replace("experiment_results_", "")   # "20260521_164425"
        out_filename = f"match_{ts_part}.csv"
        out_path = os.path.join(full_dir, out_filename)

        # 写入文件（CSV 格式，前几行为注释）
        with open(out_path, 'w', encoding='utf-8-sig') as f:
            f.write(f"# Experiment ID: {exp_id}\n")
            f.write(f"# Matchup: {mbti_a} vs {mbti_b}\n")
            f.write(f"# Final scores: {mbti_a}={final_a}, {mbti_b}={final_b}\n")
            f.write(f"# Total rounds: {total_rounds}, RAG used: {use_rag}\n")
            f.write(f"# Original file: {file_stem}.json\n")
            f.write("#\n")
            # 写入轮次数据（沿用原 rounds_detail 的列）
            round_rows.to_csv(f, index=False)

        generated_count += 1

    print(f"完成！共生成 {generated_count} 场比赛文件，存放于 {OUTPUT_ROOT}")

if __name__ == "__main__":
    create_all_folders()