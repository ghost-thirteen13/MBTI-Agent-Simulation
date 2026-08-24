# Agent类

# core/agent.py

import json
import re
import random
import os
import sys
from openai import OpenAI
from httpx import Timeout

# 确保能导入 config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from environments.desert.config import DesertConfig


class MBTIAgent:
    # 天气中文到英文映射
    WEATHER_CN2EN = {
        '晴天': 'sunny',
        '高温': 'hot',
        '沙暴': 'sandstorm'
    }

    def __init__(self, mbti_type: str, profile_file: str = None,
                 api_key: str = None,
                 base_url: str = "https://api.deepseek.com",
                 model: str = "deepseek-v4-pro"):
        self.mbti_type = mbti_type
        self.model = model

        # API Key：环境变量优先，其次传入参数，最后测试用临时回退
        if api_key is None:
            api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("未找到 API Key：请设置环境变量 DEEPSEEK_API_KEY")
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=Timeout(10.0, read=120.0, write=10.0, connect=5.0)
        )

        # 加载 MBTI 人格配置
        if profile_file is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            profile_file = os.path.join(base_dir, "..", "config", "mbti_profiles.json")
        try:
            with open(profile_file, "r", encoding="utf-8") as f:
                profiles = json.load(f)
        except FileNotFoundError:
            print(f"[警告] 未找到人格配置文件 {profile_file}，使用默认系统提示。")
            profiles = {}
        self.profile = profiles.get(mbti_type, {})

        default_sys = (
            f"你是一名 {mbti_type} 型人格的沙漠穿越者。\n"
            "你的核心目标是：**在保证生存的前提下，尽快抵达终点，同时最大化剩余资金**。\n"
            "请综合地图信息、当前资源、天气与记忆，做出经得起推敲的理性决策。"
        )
        self.system_prompt = self.profile.get("system_prompt", default_sys)

    @staticmethod
    def _build_action_desc(valid_actions):
        mapping = {
            0: "0-上", 1: "1-下", 2: "2-左", 3: "3-右",
            4: "4-停留", 5: "5-挖掘(仅矿山)", 6: "6-购买补给(仅村庄)"
        }
        return "、".join(mapping[a] for a in valid_actions if a in mapping)

    def _obs_to_prompt(self, obs: dict):
        node = obs['node']
        node_type = obs['type']
        water = obs['water']
        food = obs['food']
        money = obs['money']
        weather_cn = obs['weather']
        map_desc = obs.get('map_desc', '无地图信息')

        # 计算可用动作
        valid_actions = [0, 1, 2, 3, 4]
        if node_type == 'mine':
            valid_actions.append(5)
        if node_type == 'village':
            valid_actions.append(6)

        # 获取英文天气键，用于查询消耗
        weather_en = self.WEATHER_CN2EN.get(weather_cn, 'sunny')
        base_water = DesertConfig.WATER_CONSUME[weather_en]
        base_food = DesertConfig.FOOD_CONSUME[weather_en]

        # 拼接决策信息
        desc = f"""当前状态：
{map_desc}
当前位置：节点{node}（{node_type}）
天气：{weather_cn}
资源：水 {water:.1f} 箱, 食物 {food:.1f} 箱
资金：{money:.1f} 元
基础消耗（水/食物）：{base_water}/{base_food} 箱/天
移动消耗：{DesertConfig.ACTION_CONSUME_MULT['move']}倍基础，挖掘消耗：{DesertConfig.ACTION_CONSUME_MULT['mine']}倍基础，停留/购买消耗：1倍基础
挖矿收益：{DesertConfig.BASE_MINING_INCOME}元/天
村庄购买：水{DesertConfig.WATER_PRICE * DesertConfig.VILLAGE_PRICE_MULT}元/箱，食物{DesertConfig.FOOD_PRICE * DesertConfig.VILLAGE_PRICE_MULT}元/箱（单次上限{DesertConfig.MAX_WATER}箱）
目的地退回：水{DesertConfig.WATER_PRICE * DesertConfig.END_RETURN_MULT}元/箱，食物{DesertConfig.FOOD_PRICE * DesertConfig.END_RETURN_MULT}元/箱
可用动作：{self._build_action_desc(valid_actions)}"""
        if 6 in valid_actions:
            desc += "\n若选择6，需指定购买数量，格式: [Action] 6 [Buy water: 30 food: 20]"
        return desc, valid_actions

    def _call_llm(self, messages):
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=4096,   # 足够长的输出，但避免极端值
                stream=False
            )
            if not completion.choices:
                print(f"[错误] LLM 返回空 choices: {completion}")
                return None
            return completion.choices[0].message.content
        except Exception as e:
            print(f"[LLM调用失败] {e}")
            return None

    def act(self, obs: dict, agent_id: int = 0, memory_context: str = ""):
        desc, valid_actions = self._obs_to_prompt(obs)
        user_message = f"{desc}\n\n"
        if memory_context:
            user_message += f"历史经验提示：\n{memory_context}\n\n"
        user_message += "请在思考后输出最终动作，格式： [Action] 编号 [可选参数]"

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message}
        ]

        full_reply = self._call_llm(messages)
        if not full_reply:
            # LLM 调用失败，安全动作：停留
            print(f"[回退] Agent{agent_id} LLM 无回复，强制停留")
            return 4, "[LLM无回复]", None

        # 实时打印思考过程（可注释以减少刷屏）
        print(f"[思考: Agent{agent_id}] {full_reply[:200]}...")  # 只打印前200字符，避免过长

        # 解析动作
        match = re.search(r'\[Action\]\s*(\d+)', full_reply, re.IGNORECASE)
        action = None
        if match:
            action = int(match.group(1))
        else:
            # 宽松匹配：查找第一个 1-6 的数字
            nums = re.findall(r'\b([1-6])\b', full_reply)
            if nums:
                action = int(nums[0])
                print(f"[解析] 未找到[Action]标签，回退到数字 {action}")
            else:
                print(f"[警告] 未找到动作，强制停留。原始回复：{full_reply[:100]}...")
                return 4, full_reply, None

        # 校验合法性
        if action not in valid_actions:
            print(f"[警告] 动作 {action} 不合法（可行动作: {valid_actions}），强制停留。")
            return 4, full_reply, None

        # 购买参数解析
        params = None
        if action == 6:
            buy_match = re.search(r'\[Buy water:\s*(\d+)\s+food:\s*(\d+)\]', full_reply, re.IGNORECASE)
            if buy_match:
                w = int(buy_match.group(1))
                f = int(buy_match.group(2))
                params = {'buy_water': w, 'buy_food': f}
            else:
                # 默认购买少量，避免无效动作
                params = {'buy_water': 10, 'buy_food': 10}
                print("[解析] 未指定购买量，默认各买10箱")

        return action, full_reply, params