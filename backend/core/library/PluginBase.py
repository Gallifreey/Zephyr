import abc

from core.library.EventBusBase import EventBus


# TODO 修改插件注册方式和插件结构

class PluginBase(metaclass=abc.ABCMeta):
    plugin_name = ''
    priority = -1  # 插件运行优先级，-1为自动设置。优先级越高代表插件在每次循环中运行占用资源越多，反之则少。

    def __init__(self):
        super(self).__init__()

    @classmethod
    @abc.abstractmethod
    def start(cls):
        """
        插件入口函数
        """
        pass

    @classmethod
    @abc.abstractmethod
    def uninstall(cls):
        """
        插件卸载事件
        """
        pass

    @classmethod
    def register(cls, value, key, item_type):
        """
        插件向总线注册值,value为缺省值
        """
        EventBus.register(value, key, item_type)

    @classmethod
    def update(cls, key, data):
        """
        插件向总线更新值
        """
        EventBus.put(key, data)

    @classmethod
    def get(cls, key):
        """
        插件向总线获取值
        """
        return EventBus.get(key)
