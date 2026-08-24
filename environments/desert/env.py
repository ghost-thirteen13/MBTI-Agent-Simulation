# environments/desert/multiagent_env.py

import random
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from environments.desert.map_loader import MapLoader
from environments.desert.config import DesertConfig

class MultiAgentDesertCrossingEnv:
    # 动作常量不变
    UP, DOWN, LEFT, RIGHT, STAY, MINE, BUY = 0, 1, 2, 3, 4, 5, 6

    def __init__(self, n_agents=2, agent_mbtis=None, max_steps=30, weather_random_seed=None):
        self.n_agents = n_agents
        self.map = MapLoader.generate_desert_map()   # map_loader 已用 config
        self.max_steps = max_steps
        self.agent_mbtis = agent_mbtis if agent_mbtis else ['INTJ'] * n_agents
        self.current_weather = 'sunny'  # 内部用英文
        self.weather_sequence = []
        self.rng = random.Random(weather_random_seed)
        self.step_count = 0
        self.done = False
        # 天气中英文映射
        self._weather_cn = {'sunny': '晴天', 'hot': '高温', 'sandstorm': '沙暴'}

    def reset(self):
        self.weather_sequence = DesertConfig.generate_weather_sequence(self.max_steps)
        self.agents = []
        for i in range(self.n_agents):
            self.agents.append({
                'id': i,
                'node': DesertConfig.START,
                'water': DesertConfig.INITIAL_WATER,
                'food': DesertConfig.INITIAL_FOOD,
                'money': DesertConfig.INITIAL_MONEY,
                'done': False,
                'mbti': self.agent_mbtis[i],
                'arrived_at_end': False,
                'end_water': 0,
                'end_food': 0,
                'returned_money': 0,
                'settled': False
            })
        self.step_count = 0
        self.done = False
        self._update_weather()
        return self._get_obs_all()

    def _update_weather(self):
        if self.step_count < len(self.weather_sequence):
            self.current_weather = self.weather_sequence[self.step_count]
        else:
            self.current_weather = self.rng.choice(DesertConfig.WEATHER_TYPES)
        return self.current_weather

    def _get_obs_all(self):
        obs_list = []
        for agent in self.agents:
            obs = {
                'node': agent['node'],
                'water': agent['water'],
                'food': agent['food'],
                'money': agent['money'],
                'type': self.map[agent['node']]['type'],
                'mbti': agent['mbti'],
                'neighbors': self.map[agent['node']]['neighbors'],
                'weather': self._weather_cn[self.current_weather],  # 中文天气
                'weather_en': self.current_weather                 # 保留英文给内部用
            }
            obs_list.append(obs)
        return obs_list

    def step(self, actions):
        if self.done:
            raise RuntimeError("Episode已结束")

        self._update_weather()
        weather = self.current_weather  # 英文
        base_water = DesertConfig.WATER_CONSUME[weather]
        base_food = DesertConfig.FOOD_CONSUME[weather]

        rewards = [0] * self.n_agents

        for i, agent in enumerate(self.agents):
            if agent['done']:
                continue
            act_dict = actions[i]
            if act_dict is None:
                continue
            action = act_dict['action']
            params = act_dict.get('params')

            node = agent['node']
            node_type = self.map[node]['type']
            row, col = divmod(node - 1, DesertConfig.MAP_SIZE)

            # 沙暴强制停留（按你的设定，只禁移动，可保留）
            if weather == 'sandstorm' and action in [self.UP, self.DOWN, self.LEFT, self.RIGHT]:
                action = self.STAY

            water_spent = base_water * DesertConfig.ACTION_CONSUME_MULT['stay']
            food_spent = base_food * DesertConfig.ACTION_CONSUME_MULT['stay']

            if action in [self.UP, self.DOWN, self.LEFT, self.RIGHT]:
                water_spent = base_water * DesertConfig.ACTION_CONSUME_MULT['move']
                food_spent = base_food * DesertConfig.ACTION_CONSUME_MULT['move']
                dr, dc = 0, 0
                if action == self.UP: dr = -1
                elif action == self.DOWN: dr = 1
                elif action == self.LEFT: dc = -1
                elif action == self.RIGHT: dc = 1
                new_row, new_col = row + dr, col + dc
                if 0 <= new_row < DesertConfig.MAP_SIZE and 0 <= new_col < DesertConfig.MAP_SIZE:
                    target_node = new_row * DesertConfig.MAP_SIZE + new_col + 1
                else:
                    target_node = None

                if target_node is not None and target_node in self.map[node]['neighbors']:
                    agent['node'] = target_node
                    if self.map[target_node]['type'] == 'end':
                        agent['arrived_at_end'] = True
                        agent['done'] = True
            elif action == self.STAY:
                pass  # 消耗已在上面默认计算为 1 倍
            elif action == self.MINE:
                water_spent = base_water * DesertConfig.ACTION_CONSUME_MULT['mine']
                food_spent = base_food * DesertConfig.ACTION_CONSUME_MULT['mine']
                if node_type == 'mine':
                    agent['money'] += DesertConfig.BASE_MINING_INCOME
                else:
                    rewards[i] -= 10
            elif action == self.BUY:
                if node_type == 'village' and params and isinstance(params, dict):
                    buy_w = int(params.get('buy_water', 0))
                    buy_f = int(params.get('buy_food', 0))
                    buy_w = max(0, min(buy_w, DesertConfig.MAX_WATER - agent['water']))
                    buy_f = max(0, min(buy_f, DesertConfig.MAX_FOOD - agent['food']))
                    cost = (buy_w * DesertConfig.WATER_PRICE + buy_f * DesertConfig.FOOD_PRICE) * DesertConfig.VILLAGE_PRICE_MULT
                    if agent['money'] >= cost:
                        agent['money'] -= cost
                        agent['water'] += buy_w
                        agent['food'] += buy_f
                    else:
                        # 能买多少买多少
                        unit_w = DesertConfig.WATER_PRICE * DesertConfig.VILLAGE_PRICE_MULT
                        unit_f = DesertConfig.FOOD_PRICE * DesertConfig.VILLAGE_PRICE_MULT
                        can_w = min(buy_w, int(agent['money'] // unit_w))
                        spent_w = can_w * unit_w
                        rem = agent['money'] - spent_w
                        can_f = min(buy_f, int(rem // unit_f))
                        agent['water'] += can_w
                        agent['food'] += can_f
                        agent['money'] -= (can_w * unit_w + can_f * unit_f)
                else:
                    # 非法购买，改为停留
                    print(f"[警告] Agent{i} 在非村庄节点尝试购买，动作改为停留")
                    action = self.STAY  # 已经赋过初始停留消耗，不再改变
            else:
                pass

            agent['water'] -= water_spent
            agent['food'] -= food_spent
            if agent['water'] < 0: agent['water'] = 0
            if agent['food'] < 0: agent['food'] = 0
            if agent['water'] == 0 or agent['food'] == 0:
                agent['done'] = True

        # 终点结算
        for a in self.agents:
            if a['arrived_at_end'] and not a.get('settled', False):
                a['end_water'] = a['water']
                a['end_food'] = a['food']
                returned = (a['water'] * DesertConfig.WATER_PRICE + a['food'] * DesertConfig.FOOD_PRICE) * DesertConfig.END_RETURN_MULT
                a['money'] += returned
                a['returned_money'] = returned
                a['water'] = 0
                a['food'] = 0
                a['settled'] = True

        self.step_count += 1
        if all(a['done'] for a in self.agents) or self.step_count >= self.max_steps:
            self.done = True

        return self._get_obs_all(), rewards, [a['done'] for a in self.agents], {'step': self.step_count, 'weather': weather}