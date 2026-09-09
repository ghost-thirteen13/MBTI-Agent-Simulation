# memory/memory.py
# RAG 记忆：Milvus 向量库 + 中文句向量模型，为 Agent 提供跨轮次经验检索
import os
import numpy as np
from pymilvus import connections, Collection
from sentence_transformers import SentenceTransformer

_model = None
_collection = None


def init_memory(milvus_host="localhost", milvus_port="19530"):
    """加载句向量模型 + 连接 Milvus，各只执行一次。"""
    global _model, _collection

    # 句向量模型缓存目录（放 D 盘，避免占用 C 盘；可被环境变量覆盖）
    _home = os.environ.get("SENTENCE_TRANSFORMERS_HOME") or r"D:\caches\torch\sentence_transformers"
    os.environ["SENTENCE_TRANSFORMERS_HOME"] = _home
    # 首次下载 / 补文件时走国内镜像（离线模式下不会访问）
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    # 强制离线，从本地缓存加载模型（模型需已下载到位）
    os.environ["HF_HUB_OFFLINE"] = "1"

    print("[加载] 从本地缓存加载句向量模型 (bge-small-zh-v1.5, 离线)...")
    _model = SentenceTransformer("BAAI/bge-small-zh-v1.5", device="cpu")
    print("[OK] 句向量模型加载成功")

    connections.connect(host=milvus_host, port=milvus_port)
    _collection = Collection("game_memory")
    _collection.load()
    print("[OK] Milvus 记忆模块已就绪")


def _embed(text: str) -> np.ndarray:
    return _model.encode(text, normalize_embeddings=True)


def store_experience(experiment_id, agent_mbti, opponent_mbti, round_num,
                     my_action, opponent_action, my_payoff, opponent_payoff,
                     context_text):
    """写入一条经验。字段与 init_milvus.py 建的 Collection 一一对应。"""
    vec = _embed(context_text).tolist()
    data = [
        [experiment_id], [agent_mbti], [opponent_mbti], [round_num],
        [my_action], [opponent_action], [my_payoff], [opponent_payoff],
        [context_text], [vec]
    ]
    _collection.insert(data)
    _collection.flush()


def retrieve_similar(agent_mbti, experiment_id, query_text, top_k=5):
    """按「实验ID + 人格」过滤，检索语义最相近的 top_k 条经验。"""
    query_vec = _embed(query_text).tolist()
    search_params = {"metric_type": "IP", "params": {"nprobe": 16}}
    expr = f'experiment_id == "{experiment_id}" and agent_mbti == "{agent_mbti}"'
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
