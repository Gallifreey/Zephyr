"""
反投影定位测试，可以选中或调入模型检测物体，测试物体在环境投影下的坐标精确度
"""
import cv2
import numpy as np

from core.hardware.Camera.CameraPlugin import CameraPlugin
from core.hardware.Lidar.LidarPlugin import LidarPlugin
from core.library.EasyImportBase import ROOT
from core.library.Enums import EventBusItemType
from core.library.EventBusBase import EventBus
from core.library.Utils import is_none, regen_list_from_keys, pnp, pnp2pose


class ReprojectMeasure(object):
    def __init__(self):
        self.init()

    def init(self):
        """
        程序引导
        """
        EventBus.read_config_file()
        EventBus.install_plugin([LidarPlugin, CameraPlugin])
        CameraPlugin.register(CameraPlugin.camera_view, 'camera_view', EventBusItemType.DATA)
        LidarPlugin.register(LidarPlugin.depth_queue, 'depth_queue', EventBusItemType.DATA)
        EventBus.start()

    def start(self):
        ground_width = EventBus.get('game_ground_size')['data'][1]
        # 深度图
        h_, w_ = EventBus.get('image')['data']['height'], EventBus.get('image')['data']['width']
        iw, ih = 1200, 600
        rh, rw = h_ / ih, w_ / iw
        bw, bh = 20, 20
        k0 = np.array(EventBus.get('camera_intrinsic_matrix')['data'])
        c0 = np.array(EventBus.get('camera_dist')['data'])
        bev = cv2.imread(ROOT(EventBus.get('read_bev_path')['data']))
        bev = cv2.resize(bev, dsize=(int(bev.shape[1] * 0.6), int(bev.shape[0] * 0.6)))
        real_h, real_w = EventBus.get('game_ground_size')['data']
        bev_h, bev_w, _ = bev.shape
        bev_rw = bev_w / real_w
        bev_rh = bev_h / real_h
        t, _ = self.pnp4p(size=[iw, ih])

        def callback(event, _x, _y, _, param: dict):
            if event == cv2.EVENT_LBUTTONDOWN:
                # 鼠标左键点选
                param['x'] = _x
                param['y'] = _y

        # 回调参数
        params = {
            'x': 0,
            'y': 0
        }
        while True:
            img = EventBus.get('camera_view')['data']
            if not is_none(img):
                img = cv2.resize(img, dsize=(iw, ih))
                x, y = params['x'], params['y']
                img = cv2.circle(img, (x, y), color=(0, 0, 255), radius=5, thickness=-1)
                x *= rw
                y *= rh
                cv2.imshow("camera_view", img)
                cv2.setMouseCallback("camera_view", callback, params)
                keyboard = cv2.waitKey(1) & 0xFF
                if keyboard == ord('s'):
                    bev_ = bev.copy()
                    d = self.__get_depth([x, y, x + 2 * bw, y + 2 * bh], h_, w_, k0, c0)
                    # 反投影
                    d = (t @ np.concatenate(
                        [np.concatenate([d[0:2], np.ones(1)], axis=0) * d[2], np.ones(1)], axis=0))[:3]
                    # 坐标变换
                    d[1] += ground_width
                    # 伸缩
                    bev_ = cv2.circle(bev_, (int(d[1] * bev_rw), int(d[0] * bev_rh)), color=(0, 0, 255),
                                      thickness=-1, radius=2)
                    cv2.imshow("bev", bev_)
                    cv2.waitKey(1)

    def pnp4p(self, size):
        """
        PNP 4点标定
        """

        def callback(event, _x, _y, _, param: dict):
            if event == cv2.EVENT_LBUTTONDOWN:
                # 鼠标左键点选
                param[f"p{param['time'] + 1}"] = [_x, _y]
                param['time'] += 1
                if param['time'] == 4:
                    param['time'] = 0

        # 回调参数
        params = {
            'p1': [0, 0],
            'p2': [0, 0],
            'p3': [0, 0],
            'p4': [0, 0],
            'time': 0
        }
        while True:
            img = EventBus.get('camera_view')['data']
            if not is_none(img):
                img = cv2.resize(img, dsize=(1200, 600))
                img = cv2.polylines(img, np.array([regen_list_from_keys(params, [f'p{i + 1}' for i in range(4)])]),
                                    True, thickness=2, color=(0, 0, 255))
                cv2.imshow("camera_view", img)
                cv2.setMouseCallback("camera_view", callback, params)
                keyboard = cv2.waitKey(1) & 0xFF
                if keyboard == ord('s'):
                    points = params.copy()
                    # 标志进行PNP解算
                    rw = EventBus.get('image')['data']['width'] / size[0]
                    rh = EventBus.get('image')['data']['height'] / size[1]
                    for k, v in points.items():
                        if k != 'time':
                            x, y = points[k]
                            points[k] = [x * rw, y * rh]
                    # 解算
                    obp = EventBus.get('real_world_label_points')['data']
                    rvec, tvec = pnp(list(points.values())[:-1],
                                     [obp['red_base'], obp['blue_outpost'], obp['b_rt'], obp['b_lt']],
                                     EventBus.get('camera_intrinsic_matrix')['data'],
                                     EventBus.get('camera_dist')['data'])
                    t, cp = pnp2pose(rvec, tvec)
                    return t, cp
                elif keyboard == ord('c'):
                    # 清空，重新进行选点
                    for i in range(4):
                        params[f'p{i + 1}'] = [0, 0]
                elif keyboard == ord('f'):
                    # 退回前一个点
                    if params['time'] != 0:
                        params[f"p{params['time']}"] = [0, 0]
                        params['time'] -= 1

    def __get_depth(self, point: list, h_, w_, k0, c0):
        """
        抽离出来的计算深度程序
        :param point: 像素坐标点
        """

        def xywh2c(p):
            return np.float32([p[0] + (p[2] / 2), p[1] + (p[3] / 2)])

        def xyxy2xywh(p):
            return [p[0], p[1], abs(p[2] - p[0]), abs(p[3] - p[1])]

        depth = EventBus.get('depth_queue')['data'].get_depth()
        x1, y1, x2, y2 = point
        box = xyxy2xywh([x1, y1, x2, y2])
        c = xywh2c(box)
        area = depth[int(max(0, c[1] - box[3])):int(min(c[1] + box[3], h_ - 1)),
               int(max(c[0] - box[2], 0)):int(min(c[0] + box[2], w_ - 1))]
        z = np.nanmean(area) if not np.isnan(area).all() else np.nan
        return np.concatenate([cv2.undistortPoints(c, k0, c0).reshape(-1), np.array([z])],
                              axis=0)


if __name__ == "__main__":
    rm = ReprojectMeasure()
    rm.start()
