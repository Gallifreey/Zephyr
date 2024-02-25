"""
反投影定位测试，可以选中或调入模型检测物体，测试物体在环境投影下的坐标精确度
"""
import cv2

from core.hardware.Camera.CameraPlugin import CameraPlugin
from core.hardware.Lidar.LidarPlugin import LidarPlugin
from core.library.Enums import EventBusItemType
from core.library.EventBusBase import EventBus


class ReprojectMeasure(object):
    def __init__(self):
        pass

    def init(self):
        """
        程序引导
        """
        EventBus.read_config_file()
        EventBus.install_plugin([LidarPlugin, CameraPlugin])
        CameraPlugin.register(CameraPlugin.camera_view, 'camera_view', EventBusItemType.DATA)
        LidarPlugin.register(LidarPlugin.depth_queue, 'depth_queue', EventBusItemType.DATA)
        EventBus.start()
