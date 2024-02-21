from core.hardware.Camera.USBCamera import USBCamera
from core.hardware.Camera.ZED import ZED
from core.library.PluginBase import PluginBase
from core.utils.logger import Logger


class CameraPlugin(PluginBase):
    __camera = USBCamera()
    camera_view = None  # 摄像头视野
    plugin_name = 'camera'

    def __init__(self):
        super().__init__()
        self.priority = 1

    @classmethod
    def start(cls):
        cls.__camera.parent = cls
        cls.__camera.open()
        Logger.info(f'{cls.__camera.name} open.')

    @classmethod
    def uninstall(cls):
        cls.__camera.close()
