import copy

import cv2
import numpy as np

from core.library.EasyImportBase import ROOT
from core.library.Utils import Singleton, RED, BLUE, normalize_dict

"""
绘制BEV
"""


class BEVHandler(Singleton):
    """
    BEV绘制句柄
    """
    bev = None
    bus_handler = None
    bev_size = None
    ground_size = None
    bg_ratio = None

    @classmethod
    def init(cls):
        """
        初始化BEV
        region: BEV预警区域，格式[[(x1, y2), ...], ...]
        """
        cls.bev = cv2.imread(ROOT(cls.bus_handler.get('read_bev_path')['data']))
        region = cls.bus_handler.get('alert_region')['data']
        h, w, _ = cls.bev.shape
        cls.bev_size = [h, w]
        cls.ground_size = cls.bus_handler.get('game_ground_size')['data']
        cls.bg_ratio = [cls.bev_size[1] / cls.ground_size[1], cls.bev_size[0] / cls.ground_size[0]]
        for k, r in region.items():
            r = np.array(r).reshape((-1, 1, 2))
            cv2.polylines(cls.bev, [r], True, RED, 4)
            # 补全下半层
            r[:, :, 0] = w - r[:, :, 0]
            r[:, :, 1] = h - r[:, :, 1]
            cv2.polylines(cls.bev, [r], True, BLUE, 4)

    @classmethod
    def draw(cls):
        bev = cls.bev.copy()
        robots = copy.deepcopy(cls.bus_handler.get('bev_points')['data'])
        cls.draw_robots(bev, normalize_dict(robots, cls.bg_ratio))
        cv2.imshow('bev', cv2.resize(bev, dsize=(400, 800)))
        cv2.waitKey(1)

    @classmethod
    def draw_robots(cls, bev, robots):
        for label, robot in robots.items():
            is_red = label > 5
            if np.isnan(robot[0]) or np.isnan(robot[1]):
                continue
            bev = cv2.circle(bev, (int(robot[1]), int(robot[0])), 10,
                             RED if is_red else BLUE, thickness=-1)
            bev = cv2.putText(bev, str(label % 6 + 1), (int(robot[1]), int(robot[0])),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

