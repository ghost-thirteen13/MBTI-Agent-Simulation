# core/agent.py
# MBTIAgent：把 MBTI 人格注入大模型，让它在囚徒困境中做出 C/D 决策

import os
import re
from openai import OpenAI
from httpx import Timeout


class MBTIAgent:
    """MBTI 人格 Agent，调用 DeepSeek 大模型做囚徒困境决策（输出 C 或 D）。"""

    def __init__(self, mbti_type: str, profile: dict = None,
                 api_key: str = None,
                 base_url: str = "https://api.deepseek.com",
                 model: str = "deepseek-chat"):
        self.mbti_type = mbti_type
        self.model = model
        self.total_score = 0  # 累计得分，由 runner 每轮累加

        # API Key：传入参数优先，其次环境变量
        if api_key is None:
            api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("未找到 API Key：请设置环境变量 DEEPSEEK_API_KEY 或传入 api_key 参数")
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=Timeout(10.0, read=120.0, write=10.0, connect=5.0)
        )

        # 人格配置：直接收 dict（含 personality / traits）
        self.profile = profile or {}
        personality = self.profile.get("personality", mbti_type)
        traits = self.profile.get("traits", "")
        self.system_prompt = self._build_system_prompt(personality, traits)

    def _build_system_prompt(self, personality: str, traits: str) -> str:
        """构造囚徒困境专用的、注入 MBTI 人格的 system prompt。"""
        return (
            f"你正在参与一场反复进行的囚徒困境博弈，你的人格是 {personality}。\n"
            f"你的人格特质：{traits}\n\n"
            "博弈规则：每一轮你与对手各自在「合作(C)」与「背叛(D)」之间做出选择，"
            "双方选择同时揭晓，按如下矩阵计分：\n"
            "- 都合作(C,C)：双方各 +2\n"
            "- 你合作、对方背叛(C,D)：你 -1，对方 +3\n"
            "- 你背叛、对方合作(D,C)：你 +3，对方 -1\n"
            "- 都背叛(D,D)：双方各 +0\n\n"
            "你的目标：在始终符合你人格特质的前提下，追求多轮累计得分最大化。\n"
            "你会看到最近几轮的历史与可选的经验记忆，请基于它们，"
            "以你的人格视角做出经得起推敲的决策。"
        )

    def _call_llm(self, messages):
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2048,
                stream=False
            )
            if not completion.choices:
                print(f"[错误] LLM 返回空 choices: {completion}")
                return None
            return completion.choices[0].message.content
        except Exception as e:
            print(f"[LLM调用失败] {e}")
            return None

    def decide(self, state_description: str, memory_context: str = ""):
        """
        做出本轮决策。
        参数：
            state_description: 当前局势的自然语言描述
            memory_context:    检索到的历史经验（可选，无 RAG 时为空串）
        返回：(move, thought)，move 为 'C' 或 'D'，thought 为完整思考文本
        """
        user_message = f"{state_description}\n\n"
        if memory_context:
            user_message += f"历史经验提示：\n{memory_context}\n\n"
        user_message += "请先思考，然后只输出你的最终动作，格式： [Action] C 或 [Action] D"

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message}
        ]

        full_reply = self._call_llm(messages)
        if not full_reply:
            # LLM 调用失败，安全默认：合作
            print(f"[回退] {self.mbti_type} LLM 无回复，默认合作 C")
            return "C", "[LLM无回复]"

        move = self._parse_move(full_reply)
        return move, full_reply

    @staticmethod
    def _parse_move(reply: str) -> str:
        """从 LLM 回复中解析出 C/D，解析失败默认合作 C。"""
        # 1) 优先匹配 [Action] C / [Action] D
        match = re.search(r'\[Action\]\s*([CD])', reply, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        # 2) 中文关键词兜底：取最后出现的「合作/背叛」（结论通常在结尾）
        coop = reply.rfind('合作')
        defect = reply.rfind('背叛')
        if coop != -1 or defect != -1:
            return 'C' if coop > defect else 'D'
        # 3) 英文字母兜底：取最后一个单独出现的 C/D
        found = re.findall(r'\b([CD])\b', reply, re.IGNORECASE)
        if found:
            return found[-1].upper()
        print(f"[警告] 未解析出 C/D，默认合作 C。原始回复：{reply[:100]}...")
        return "C"
