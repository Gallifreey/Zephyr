import threading

from core.inference.yolov5.detect import YoloDetector
from core.library.EventBusBase import EventBus
from core.library.PluginBase import PluginBase


# TODO 精简化YOLO
class YoloPlugin(PluginBase):
    __thread = None
    annotator_result = None  # 检测结果图像
    armor_car_index = None   # armor-car索引表
    armor_bbox = None        # armor的bbox[[cls, bbox], ...]
    is_pause = False
    plugin_name = 'yolo'

    def __init__(self):
        super().__init__()
        self.priority = 1

    @classmethod
    def start(cls):
        cls.__thread = threading.Thread(target=cls.__yolo_thread, daemon=False)
        cls.__thread.start()

    @classmethod
    def uninstall(cls):
        cls.is_pause = True

    @classmethod
    def __yolo_thread(cls):
        YoloDetector.parent = cls
        while not cls.is_pause:
            img = EventBus.get('camera_view')['data']
            if img is not None:
                YoloDetector.run(img)
