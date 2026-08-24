"""
实验数据提取脚本
- 从指定时间范围内的 experiment_results_*.json 中提取轮次得分与总览
- JSON 数据目录：D:\Desktop\my_work\test\learn\Agent\logs
- 脚本所在目录（data）用于存放输出 CSV
用法：直接运行
"""

import json
import glob
import os
import pandas as pd
from pathlib import Path

# ==================== 配置区 ====================
DATA_DIR = r"D:\Desktop\my_work\test\learn\Agent\logs"   # JSON 文件存放目录
START_TS = "20260521164425"                              # 起始时间戳（包含）
END_TS   = "20260523202404"                              # 结束时间戳（包含）

# 输出目录：脚本所在文件夹
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_ROUNDS = os.path.join(OUT_DIR, "rounds_detail.csv")
OUTPUT_SUMMARY = os.path.join(OUT_DIR, "su  mmary.csv")
# =================================================

def timestamp_from_filename(filepath):
    """从文件名中提取紧凑时间戳"""
    stem = Path(filepath).stem
    ts_part = stem.replace("experiment_results_", "")
    return ts_part.replace("_", "")

def filter_files_by_time(data_dir, start_ts, end_ts):
    """根据时间戳范围筛选文件列表"""
    pattern = str(Path(data_dir) / "experiment_results_*.json")
    all_files = sorted(glob.glob(pattern))
    selected = []
    for f in all_files:
        ts = timestamp_from_filename(f)
        if start_ts <= ts <= end_ts:
            selected.append(f)
    return selected

def extract_data(file_list):
    """解析 JSON 并返回轮次明细与总览的 DataFrame"""
    rounds_records = []
    summary_records = []

    for fpath in file_list:
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        summary = data['summary']
        file_stem = Path(fpath).stem
        mbti_a = summary['mbti_a']
        mbti_b = summary['mbti_b']
        final_a = summary['final_score_a']
        final_b = summary['final_score_b']
        exp_id = summary['experiment_id']
        use_rag = summary['use_rag']

        # 总览记录
        summary_records.append({
            'file': file_stem,
            'experiment_id': exp_id,
            'mbti_a': mbti_a,
            'mbti_b': mbti_b,
            'final_score_a': final_a,
            'final_score_b': final_b,
            'total_rounds': summary['total_rounds'],
            'use_rag': use_rag
        })

        # 轮次记录
        for rnd in data['rounds']:
            round_num = rnd['round']
            scores = rnd['scores']
            decisions = (rnd.get(f'{mbti_a}_decision', ''),
                         rnd.get(f'{mbti_b}_decision', ''))
            thoughts = (rnd.get(f'{mbti_a}_thought', ''),
                        rnd.get(f'{mbti_b}_thought', ''))

            rounds_records.append({
                'file': file_stem,
                'experiment_id': exp_id,
                'mbti_a': mbti_a,
                'mbti_b': mbti_b,
                'round': round_num,
                'score_a': scores[0],
                'score_b': scores[1],
                'decision_a': decisions[0],
                'decision_b': decisions[1],
                'thought_a': thoughts[0],
                'thought_b': thoughts[1]
            })

    return pd.DataFrame(rounds_records), pd.DataFrame(summary_records)

if __name__ == "__main__":
    print(f"扫描目录: {DATA_DIR}")
    files = filter_files_by_time(DATA_DIR, START_TS, END_TS)
    if not files:
        print("未找到匹配的时间戳文件，请检查 DATA_DIR 和时间范围。")
        exit(0)

    print(f"找到 {len(files)} 个文件，开始提取...")
    df_rounds, df_summary = extract_data(files)

    df_rounds.to_csv(OUTPUT_ROUNDS, index=False, encoding='utf-8-sig')
    df_summary.to_csv(OUTPUT_SUMMARY, index=False, encoding='utf-8-sig')

    print(f"完成！")
    print(f"  轮次明细: {OUTPUT_ROUNDS}  ({len(df_rounds)} 行)")
    print(f"  实验总览: {OUTPUT_SUMMARY}  ({len(df_summary)} 行)")

    if not df_summary.empty:
        df_summary['timestamp'] = df_summary['file'].str.extract(r'_(\d{8}_\d{6})')
        print(f"  时间范围: {df_summary['timestamp'].min()}  ~  {df_summary['timestamp'].max()}")