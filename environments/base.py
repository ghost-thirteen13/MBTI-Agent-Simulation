# environments/base.py
# 博弈环境基类


class BaseEnvironment:
    """所有博弈环境（囚徒困境、沙漠困境）的基类，负责通用 config 的存取。"""

    def __init__(self, config: dict = None):
        self.config = config or {}
