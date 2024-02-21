import abc
import asyncio
import socket


class RadarWebsocketViewBase(metaclass=abc.ABCMeta):

    def __init__(self):
        self.server = None
        try:
            hostname = socket.gethostname()
            self.host = socket.gethostbyname(hostname)
        except RuntimeError:
            self.host = "127.0.0.1"
        self.init()

    def init(self):
        """
        初始化ws，提供修改后的port及host构建url
        """
        # 重新获取事件循环
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        from websockets.legacy.server import serve
        self.server = serve(self.enter, self.host, self.port)
        asyncio.get_event_loop().run_until_complete(self.server)
        asyncio.get_event_loop().run_forever()

    @abc.abstractmethod
    async def enter(self, websocket):
        """
        websocket入口函数
        """
        pass
