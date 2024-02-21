from core.library.CommandBase import CommandBase


class CommandLidar(CommandBase):

    def __init__(self):
        super().__init__()

    def execute(self, command_pack, lidar_entity):
        """
        Lidar指令组，基本格式： \n
        /lidar [lidar_name] [lidar_operation]{open, close, start_record, stop_record} [optional args]
        """
        name, operation, args = self.command_pack['args']
        if operation == "open":
            lidar_entity.start()
        elif operation == "close":
            lidar_entity.close()
        elif operation == "start_record":
            pass
        elif operation == "stop_record":
            pass

    def get_result(self):
        pass

    def get_name(self):
        return "lidar"
