import os
import json
from datetime import datetime
from core.memory import MemoryHandler
from environments.desert.config import DesertConfig


class ExperimentRunner:
    def __init__(self, env, agents, environment_name="desert", use_rag=True):
        self.env = env
        self.agents = agents
        self.environment_name = environment_name
        self.use_rag = use_rag
        self.experiment_id = f"{environment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.map_desc = self._build_map_desc()

        if use_rag:
            self.memory = MemoryHandler(environment_name=environment_name,
                                        experiment_id=self.experiment_id)
        else:
            self.memory = None

        os.makedirs("logs", exist_ok=True)
        self.json_log = f"logs/experiment_{self.experiment_id}.json"
        self.thinking_log = f"logs/thinking_{self.experiment_id}.log"

    def _build_map_desc(self):
        size = DesertConfig.MAP_SIZE
        start = DesertConfig.START
        end = DesertConfig.END
        village = DesertConfig.VILLAGE
        mine = DesertConfig.MINE

        desc = (
            f"地图为 {size}x{size} 网格，节点按行从左到右、从上到下编号 1（左上）到 {size*size}（右下）。\n"
            f"起点：节点 {start}（左上）；终点：节点 {end}（右下）。\n"
            f"村庄位于节点 {village}（可购买补给）；矿山位于节点 {mine}（可挖矿）。\n"
            f"其他节点为普通沙漠。\n"
            f"相邻节点移动规则：上(0)、下(1)、左(2)、右(3)，边界外不可移动。\n"
            f"当前实验 ID: {self.experiment_id}"
        )
        return desc

    def _log_thought(self, step, agent_id, mbti, thought):
        with open(self.thinking_log, "a", encoding="utf-8") as f:
            f.write(f"Step {step}, Agent {agent_id} ({mbti}):\n{thought}\n{'='*60}\n")

    def run(self, max_steps=30):
        obs_all = self.env.reset()
        step = 0

        experiment_data = {
            "experiment_id": self.experiment_id,
            "environment": self.environment_name,
            "agents": [{"id": i, "mbti": agent.mbti_type} for i, agent in enumerate(self.agents)],
            "rounds": []
        }

        # 改用 self.env.done 控制循环，避免环境结束后再调用 step
        while step < max_steps and not self.env.done:
            actions = []
            thoughts = []
            for i, agent in enumerate(self.agents):
                obs = obs_all[i].copy()
                obs['map_desc'] = self.map_desc

                mem_context = ""
                if self.memory:
                    mem_context = self.memory.retrieve(
                        state_desc=str(obs), agent_id=i
                    )

                action, thought, params = agent.act(obs, agent_id=i, memory_context=mem_context)
                actions.append({'action': action, 'params': params})
                thoughts.append(thought)

                self._log_thought(step, i, agent.mbti_type, thought)
                print(f"Step{step} Agent{i}({agent.mbti_type}) 节点{obs['node']} -> 动作{action}")

            next_obs_all, rewards, dones, info = self.env.step(actions)

            if self.memory:
                for i, agent in enumerate(self.agents):
                    experience = (
                        f"动作 {actions[i]['action']}, 奖励 {rewards[i]}, "
                        f"剩余水 {next_obs_all[i]['water']:.1f}, "
                        f"食物 {next_obs_all[i]['food']:.1f}, 资金 {next_obs_all[i]['money']:.1f}"
                    )
                    self.memory.store(
                        experience_context=experience,
                        agent_id=i,
                        round_num=step,
                        metadata={"action": actions[i], "reward": rewards[i]}
                    )

            experiment_data["rounds"].append({
                "step": step,
                "actions": actions,
                "rewards": rewards,
                "obs": [{k: v for k, v in obs.items() if k != 'map_desc'} for obs in obs_all]
            })

            obs_all = next_obs_all
            step += 1

        # 保存实验日志
        with open(self.json_log, "w", encoding="utf-8") as f:
            json.dump(experiment_data, f, indent=2, ensure_ascii=False)

        print(f"\n实验结束，日志保存至 {self.json_log} 和 {self.thinking_log}")
        return experiment_data