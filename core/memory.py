"""
轻量内存记忆模块（支持按 Agent ID 隔离）
- 每个实验内不同 Agent 拥有独立记忆空间
- 实验结束对象销毁后内存自动清空
"""
class MemoryHandler:
    def __init__(self, environment_name="desert", experiment_id="default"):
        # key: agent_id, value: list of experience strings
        self.storage = {}
        self.environment = environment_name
        self.experiment_id = experiment_id

    def store(self, experience_context: str, agent_id: int, round_num: int, metadata: dict = None):
        """存储一条经验到指定 Agent"""
        if agent_id not in self.storage:
            self.storage[agent_id] = []
        entry = f"[轮{round_num}] {experience_context}"
        self.storage[agent_id].append(entry)
        # 只保留最近 10 条
        if len(self.storage[agent_id]) > 10:
            self.storage[agent_id] = self.storage[agent_id][-10:]

    def retrieve(self, state_desc: str, agent_id: int, top_k: int = 3) -> str:
        """检索指定 Agent 的记忆（最近 top_k 条，倒序）"""
        if agent_id not in self.storage or not self.storage[agent_id]:
            return ""
        recent = self.storage[agent_id][-top_k:][::-1]
        return "；\n".join(recent)