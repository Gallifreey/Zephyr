from core.library.Utils import Singleton


class Serial(Singleton):
    """
    串口类，用于发送/接收信息，机间通信。
    """
    def __init__(self):
        super().__init__()

    @classmethod
    def open(cls):
        """
        开启串口
        """
        pass
