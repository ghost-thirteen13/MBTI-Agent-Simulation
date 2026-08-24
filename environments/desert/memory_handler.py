import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os

class MemoryHandler:
    def __init__(self, agent_id, vector_dim=4, store_dir=None):
        self.agent_id = agent_id
        self.vector_dim = vector_dim
        # 默认存储位置：项目根 data/memory/
        if store_dir is None:
            base = os.path.dirname(os.path.abspath(__file__))  # environments/desert/
            store_dir = os.path.join(base, "..", "..", "data", "memory")
        self.store_dir = store_dir
        self.memory = []   # (vector, action, reward)
        os.makedirs(store_dir, exist_ok=True)

    def _encode_obs(self, obs: dict):
        node_norm = (obs['node'] - 1) / 24.0
        water_norm = obs['water'] / 200.0
        food_norm = obs['food'] / 200.0
        type_map = {'start': 0, 'normal': 1, 'village': 2, 'mine': 3, 'end': 4}
        type_id = type_map.get(obs['type'], 1)
        type_norm = type_id / 4.0
        return np.array([node_norm, water_norm, food_norm, type_norm])

    def store(self, obs: dict, action: int, reward: float):
        vec = self._encode_obs(obs)
        self.memory.append((vec, action, reward))
        self._save()

    def retrieve(self, query_obs: dict, top_k=5):
        if not self.memory:
            return ""
        query_vec = self._encode_obs(query_obs).reshape(1, -1)
        vectors = [mem[0] for mem in self.memory]
        X = np.array(vectors)
        if X.shape[0] == 0:
            return ""
        sims = cosine_similarity(query_vec, X)[0]
        top_indices = np.argsort(sims)[-top_k:][::-1]

        reminiscences = []
        for idx in top_indices:
            vec, action, reward = self.memory[idx]
            reminiscences.append(
                f"曾经在类似状态（节点{int(vec[0]*24)+1}, 水{vec[1]*200:.0f}, 食物{vec[2]*200:.0f}）"
                f"选择了动作{action}，获得奖励{reward}"
            )
        return "\n".join(reminiscences)

    def clear(self):
        self.memory = []
        filepath = os.path.join(self.store_dir, f"{self.agent_id}.pkl")
        if os.path.exists(filepath):
            os.remove(filepath)

    def _save(self):
        filepath = os.path.join(self.store_dir, f"{self.agent_id}.pkl")
        with open(filepath, "wb") as f:
            pickle.dump(self.memory, f)

    def _load(self):
        filepath = os.path.join(self.store_dir, f"{self.agent_id}.pkl")
        if os.path.exists(filepath):
            with open(filepath, "rb") as f:
                self.memory = pickle.load(f)
