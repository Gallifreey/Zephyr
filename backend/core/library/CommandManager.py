from core.commands.CommandLidar import CommandLidar
from core.library.Utils import Singleton


class CommandManager(Singleton):
    """
    指令管理
    """
    __command_map = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def command_manager(cls):
        cls._register_command(CommandLidar)

    @classmethod
    def _register_command(cls, command):
        cls.__command_map[command().get_name()] = command
