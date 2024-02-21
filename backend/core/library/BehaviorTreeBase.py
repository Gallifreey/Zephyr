import abc
import enum
import threading
import re
import json
from graphviz import Digraph
from collections import Counter

from core.library.BlackBoard import BlackBoard
from core.library.Utils import Singleton
from core.utils.logger import Logger
from core.utils.utils import FORMAT_LEFT_BRACE, FORMAT_RIGHT_BRACE, FORMAT_ENTER, COLOR_PICKER


# TODO 尝试使用有限状态机与行为树相结合是个选择
# TODO 启发式搜索行为树获得最优路径(代价最小)
# TODO 长期目标：维护和优化行为树

class BehaviorTreeNodeState(enum.Enum):
    READY = 1,
    RUNNING = 2,
    SUCCESS = 3,
    FAILED = 4


class BehaviorTreeNodeType(enum.Enum):
    # 组合控制节点
    SEQUENCE = 1,  # 从左到右依次执行其子分支，当第一次遇到当第一次遇到子分支返回失败时，则停止继续执行其他分支，此时Sequence返回失败，如果所有分支都返回成功，此时Sequence返回成功，其他同上。
    SELECTOR = 2,  # 按照顺序执行子节点，当某个子节点返回success时，停止执行并返回success
    MULTI_PARALLEL = 3,  # 处理并发行为
    # 服务节点
    SERVICE = 4,  # 服务节点的主要作用就是在后台更新数据（比如修改黑板变量以供装饰器用），但并不会返回结果，也不能直接影响行为树的执行流程，通常它可以配合装饰器节点来实现复杂的功能。
    # 装饰节点
    INVERTER = 5,  # 它可以将子节点的结果倒转，比如子节点返回了failure，则这个修饰节点会向上返回success
    REPEATER = 6,  # 重复执行其子节点指定的次数或者一直重复执行，直到其子节点返success或者failure
    # 叶节点
    CONDITION = 7,  # 判断条件是否满足，如果满足则返回success，否则返回failure
    ACTION = 8,  # 执行某个具体的动作或行为


class BehaviorTreeNode(metaclass=abc.ABCMeta):
    """
    当你的节点是叶节点时(Condition、Action)，你需要保证你的类名是符合驼峰命名规则且以'ActionNode'或'ConditionNode'结尾，
    并且若你的属性是可读可写(指可通过读取配置文件进行类中属性的读写)的，则你需要编写get和set方法，具体举例在下方。 \n
    且你的可读可写属性应是私有的，如__speed，变量前加'__'。下面是个例子： \n
    你的属性名：__开始为私有 \n
    你的get/set方法：需要以get_你的属性名命名，同理set亦然。

    >>> @BTActionNodeAnnotation                 \
        class SwimActionNode(BehaviorTreeNode): \
        def __init__(self):                     \
            super().__init__()                  \
            self.__speed = 10.0                 \
        def get_speed(self):                    \
            return self.__speed                 \
        def set_speed(self, speed):             \
            self.__speed = speed                \
        def execute(self, from_to):             \
            pass                                \
    """
    logger = Logger

    def __init__(self):
        self.state = BehaviorTreeNodeState.READY

    @abc.abstractmethod
    def execute(self, from_to):
        """
        执行行为 \n
        :param from_to: 来自对象
        """
        pass

    @abc.abstractmethod
    def should_execute(self):
        """
        是否执行。
        """
        return True

    def get_attr_list(self):
        """
        获得该节点的所有在册属性
        """
        dirs = self.__dir__()
        dir_list = []
        values = []
        for _dir in dirs:
            if _dir.startswith('get_') or _dir.startswith('set_'):
                dir_list.append(_dir[4:])
        for k, v in Counter(dir_list).items():
            if v > 1:
                values.append(k)
        for k, v in self.__dict__.items():
            split_list = k.split('__')
            if len(split_list) == 2:
                key = split_list[1]
                if key in values:
                    Logger.info(f'Attr {key}: {v}')


class BTSequenceNode(BehaviorTreeNode):

    def __init__(self, children=None):
        super().__init__()
        if children is None:
            children = []
        self.children = children  # 子节点列表

    def __call__(self, children):
        self.children = children

    def add_child_node(self, node):
        self.children.append(node)

    def should_execute(self):
        return True

    def execute(self, from_to):
        self.state = BehaviorTreeNodeState.RUNNING
        for node in self.children:
            node.execute(from_to)
            if node.state == BehaviorTreeNodeState.FAILED:
                self.state = BehaviorTreeNodeState.FAILED
                return
        self.state = BehaviorTreeNodeState.SUCCESS


class BTSelectorNode(BehaviorTreeNode):

    def __init__(self, children=None):
        super().__init__()
        if children is None:
            children = []
        self.children = children  # 子节点列表

    def __call__(self, children):
        self.children = children

    def add_child_node(self, node):
        self.children.append(node)

    def should_execute(self):
        return True

    def execute(self, from_to):
        self.state = BehaviorTreeNodeState.RUNNING
        for node in self.children:
            node.execute(from_to)
            if node.state == BehaviorTreeNodeState.SUCCESS:
                self.state = BehaviorTreeNodeState.SUCCESS
                return
        self.state = BehaviorTreeNodeState.FAILED


class BTMultiParallelNode(BehaviorTreeNode):

    def __init__(self, children=None):
        super().__init__()
        if children is None:
            children = []
        self.children = children  # 子节点列表

    def __call__(self, children):
        self.children = children

    def add_child_node(self, node):
        self.children.append(node)

    def should_execute(self):
        return True

    def execute(self, from_to):
        self.state = BehaviorTreeNodeState.RUNNING
        for node in self.children:
            thread = threading.Thread(target=node.execute, args=(from_to,), daemon=True)
            thread.start()
        while True:
            flag = True
            for node in self.children:
                if node.state == BehaviorTreeNodeState.FAILED:
                    self.state = BehaviorTreeNodeState.FAILED
                    return
                elif node.state != BehaviorTreeNodeState.SUCCESS:
                    flag = False
                    break
            if flag:
                self.state = BehaviorTreeNodeState.SUCCESS
                return


class BTServiceNode(BehaviorTreeNode):

    def __init__(self):
        super().__init__()

    def should_execute(self):
        return True

    def execute(self, from_to):
        self.state = BehaviorTreeNodeState.RUNNING
        pass


class BTInverterNode(BehaviorTreeNode):

    def __init__(self, child=None):
        super().__init__()
        self.child = child

    def __call__(self, child):
        self.child = child

    def should_execute(self):
        return True

    def execute(self, from_to):
        self.state = BehaviorTreeNodeState.RUNNING
        state = self.child.execute(from_to)
        if state == BehaviorTreeNodeState.FAILED:
            self.state = BehaviorTreeNodeState.SUCCESS
        elif state == BehaviorTreeNodeState.SUCCESS:
            self.state = BehaviorTreeNodeState.FAILED


class BTRepeaterNode(BehaviorTreeNode):

    def __init__(self, child=None, repeat_times=-1):
        super().__init__()
        self.child = child
        self.repeat_times = repeat_times

    def __call__(self, child):
        self.child = child

    def should_execute(self):
        return True

    def execute(self, from_to):
        self.state = BehaviorTreeNodeState.RUNNING
        is_infinite = False
        if self.repeat_times == -1:
            is_infinite = True
        if is_infinite:
            while True:
                self.child.execute(from_to)
                if self.child.state == BehaviorTreeNodeState.SUCCESS:
                    self.state = BehaviorTreeNodeState.SUCCESS
                elif self.child.state == BehaviorTreeNodeState.FAILED:
                    self.state = BehaviorTreeNodeState.FAILED
        else:
            for _ in range(self.repeat_times):
                self.child.execute(from_to)
                if self.child.state == BehaviorTreeNodeState.SUCCESS:
                    self.state = BehaviorTreeNodeState.SUCCESS
                elif self.child.state == BehaviorTreeNodeState.FAILED:
                    self.state = BehaviorTreeNodeState.FAILED


class BTConditionNode(BehaviorTreeNode):

    def __init__(self):
        super().__init__()

    def should_execute(self):
        return True

    def execute(self, from_to):
        self.state = BehaviorTreeNodeState.RUNNING
        pass


class BTActionNode(BehaviorTreeNode):

    def __init__(self, action=None):
        super().__init__()
        self.action = action

    def should_execute(self):
        return True

    def execute(self, from_to):
        self.state = BehaviorTreeNodeState.RUNNING
        pass


class BTActionNodeAnnotation:
    __actions = []

    def __init__(self, action=None):
        super().__init__()
        self.action = action
        subclass = action.__name__
        if not self.__check_is_camel_with_node(subclass):
            raise ValueError("Your Node Need Write in Camel And With 'ActionNode' String End.")
        if self.__check_dup(subclass):
            raise ValueError('Your Node Is Duplicate.')
        self.__actions.append({
            'class': action,
            'name': subclass
        })

    @staticmethod
    def __get_class_name_from_str(_str):
        _, a = _str.split('.')
        b, _ = a.split('\'')
        return b

    @staticmethod
    def __check_is_camel_with_node(_str):
        pattern = r'^[a-zA-Z]+([A-Z][a-z]+)+$'
        return (_str.endswith('ActionNode') or _str.endswith('ConditionNode')) and bool(re.match(pattern, _str)) and _str[
            0].isupper()

    def __check_dup(self, action):
        for ac in self.__actions:
            if ac['name'] == action:
                return True
        return False

    @classmethod
    def get_action_from_name(cls, name):
        obj = None
        for cl in cls.__actions:
            if cl['name'] == name:
                obj = cl['class']
                break
        return obj

    def __call__(self, *args, **kwargs):
        return self.action(*args, **kwargs)


class BehaviorTree(object):
    def __init__(self):
        self.tree = None

    def build_bt_from_config_file(self, config):
        with open(config, 'r') as cg:
            data = json.load(cg)['start']
            self.tree = self.__build_node(data)
            cg.close()

    def __build_node(self, node):
        _type = node['type']
        if _type == "SEQUENCE":
            return self.__build_sequence_node(node)
        elif _type == 'SELECTOR':
            return self.__build_selector_node(node)
        elif _type == 'MULTI_PARALLEL':
            return self.__build_multi_parallel_node(node)
        elif _type == 'SERVICE':
            return self.__build_service_node(node)
        elif _type == 'INVERTER':
            return self.__build_inverter_node(node)
        elif _type == 'REPEATER':
            return self.__build_repeater_node(node)
        elif _type == 'CONDITION':
            return self.__build_condition_node(node)
        elif _type == 'ACTION':
            return self.__build_action_node(node)

    def __build_sequence_node(self, node):
        seq_node = BTSequenceNode()
        for child in node['children']:
            seq_node.add_child_node(self.__build_node(child))
        return seq_node

    def __build_selector_node(self, node):
        selector_node = BTSelectorNode()
        for child in node['children']:
            selector_node.add_child_node(self.__build_node(child))
        return selector_node

    def __build_multi_parallel_node(self, node):
        mp_node = BTMultiParallelNode()
        for child in node['children']:
            mp_node.add_child_node(self.__build_node(child))
        return mp_node

    def __build_service_node(self, node):
        pass

    def __build_inverter_node(self, node):
        inverter_node = BTInverterNode(self.__build_node(node['child']))
        return inverter_node

    def __build_repeater_node(self, node):
        repeater_node = BTRepeaterNode(self.__build_node(node['child']), node['repeat_times'])
        return repeater_node

    def __build_condition_node(self, node):
        pass

    def __build_action_node(self, node):
        action_node = BTActionNodeAnnotation.get_action_from_name(node['action'])()
        if action_node is None:
            raise RuntimeError('It seems that you only run the node files before the annotation works.')
        for k, v in node['params'].items():
            getattr(action_node, f'set_{k}')(v)
        return action_node

    def start(self, from_to):
        thread = threading.Thread(target=self.tree.execute, args=(from_to,), daemon=False)
        thread.start()


class BehaviourTreeGraph(Singleton):
    """
    行为树可视化
    """
    __graph = Digraph(node_attr={'shape': 'Mrecord'})

    def __init__(self):
        super().__init__()

    @classmethod
    def build(cls, config, draw_blackboard=True):
        with open(config, 'r') as cg:
            data = json.load(cg)['start']
            cls.__gen_node(cls(), data, 'root_0')
            cg.close()
        if draw_blackboard:
            BlackBoard.draw(cls.__graph)
        from core.library.EasyImportBase import ROOT
        cls.__graph.render(ROOT('round-table.gv'), view=True)

    @staticmethod
    def __gen_node_str(node):
        if 'params' in node.keys() and 'action' in node.keys():
            _str = ''
            for k, v in node['params'].items():
                _str += f'{k}: {v}\\n'
            return f"{FORMAT_LEFT_BRACE}{node['type']}|{node['action']}|{_str}{FORMAT_RIGHT_BRACE}"
        else:
            return f"{FORMAT_LEFT_BRACE}{node['type']}{FORMAT_RIGHT_BRACE}"

    def __gen_node(self, node, parent_name):
        _type = node['type']
        if _type == 'SEQUENCE':
            return self.__gen_sequence_node(node, parent_name)
        elif _type == 'MULTI_PARALLEL':
            return self.__gen_multi_parallel_node(node, parent_name)
        elif _type == 'INVERTER':
            return self.__gen_inverter_node(node, parent_name)
        elif _type == 'REPEATER':
            return self.__gen_repeater_node(node, parent_name)
        elif _type == 'SELECTOR':
            return self.__gen_selector_node(node, parent_name)
        elif _type == 'ACTION':
            return self.__gen_action_node(node, parent_name)
        elif _type == 'CONDITION':
            return self.__gen_condition_node(node, parent_name)

    def __gen_sequence_node(self, node, parent_name):
        spl = parent_name.split('_')
        prefix = '_'.join(spl)
        index = 0
        self.__graph.node(parent_name, self.__gen_node_str(node), fillcolor=COLOR_PICKER[0], style='filled')
        for _node in node['children']:
            index = index + 1
            self.__gen_node(_node, f'{prefix}_{str(index)}')
            self.__graph.edge(parent_name, f'{prefix}_{str(index)}')

    def __gen_multi_parallel_node(self, node, parent_name):
        spl = parent_name.split('_')
        prefix = '_'.join(spl)
        index = 0
        self.__graph.node(parent_name, self.__gen_node_str(node), fillcolor=COLOR_PICKER[1], style='filled')
        for _node in node['children']:
            index = index + 1
            self.__gen_node(_node, f'{prefix}_{str(index)}')
            self.__graph.edge(parent_name, f'{prefix}_{str(index)}')

    def __gen_inverter_node(self, node, parent_name):
        spl = parent_name.split('_')
        prefix = '_'.join(spl)
        index = 0
        self.__graph.node(parent_name, self.__gen_node_str(node), fillcolor=COLOR_PICKER[2], style='filled')
        self.__gen_node(node['child'], f'{prefix}_{str(index)}')
        self.__graph.edge(parent_name, f'{prefix}_{str(index)}')

    def __gen_repeater_node(self, node, parent_name):
        spl = parent_name.split('_')
        prefix = '_'.join(spl)
        index = 0
        self.__graph.node(parent_name, self.__gen_node_str(node), fillcolor=COLOR_PICKER[3], style='filled')
        self.__gen_node(node['child'], f'{prefix}_{str(index)}')
        self.__graph.edge(parent_name, f'{prefix}_{str(index)}', label=f"Repeat times:{node['repeat_times']}")

    def __gen_selector_node(self, node, parent_name):
        spl = parent_name.split('_')
        prefix = '_'.join(spl)
        index = 0
        self.__graph.node(parent_name, self.__gen_node_str(node), fillcolor=COLOR_PICKER[4], style='filled')
        for _node in node['children']:
            index = index + 1
            self.__gen_node(_node, f'{prefix}_{str(index)}')
            self.__graph.edge(parent_name, f'{prefix}_{str(index)}')

    def __gen_action_node(self, node, parent_name):
        self.__graph.node(parent_name, self.__gen_node_str(node), fillcolor=COLOR_PICKER[5], style='filled')

    def __gen_condition_node(self, node, parent_name):
        spl = parent_name.split('_')
        prefix = '_'.join(spl)
        self.__graph.node(parent_name, self.__gen_node_str(node), fillcolor=COLOR_PICKER[6], style='filled')
        self.__gen_node(node['true'], f'{prefix}_1')
        self.__graph.edge(parent_name, f'{prefix}_1', label='TRUE')
        self.__gen_node(node['false'], f'{prefix}_2')
        self.__graph.edge(parent_name, f'{prefix}_2', label='FALSE')


class FSM2BTBridge(object):
    """
    有限状态机与行为树传输桥
    """

    def __init__(self):
        pass

# BehaviourTreeGraph().build(r'F:\Python\Zephyr\backend\resource\behavior_tree_config\config.json')
