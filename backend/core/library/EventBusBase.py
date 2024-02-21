import abc
import json

from core.library.CommandManager import CommandManager
from core.library.Enums import EventBusItemType
from core.library.PluginManager import PluginManager
from core.library.Utils import ThreadSafeSingleton
from core.utils.logger import Logger


class EventBase(metaclass=abc.ABCMeta):
    event: list

    def __init__(self):
        super().__init__()

    @abc.abstractmethod
    def subscribe(self, event):
        """
        事件订阅
        """
        pass

    @abc.abstractmethod
    def publish(self, event):
        """
        事件发布
        """
        pass

    @abc.abstractmethod
    def remove(self, event):
        """
        事件移除
        """
        pass


class SubscribeEvent(object):
    __events = []

    def __init__(self, cls):
        self.__events.append(cls)


# TODO 修改总线格式，完善注册、卸载消息机制
class EventBus(ThreadSafeSingleton):
    __items = []
    __plugins = []
    from core.library.EasyImportBase import ROOT
    __config_file = ROOT('data/config.json')
    print(
        r" ____     ___             __                ___       ____                   __                                    _          __     " + "\n"
        r"/\  _`\  /\_ \           /\ \              /\_ \     /\  _`\                /\ \                                 /' \       /'__`\   " + "\n "
        r"\ \ \L\_\\//\ \      ___ \ \ \____     __  \//\ \    \ \ \L\ \      __      \_\ \      __     _ __       __  __ /\_, \     /\ \/\ \  " + "\n"
        r" \ \ \L_L  \ \ \    / __`\\ \ '__`\  /'__`\  \ \ \    \ \ ,  /    /'__`\    /'_` \   /'__`\  /\`'__\    /\ \/\ \\/_/\ \    \ \ \ \ \ " + "\n"
        r"  \ \ \/, \ \_\ \_ /\ \L\ \\ \ \L\ \/\ \L\.\_ \_\ \_   \ \ \\ \  /\ \L\.\_ /\ \L\ \ /\ \L\.\_\ \ \/     \ \ \_/ |  \ \ \  __\ \ \_\ \ " + "\n"
        r"   \ \____/ /\____\\ \____/ \ \_,__/\ \__/.\_\/\____\   \ \_\ \_\\ \__/.\_\\ \___,_\\ \__/.\_\\ \_\      \ \___/    \ \_\/\_\\ \____/" + "\n"
        r"    \/___/  \/____/ \/___/   \/___/  \/__/\/_/\/____/    \/_/\/ / \/__/\/_/ \/__,_ / \/__/\/_/ \/_/       \/__/      \/_/\/_/ \/___/ "
    )
    Logger.main('EventBus has been started.')
    Logger.main('Initializing command manager.')
    CommandManager.command_manager()
    Logger.main('Command manager initialized.')

    def __init__(self):
        super().__init__()

    @classmethod
    def register(cls, item, key: str, item_type: EventBusItemType):
        cls.__items.append({
            'data': item,
            'key': key,
            'type': item_type
        })

    @classmethod
    def register_with_all(cls, data):
        cls.__items.append(data)

    @classmethod
    def put(cls, key, data):
        for item in cls.__items:
            if item['key'] == key:
                if item['type'] != EventBusItemType.DATA:
                    raise ValueError('Only data can be update.')
                else:
                    item['data'] = data

    @classmethod
    def get(cls, key: str):
        # TODO 改为HashMap
        for item in cls.__items:
            if item['key'] == key:
                return item
        return None

    @classmethod
    def remove(cls, key: str):
        index = None
        for _index, item in enumerate(cls.__items):
            if item['key'] == key:
                index = _index
                break
        if index is not None:
            cls.__items.remove(index)

    @classmethod
    def install_plugin(cls, plugin):
        if not isinstance(plugin, list):
            plugin = [plugin]
        for p in plugin:
            cls.__plugins.append(p)

    @classmethod
    def get_items(cls):
        return cls.__items

    @classmethod
    def get_plugin(cls, plugin_name):
        for plugin in cls.__plugins:
            if plugin.plugin_name == plugin_name:
                return plugin
        return None

    @classmethod
    def start(cls):
        PluginManager.load_plugins(cls.__plugins)
        PluginManager.run_plugins()

    @classmethod
    def stop(cls):
        PluginManager.uninstall_plugins()

    @classmethod
    def read_config_file(cls, config_files: str = None):
        if config_files is None:
            Logger.main(f'Skip load from user input, use cache only.')
        load_file = cls.__config_file if config_files is None else config_files
        Logger.main(f'EventBus load config file in {load_file}.')
        with open(load_file, 'r') as f:
            data = json.load(f)
            for k, v in data.items():
                cls.register(v, k, EventBusItemType.DATA)
        Logger.main(f'EventBus load config file success.')
