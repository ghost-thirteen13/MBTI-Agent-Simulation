class MockAgent:
    def __init__(self, mbti_type):
        self.mbti_type = mbti_type

    def act(self, obs, agent_id=0, memory_context=""):
        node = obs['node']
        node_type = obs['type']
        neighbors = obs['neighbors']  # 实际可移动的相邻节点列表

        # 优先向右移动，其次向下，否则停留
        if node_type == 'village' and obs['money'] > 100:
            return 6, "mock buy", {'buy_water': 20, 'buy_food': 20}
        if node_type == 'mine':
            return 5, "mock mine", None

        # 根据邻居选择方向
        # 方向映射：上(0),下(1),左(2),右(3)
        # 先尝试右移（节点号增1），再下移（增5），再其他
        for direction, delta in [(3,1), (1,5), (2,-1), (0,-5)]:
            target = node + delta
            if target in neighbors:
                return direction, f"mock move to {target}", None

        return 4, "mock stay", None