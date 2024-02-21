from core.library.Draw import BEVHandler
from core.library.EventBusBase import EventBus, EventBusItemType
from core.inference.ReprojectPlugin import ReprojectPlugin
from core.inference.YoloPlugin import YoloPlugin
from core.hardware.Camera.CameraPlugin import CameraPlugin
from core.hardware.Lidar.LidarPlugin import LidarPlugin
from core.inference.AlertPlugin import AlertPlugin
from radar_websocket.WebsocketPlugin import WebsocketPlugin

# TODO 深度测量例程、相机标定例程

if __name__ == "__main__":
    EventBus.read_config_file()
    BEVHandler.bus_handler = EventBus
    BEVHandler.init()
    EventBus.install_plugin([LidarPlugin, AlertPlugin, CameraPlugin, YoloPlugin, WebsocketPlugin, ReprojectPlugin])
    CameraPlugin.register(CameraPlugin.camera_view, 'camera_view', EventBusItemType.DATA)
    YoloPlugin.register(YoloPlugin.annotator_result, 'annotator_result', EventBusItemType.DATA)
    YoloPlugin.register(YoloPlugin.armor_car_index, 'armor_car_index', EventBusItemType.DATA)
    YoloPlugin.register(YoloPlugin.armor_bbox, 'armor_bbox', EventBusItemType.DATA)
    AlertPlugin.register(AlertPlugin.alert_msg, 'alert_msg', EventBusItemType.DATA)
    LidarPlugin.register(LidarPlugin.depth_queue, 'depth_queue', EventBusItemType.DATA)
    ReprojectPlugin.register(ReprojectPlugin.cam2world, 'cam2world', EventBusItemType.DATA)
    ReprojectPlugin.register(ReprojectPlugin.cam_in_world, 'cam_in_world', EventBusItemType.DATA)
    ReprojectPlugin.register(ReprojectPlugin.bev_points, 'bev_points', EventBusItemType.DATA)
    WebsocketPlugin.register(WebsocketPlugin.label_points, 'label_points', EventBusItemType.DATA)
    EventBus.start()
