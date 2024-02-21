import numpy as np

from core.hardware.Lidar.LivoxMid70 import LivoxMid70
from core.library.EventBusBase import EventBus
from core.library.PluginBase import PluginBase
from core.library.Utils import DepthQueue


class LidarPlugin(PluginBase):
    use_file = True
    __livox = LivoxMid70(use_file=use_file)
    plugin_name = 'lidar'
    depth_queue = DepthQueue(maxsize=120)

    def __init__(self):
        super().__init__()

    @classmethod
    def start(cls):
        # 初始化参数
        cls.depth_queue.set(k0=np.array(EventBus.get('camera_intrinsic_matrix')['data']), c0=np.array(EventBus.get('camera_dist')['data']), e0=np.array(EventBus.get('lidar_extrinsic')['data']), size=[EventBus.get('image')['data']['height'], EventBus.get('image')['data']['width']])
        if not cls.use_file:
            cls.__livox.build_connection()
        else:
            cls.__livox.load_pcd()

    @classmethod
    def uninstall(cls):
        pass

    @classmethod
    def get_entity(cls):
        return cls.__livox
