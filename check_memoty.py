from pymilvus import connections, Collection

connections.connect(host="localhost", port="19530")
col = Collection("game_memory")
col.load()

# 查询总条数
print(f"总记录数: {col.num_entities}")

# 获取前 10 条（需要指定输出字段）
results = col.query(
    expr="id >= 0",
    output_fields=["agent_mbti", "round", "my_action", "opponent_action", "my_payoff", "context_text"],
    limit=10
)
for r in results:
    print(r)