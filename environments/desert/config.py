# 环境参数（天气序列，消耗倍率等）
# environments/desert/config.py
# environments/desert/config.py
import random

class DesertConfig:
    MAP_SIZE = 5
    START = 1
    END = 25
    VILLAGE = 14
    MINE = 18

    # 初始资源
    INITIAL_WATER = 100       # 箱
    INITIAL_FOOD = 100
    INITIAL_MONEY = 10000

    # 资源上限
    MAX_WATER = 200
    MAX_FOOD = 200

    # 基础价格
    WATER_PRICE = 5
    FOOD_PRICE = 10
    VILLAGE_PRICE_MULT = 2   # 村庄购买乘数

    # 收入与返还
    BASE_MINING_INCOME = 1000
    END_RETURN_MULT = 0.5

    # 天气与消耗（英文键，内部使用）
    WEATHER_TYPES = ["sunny", "hot", "sandstorm"]
    # 基础消耗（箱/天）
    WATER_CONSUME = {"sunny": 3, "hot": 9, "sandstorm": 10}
    FOOD_CONSUME  = {"sunny": 4, "hot": 9, "sandstorm": 10}

    # 行动消耗倍数
    ACTION_CONSUME_MULT = {
        "stay": 1.0,
        "move": 2.0,
        "mine": 3.0
    }

    # 天气生成概率
    WEATHER_PROBS = [0.3, 0.6, 0.1]  # sunny, hot, sandstorm

    @staticmethod
    def generate_weather_sequence(length=30):
        return random.choices(DesertConfig.WEATHER_TYPES,
                              weights=DesertConfig.WEATHER_PROBS, k=length)

    # 多人协同倍数（暂保留，后续可用）
    @staticmethod
    def coop_move_consume_mult(n): return 1 + 0.5 * (n-1)
    @staticmethod
    def coop_mine_consume_mult(n): return 1 + 0.5 * (n-1)
    @staticmethod
    def coop_mine_income_mult(n): return 1.0 / n
    @staticmethod
    def coop_buy_price_mult(n): return 1 + 0.5 * (n-1)