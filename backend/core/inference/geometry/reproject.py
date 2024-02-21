import time

import cv2
import numpy as np

from core.library.Draw import BEVHandler
from core.library.EasyImportBase import ROOT
from core.library.Utils import Singleton, is_none


class Reproject(Singleton):
    """
    反投影类，接收armor坐标，将点云数据转换成深度
    """

    def __init__(self):
        super().__init__()
        self.parent = None
        self.t = None
        self.img = cv2.rotate(cv2.imread(ROOT('map.jpg')), cv2.ROTATE_90_CLOCKWISE)
        self.size = [1150, 616]

    def get_depth(self, armor, cloud):
        """
        获取深度数据
        :param armor: armor[cls, bbox, conf]索引
        :param cloud: 点云
        :return: 深度d
        """
        if is_none(armor) or is_none(cloud) or is_none(self.t['data']):
            return
        # 获取所有armor对应的类别与深度
        depth = cloud.get_armor_depth(armor)
        if is_none(depth):
            return
        # 反投影
        bev_points = {}  # 映射到小地图上的点
        ground_width = self.parent.get('game_ground_size')['data'][1]
        for cls, d in depth:
            d = (self.t['data'] @ np.concatenate(
                [np.concatenate([d[0:2], np.ones(1)], axis=0) * d[2], np.ones(1)], axis=0))[:3]
            # 坐标变换
            d[1] += ground_width
            bev_points[cls] = d
        self.parent.update('bev_points', bev_points)
        BEVHandler.draw()
        print(bev_points)

    def alert(self):
        """
        预警，暂不将预警另设插件
        """
