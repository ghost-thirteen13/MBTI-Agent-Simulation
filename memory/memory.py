# memory.py
import os
import numpy as np
from pathlib import Path
from pymilvus import connections, Collection
from sentence_transformers import SentenceTransformer

_model = None
_collection = None

def init_memory(milvus_host="localhost", milvus_port="19530"):
    global _model, _collection
    
    # --- 1. 设置强制离线环境变量 (必须在导入或加载模型前设置) ---
    os.environ["HF_HUB_OFFLINE"] = "1"  # 关键：强制 Hugging Face Hub 进入离线模式
    # 保留你的镜像设置，离线模式下它不会被访问，但留着无害
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    
    # 指定一个本地缓存路径，确保它在完全断网时也能读取到
    os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(Path.home() / ".cache" / "torch" / "sentence_transformers")

    print("⏳ 从本地缓存加载句向量模型 (强制离线模式)...")
    try:
        # 模型名称保持不变，库会自动在 SENTENCE_TRANSFORMERS_HOME 指定的路径下查找
        _model = SentenceTransformer("BAAI/bge-small-zh-v1.5", device="cpu")
        print("✅ 模型加载成功")
    except Exception as e:
        print("❌ 模型加载失败，请检查缓存路径是否正确，以及模型文件是否完整。")
        print("   尝试的缓存路径:", os.environ["SENTENCE_TRANSFORMERS_HOME"])
        raise

    # --- 2. 连接 Milvus ---
    connections.connect(host=milvus_host, port=milvus_port)
    _collection = Collection("game_memory")
    _collection.load()
    print("✅ Milvus 记忆模块已就绪")


def _embed(text: str) -> np.ndarray:
    return _model.encode(text, normalize_embeddings=True)


def store_experience(environment: str,
                     experiment_id: str,
                     agent_mbti: str,
                     opponent_mbti: str,
                     round_num: int,
                     my_action: str,
                     opponent_action: str,
                     my_payoff: float,
                     opponent_payoff: float,
                     context_text: str):
    vec = _embed(context_text).tolist()
    data = [[environment], [experiment_id], [agent_mbti], [opponent_mbti], [round_num],
            [my_action], [opponent_action],
            [my_payoff], [opponent_payoff],
            [context_text], [vec]]
    _collection.insert(data)
    _collection.flush()


def retrieve_similar(environment: str,
                     agent_mbti: str,
                     experiment_id: str,
                     query_text: str,
                     top_k: int = 5) -> list:
    query_vec = _embed(query_text).tolist()
    search_params = {"metric_type": "IP", "params": {"nprobe": 16}}
    # 三重过滤：环境 + 实验ID + 人格
    expr = f'environment == "{environment}" and experiment_id == "{experiment_id}" and agent_mbti == "{agent_mbti}"'
    results = _collection.search(
        data=[query_vec],
        anns_field="context_vector",
        param=search_params,
        limit=top_k,
        expr=expr,
        output_fields=["agent_mbti", "round", "my_action", "opponent_action",
                       "my_payoff", "context_text"]
    )
    hits = []
    for hit in results[0]:
        entity = hit.entity
        hits.append({
            "context": entity.context_text,
            "round": entity.round,
            "my_action": entity.my_action,
            "opponent_action": entity.opponent_action,
            "my_payoff": entity.my_payoff,
            "score": hit.distance
        })
    return hits