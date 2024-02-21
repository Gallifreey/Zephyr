from core.hardware.Camera.CameraPlugin import CameraPlugin
from core.hardware.Lidar.LidarPlugin import LidarPlugin
from core.inference.AlertPlugin import AlertPlugin
from core.inference.YoloPlugin import YoloPlugin
from radar_websocket.WebsocketPlugin import WebsocketPlugin
from core.library.EasyImportBase import ROOT
from core.library.EventBusBase import EventBus, EventBusItemType
from core.library.Utils import Singleton

# TODO 场地模拟，创建虚拟场地，模拟算法结果


class Simulation(Singleton):
    """
    模拟类
    """

    def __init__(self):
        super().__init__()

    @classmethod
    def create_background(cls):
        """
        创建背景
        """
        pass

    @classmethod
    def read_config_file(cls):
        EventBus.read_config_file(ROOT("data/simulate_config.json"))

    @classmethod
    def start(cls):
        EventBus.install_plugin([CameraPlugin, LidarPlugin, AlertPlugin, YoloPlugin, WebsocketPlugin])
        CameraPlugin.register(CameraPlugin.camera_view, 'camera_view', EventBusItemType.DATA)
        AlertPlugin.register(AlertPlugin.alert_msg, 'alert_msg', EventBusItemType.DATA)
        LidarPlugin.register(LidarPlugin.depth_queue, 'depth_queue', EventBusItemType.DATA)
        YoloPlugin.register(YoloPlugin.reproject_points, 'reproject_points', EventBusItemType.DATA)
        YoloPlugin.register(YoloPlugin.annotator_result, 'annotator_result', EventBusItemType.DATA)
        YoloPlugin.register(YoloPlugin.armor_car_index, 'armor_car_index', EventBusItemType.DATA)
        EventBus.start()
        # while True:
        #     print(EventBus.get('depth_queue')['data'].queue)


Simulation.read_config_file()
Simulation.start()
