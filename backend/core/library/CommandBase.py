import abc


class CommandBase(metaclass=abc.ABCMeta):
    """
    指令基类，基本通信指令格式： \n
    将被解码到如下格式： \n
    {
        type: 0, # 指令格式标记，0为指令助记符，1为指令映射表 \n
        command: 'close_lidar', # 指令 \n
        args: [] # 指令参数 \n
        priority: -1 # 指令执行优先级，数值越高代表越先执行，-1默认为auto \n
    }
    """
    def __init__(self):
        self.command_pack = None
        self.__result = None

    @abc.abstractmethod
    def execute(self, command_pack, entity):
        """
        指令执行
        """
        pass

    @abc.abstractmethod
    def get_result(self):
        """
        用于获取指令执行结果
        """
        return self.__result

    @abc.abstractmethod
    def get_name(self):
        """
        获取指令唯一键值
        """
        pass
