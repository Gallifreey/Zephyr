import enum
import threading

from core.library.Utils import Singleton


class BlackBoardDataType(enum.Enum):
    """
    枚举类：黑板数据类型
    """
    INTEGER = 1,
    FLOAT = 2,
    STRING = 3,
    BOOLEAN = 4,
    LIST = 5,
    TUPLE = 6,
    SET = 7,
    DICT = 8,
    OBJECT = 9


class BlackBoard(Singleton):
    """
    黑板类，存储可以被多个结点访问的共享信息，一块可以被结点读写的公共存储区。
    """
    __data_pool = []  # 数据缓存池
    '''
    数据池：每一个即为单元节点：
    {
        'key': 键值,
        'data': 数据,
        'type': BlackBoardDataType.INTEGER
    }
    '''

    def __init__(self):
        super().__init__()

    @classmethod
    def set_data(cls, key, data, data_type: BlackBoardDataType):
        for dic in cls.__data_pool:
            if dic['key'] == key:
                raise RuntimeError('Your key is duplicate.')
        cls.__data_pool.append({
            'data': data,
            'key': key,
            'type': data_type
        })

    @classmethod
    def get_data(cls, key):
        for dic in cls.__data_pool:
            if dic['key'] == key:
                return dic['data']
        return None

    @classmethod
    def update_data(cls, key, data):
        mutex = threading.Lock()
        with mutex:
            for dic in cls.__data_pool:
                if dic['key'] == key:
                    dic['data'] = data
                    return

    @classmethod
    def draw(cls, graph):
        """
        向图中绘制数据缓存区的数据结构 \n
        :param graph: 目标图
        """
        # graph.node('blackboard', 'BlackBoard', shape='record')

