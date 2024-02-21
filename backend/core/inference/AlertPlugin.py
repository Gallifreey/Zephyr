import threading
import cv2
from core.inference.echo.alert import Alert
from core.library.PluginBase import PluginBase


class AlertPlugin(PluginBase):
    __alert = Alert()
    alert_msg = None
    is_pause = False
    plugin_name = 'alert'

    def __init__(self):
        super().__init__()
        self.priority = 1

    @classmethod
    def start(cls):
        thread = threading.Thread(target=cls.__alert_thread, daemon=False)
        thread.start()

    @classmethod
    def uninstall(cls):
        cls.is_pause = True

    @classmethod
    def __alert_thread(cls):
        cls.__alert.parent = cls
        cls.__alert.init()
