import abc

from core.library.BehaviorTreeBase import BehaviorTree


class AgentBase(metaclass=abc.ABCMeta):
    """
    Agent基类，所有角色均需继承此类 \n
    此类包含：角色的属性、角色的行为、角色的规划、角色的执行、角色的记忆、角色的互联，也就是说感知、规划和行动三大步骤
    """
    def __init__(self):
        self.attr = []
        self.__bt = None

    def set_attrs(self, attr: list):
        """
        设置Agent的属性 \n
        属性的定义：与其记忆相连接，表面了它有哪些内在和外在的属性。内在属性即为私有变量不对外透露，外在属性是共有变量，所有Agent均可访问。
        :param attr: 属性
        """
        self.attr = attr

    def set_bt(self, bt: BehaviorTree):
        """
        设置Agent的行为，即行为树 \n
        行为的定义：每一个Agent均有不同的行为，在此是行为树的体现，他决定了Agent哪些能做哪些不能做，是决策的象征。
        :param bt: 行为树
        """
        self.__bt = bt

    @abc.abstractmethod
    def start_agent_main_loop(self):
        """
        Agent的主循环，每个Agent本质都是一个线程，是无限循环的个体。
        """
        pass

