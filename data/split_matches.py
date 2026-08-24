"""
按 1v1 配对拆分实验数据
从 rounds_detail.csv 和 summary.csv 中，为每场比赛生成独立文件
输出目录：data/matches/
"""

import pandas as pd
import os

# ==================== 配置 ====================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROUNDS_FILE = os.path.join(SCRIPT_DIR, "rounds_detail.csv")
SUMMARY_FILE = os.path.join(SCRIPT_DIR, "summary.csv")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "matches")
# ==============================================

def create_match_files():
    # 读取数据
    df_rounds = pd.read_csv(ROUNDS_FILE, encoding='utf-8-sig')
    df_summary = pd.read_csv(SUMMARY_FILE, encoding='utf-8-sig')

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 按 experiment_id 分组（唯一标识一场比赛）
    grouped_rounds = df_rounds.groupby('experiment_id')
    
    for exp_id, group in grouped_rounds:
        # 从 summary 中找到对应的元信息（应该只有一行）
        match_summary = df_summary[df_summary['experiment_id'] == exp_id].iloc[0]
        mbti_a = match_summary['mbti_a']
        mbti_b = match_summary['mbti_b']
        file_stem = match_summary['file']  # 原始文件名，含时间戳
        
        # 构建输出文件名
        safe_filename = f"match_{mbti_a}_vs_{mbti_b}_{file_stem}.csv"
        out_path = os.path.join(OUTPUT_DIR, safe_filename)
        
        # 先写元信息注释
        with open(out_path, 'w', encoding='utf-8-sig') as f:
            f.write(f"# Experiment ID: {exp_id}\n")
            f.write(f"# {mbti_a} vs {mbti_b}\n")
            f.write(f"# Final scores: {mbti_a}={match_summary['final_score_a']}, {mbti_b}={match_summary['final_score_b']}\n")
            f.write(f"# Total rounds: {match_summary['total_rounds']}, Use RAG: {match_summary['use_rag']}\n")
            f.write(f"# Original file: {file_stem}.json\n")
            f.write("#\n")
            # 写入列名（仅一次）
            group.to_csv(f, index=False)
        
        print(f"已生成: {safe_filename}")

    print(f"拆分完成！共生成 {len(grouped_rounds)} 个文件，保存在 {OUTPUT_DIR}")

if __name__ == "__main__":
    create_match_files()
    