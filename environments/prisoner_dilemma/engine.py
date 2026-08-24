# 博弈环境逻辑（得分，历史记录）
from environments.base import BaseEnvironment

class PrisonerDilemmaEnv(BaseEnvironment):
    """
    博弈引擎（信任博弈环境）

    负责管理囚徒困境的收益矩阵，记录每一轮的历史对话，根据双方动作计算并返回本轮得分
    待完成：策略输出？策略迭代？
    """
    def __init__(self, config: dict = None):
        # 定义收益矩阵
        """
        矩阵以（我方动作，对方动作）为键，对应的值为（我方得分，对方得分）元组
        动作说明：'C'表示合作(Cooperate)，'D'表示欺骗(Defect)
        采用的收益值：
        - 双方均合作(C,C):各得两分
        - 我方合作，对方欺骗(C,D):我方-1分，对方3分
        - 我方欺骗，对方合作(D,C):我方3分，对方-1分
        - 双方均欺骗(D,D):各得0分
        
        这套数值满足经典的囚徒困境条件：
        T(欺骗诱惑) > R(合作奖励) > P(相互欺骗惩罚) > S(受骗支付)
        即 3 > 2 > 0 > -1
        """
        super().__init__(config)
        self.total_rounds = self.config.get("total_rounds", 50)
        self.payoff_matrix = {
            ('C', 'C'): (2, 2),
            ('C', 'D'): (-1, 3),
            ('D', 'C'): (3, -1),
            ('D', 'D'): (0, 0)
        }

        """历史记录容器
        列表每个元素将是一个字典，包含一轮对局的完整信息
        格式示例：{'move_a': 'C', 'move_b': 'D', 'score_a': '-1', 'score_b': '3'}
        """
        self.history = []
        self.current_round = 0

    def reset(self) -> dict:
        """重置环境，返回初始状态"""
        self.history = []
        self.current_round = 0
        return {
            "round": 0,
            "total_rounds": self.total_rounds,
            "history": [],
            "is_first_round": True
        }

    def record_round(self, move_a: str, move_b: str) -> tuple:
        """
        执行一轮双方决策
        返回: (state, reward, done, info)
        - state: dict, 本轮后的状态
        - reward: tuple (score_a, score_b), 双方收益
        - done: bool, 是否结束
        - info: dict, 额外信息
        """
        # 从收益矩阵中获取对应动作组合的得分
        scores = self.payoff_matrix[(move_a, move_b)]
        self.history.append({
            "round": self.current_round + 1,
            "move_a": move_a,
            "move_b": move_b,
            "score_a": scores[0],
            "score_b": scores[1]
        })
        self.current_round = len(self.history)

        state = {
            "round": self.current_round,
            "total_rounds": self.total_rounds,
            "history": self.history.copy(),
            "is_first_round": False
        }
        reward = scores  # (score_a, score_b)
        done = self.current_round >= self.total_rounds
        info = {
            "move_a": move_a,
            "move_b": move_b,
            "score_a": scores[0],
            "score_b": scores[1]
        }
        return state, reward, done, info

    def render(self, self_role: str = 'A') -> str:
        """
        返回当前状态的自然语言描述
        self_role: 'A' 或 'B'，表示返回哪个视角的描述
        """
        if not self.history:
            return "这是第1轮，暂无历史记录。"

        lines = []
        for h in self.history[-3:]:  # 最近3轮
            if self_role == 'A':
                lines.append(f"轮{h['round']}: 我方{h['move_a']}, 对方{h['move_b']}, 得分{h['score_a']}:{h['score_b']}")
            else:
                lines.append(f"轮{h['round']}: 我方{h['move_b']}, 对方{h['move_a']}, 得分{h['score_b']}:{h['score_a']}")

        summary = "；".join(lines)
        return f"当前第{self.current_round + 1}轮（共{self.total_rounds}轮）。最近局势：{summary}"

    def get_total_score(self, role: str) -> int:
        """获取某个角色的累计得分"""
        if role == 'A':
            return sum(h['score_a'] for h in self.history)
        else:
            return sum(h['score_b'] for h in self.history)