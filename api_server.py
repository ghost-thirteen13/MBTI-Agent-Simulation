import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from core.agent import MBTIAgent   # 注意根据你的实际路径调整

app = Flask(__name__)
CORS(app)   # 允许前端跨域调用

# 加载 MBTI 人格配置（与 main.py 中方式一致）
def load_profiles():
    with open('config/mbti_profiles.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# 全局配置：API Key 建议从环境变量读取，避免硬编码
API_KEY = os.environ.get("DEEPSEEK_API_KEY")
PROFILES = load_profiles()

# 预先创建两个 Agent 实例（也可以每次请求动态创建，但复用即可）
# 注意：这里的人格类型是固定的 INTJ 和 ENTJ，如果你希望前端动态选择对手/自己人格，
# 需要根据请求参数来创建 Agent。为了简单，我们先固定两个。
INTJ_AGENT = MBTIAgent("INTJ", PROFILES["INTJ"], API_KEY)
ENTJ_AGENT = MBTIAgent("ENTJ", PROFILES["ENTJ"], API_KEY)

@app.route("/decide", methods=["POST"])
def decide():
    """
    请求体 JSON 格式：
    {
        "agent_type": "INTJ" | "ENTJ",     # 决定由哪个 agent 做决策
        "opponent_mbti": "ENTJ" | "INTJ",  # 对手的人格类型
        "history": [...]                   # 历史对局列表，格式与 engine.history 一致
    }
    返回：
    {
        "action": "C" or "D",
        "thought": "模型的原始思考文本"
    }
    """
    data = request.get_json()
    agent_type = data.get("agent_type", "INTJ")
    opponent_mbti = data.get("opponent_mbti", "ENTJ")
    history = data.get("history", [])

    # 选择对应的 agent
    if agent_type == "INTJ":
        agent = INTJ_AGENT
    elif agent_type == "ENTJ":
        agent = ENTJ_AGENT
    else:
        return jsonify({"error": "Invalid agent_type"}), 400

    # 调用 agent 的 decide 方法
    action, thought = agent.decide(opponent_mbti, history)
    return jsonify({"action": action, "thought": thought})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)