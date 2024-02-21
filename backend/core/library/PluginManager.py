from core.library.Enums import EventBusItemType
from core.library.Utils import Singleton
from core.utils.logger import Logger


class PluginManager(Singleton):
    """
    插件管理器，用来创建、管理、监控插件。
    """
    __plugins = []

    def __init__(self):
        super().__init__()

    @classmethod
    def load_plugins(cls, plugin):
        """
        加载插件 \n
        :param plugin: 插件
        """
        if isinstance(plugin, list):
            for p in plugin:
                cls.__plugins.append(p)
        else:
            cls.__plugins.append(plugin)

    @classmethod
    def run_plugins(cls):
        """
        运行插件
        """
        Logger.info(f'Found Plugins {[plugin.plugin_name for plugin in cls.__plugins]}.')
        for plugin in cls.__plugins:

                plugin.start()

        Logger.info(f'All Plugins are active.')

    @classmethod
    def uninstall_plugins(cls, plugin_name=None):
        """
        卸载插件，可根据提供的插件名称进行卸载 \n
        :param plugin_name: 插件名称，默认为空
        """
        if plugin_name:
            for plugin in cls.__plugins:
                if plugin.plugin_name == plugin_name:
                    plugin.uninstall()
        else:
            for plugin in cls.__plugins:
                plugin.uninstall()

    @staticmethod
    def register(target_plugin, item, key, data: EventBusItemType):
        target_plugin.register(item, key, data)

    def monitor(self):
        """
        插件监控器，监控插件使用的资源。
        """
        pass
