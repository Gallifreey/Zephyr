from core.library.Utils import Singleton

"""
对于每个实体都会分配一个对应角色的agent，每个agent通过感知、推理、决策更新。
agent分为：自主agent(我方/敌方outpost、我方/敌方base)、半自主agent(我方哨兵)、人工agent(我方/敌方其他)
每个agent具有相应的行为树，从父节点自顶而下检索行为树节点，执行行为。
"""


class TacticalDecision(Singleton):
    """
    决策类，用于自动决策，全局热力图生成，依存图修正，下发命令
    """

    def __init__(self):
        super().__init__()

    def start(self):
        """
        启动决策
        """
        pass
