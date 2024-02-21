import threading
import time

from core.library.PluginBase import PluginBase
from core.library.Utils import Singleton
from core.utils.logger import Logger
from radar_websocket.views import VideoStreamView, DataView, ReprojectView, LogView, CalibrateView, CalibrationDataView


class WebsocketPlugin(PluginBase, Singleton):
    plugin_name = 'websocket'
    # Register Start
    label_points = []
    # Register End

    def __init__(self):
        super().__init__()
        self.priority = 1

    @classmethod
    def start(cls):
        Logger.info('Websocket server starting...')
        thread = threading.Thread(target=cls.__web_thread, daemon=False)
        thread.start()
        Logger.info('Websocket server done.')

    @classmethod
    def uninstall(cls):
        pass

    @classmethod
    def __web_thread(cls):
        t = threading.Thread(target=cls.t1, daemon=False)
        t1 = threading.Thread(target=cls.t2, daemon=False)
        t2 = threading.Thread(target=cls.t3, daemon=False)
        t3 = threading.Thread(target=cls.t4, daemon=False)
        t4 = threading.Thread(target=cls.t5, daemon=False)
        t5 = threading.Thread(target=cls.t6, daemon=False)
        t.start()
        t1.start()
        t2.start()
        t3.start()
        t4.start()
        t5.start()

    @staticmethod
    def t1():
        view1 = VideoStreamView()

    @staticmethod
    def t2():
        view2 = DataView()

    @staticmethod
    def t3():
        view3 = ReprojectView()

    @staticmethod
    def t4():
        view4 = LogView()

    @staticmethod
    def t5():
        view5 = CalibrateView()

    @staticmethod
    def t6():
        view6 = CalibrationDataView()