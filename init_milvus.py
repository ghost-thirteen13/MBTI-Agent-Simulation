# init_milvus.py
# 初始化 Milvus 的 game_memory 集合（建表 + 建索引）
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility

connections.connect(host="localhost", port="19530")

# 已存在则先删除重建，保证 schema 一致
if utility.has_collection("game_memory"):
    utility.drop_collection("game_memory")
    print("已删除旧 Collection")

fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="experiment_id", dtype=DataType.VARCHAR, max_length=64),
    FieldSchema(name="agent_mbti", dtype=DataType.VARCHAR, max_length=8),
    FieldSchema(name="opponent_mbti", dtype=DataType.VARCHAR, max_length=8),
    FieldSchema(name="round", dtype=DataType.INT64),
    FieldSchema(name="my_action", dtype=DataType.VARCHAR, max_length=1),
    FieldSchema(name="opponent_action", dtype=DataType.VARCHAR, max_length=1),
    FieldSchema(name="my_payoff", dtype=DataType.FLOAT),
    FieldSchema(name="opponent_payoff", dtype=DataType.FLOAT),
    FieldSchema(name="context_text", dtype=DataType.VARCHAR, max_length=512),
    FieldSchema(name="context_vector", dtype=DataType.FLOAT_VECTOR, dim=512)
]

schema = CollectionSchema(fields, description="MBTI agent game memory")
collection = Collection(name="game_memory", schema=schema)

index_params = {
    "metric_type": "IP",
    "index_type": "IVF_FLAT",
    "params": {"nlist": 128}
}
collection.create_index(field_name="context_vector", index_params=index_params)

print("[OK] 新 Collection 'game_memory' 创建成功")
