import threading
import time

from core.inference.geometry.reproject import Reproject
from core.library.EventBusBase import EventBus
from core.library.PluginBase import PluginBase


class ReprojectPlugin(PluginBase):
    __reproject = Reproject()
    depth = None
    cam2world = None
    cam_in_world = None
    bev_points = None
    plugin_name = 'reproject'

    def __init__(self):
        super().__init__()

    @classmethod
    def start(cls):
        thread = threading.Thread(target=cls.__reproject_thread, daemon=False)
        thread.start()

    @classmethod
    def uninstall(cls):
        pass

    @classmethod
    def __reproject_thread(cls):
        cls.__reproject.parent = cls
        cls.__reproject.t = EventBus.get('cam2world')
        while True:
            if EventBus.get('armor_car_index') and EventBus.get('depth_queue'):
                cls.__reproject.get_depth(EventBus.get('armor_bbox')['data'], EventBus.get('depth_queue')['data'])
                time.sleep(0.01)
            else:
                time.sleep(0.1)
