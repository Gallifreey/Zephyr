from core.hardware.Driver.LivoxLidarDriver import LivoxLidarDriver
from core.library.LidarBase import Lidar
from core.utils.logger import Logger


# TODO 1. 添加雷达驱动的保存点云的功能
# TODO 2. 添加雷达获取深度图的功能
class LivoxMid70(Lidar):
    """
    此为Livox Mid 70雷达类，用于创建、管理雷达，并通信。
    """

    def __init__(self, use_file):
        super().__init__()
        self.livox_mid70 = LivoxLidarDriver(without_lidar=use_file)

    def build_connection(self):
        self.livox_mid70.connect()

    def start(self):
        self.livox_mid70.start_record()

    def close(self):
        self.livox_mid70.stop_record()
        self.livox_mid70.disconnect()

    def load_pcd(self):
        self.livox_mid70.load_pcd_file()
