# environments/desert/map_loader.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from environments.desert.config import DesertConfig

class MapLoader:
    @staticmethod
    def generate_desert_map():
        """
        生成 5x5 沙漠地图。
        节点编号 1~25（1为左上，25为右下）。
        特殊点从 DesertConfig 读取。
        """
        size = DesertConfig.MAP_SIZE
        start = DesertConfig.START
        end = DesertConfig.END
        village = DesertConfig.VILLAGE
        mine = DesertConfig.MINE

        total_nodes = size * size
        map_data = {}
        for node_id in range(1, total_nodes + 1):
            row = (node_id - 1) // size
            col = (node_id - 1) % size

            # 确定类型
            if node_id == start:
                ntype = 'start'
            elif node_id == end:
                ntype = 'end'
            elif node_id == mine:
                ntype = 'mine'
            elif node_id == village:
                ntype = 'village'
            else:
                ntype = 'desert'

            # 合法邻居（上下左右）
            neighbors = []
            if row > 0:         neighbors.append(node_id - size)  # 上
            if row < size - 1:  neighbors.append(node_id + size)  # 下
            if col > 0:         neighbors.append(node_id - 1)     # 左
            if col < size - 1:  neighbors.append(node_id + 1)     # 右

            map_data[node_id] = {
                'type': ntype,
                'neighbors': neighbors
            }
        return map_data



# 测试（可忽略）
# if __name__ == '__main__':
#     data = MapLoader.load_map()
#     for nid, info in data.items():
#         print(f"Node {nid:2d}: {info['type']:8s} row={info['row']} col={info['col']} neighbors={info['neighbors']}")
