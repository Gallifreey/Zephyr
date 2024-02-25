"""
深度测量程序，在这个程序中提供了对雷达精度的测试。
包括：雷达三级测量精度测试、ROI平均深度测量测试、标定板深度测试
注意：在此程序中，不含雷达相机标定程序，需提前进行标定后可运行本程序，如若测试标定精度，请见CalibrationMeasure
"""
import cv2
import numpy as np

from core.hardware.Camera.CameraPlugin import CameraPlugin
from core.hardware.Lidar.LidarPlugin import LidarPlugin
from core.library.Enums import EventBusItemType
from core.library.EventBusBase import EventBus
from core.library.Utils import is_none, find_board, board2xyxy


class DepthMeasure(object):
    """
    深度测量程序类
    """

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

    def start(self, params):
        """
        开启测试
        :param params: 测试参数
        `basic`: 提供基本的点击取深度
        `auto`: 提供自动获取物体深度的功能，这里仅提供标定板检测
        `roi`: 提供框选区域深度功能
        """
        if params == "basic":
            self.run_basic()
        elif params == "auto":
            self.run_auto()
        elif params == "roi":
            self.run_roi()
        else:
            raise RuntimeError("No available param is given.")

    def run_basic(self):

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

        # 深度图
        h_, w_ = EventBus.get('image')['data']['height'], EventBus.get('image')['data']['width']
        iw, ih = 1200, 600
        rh, rw = h_ / ih, w_ / iw
        bw, bh = 20, 20
        while True:
            img = EventBus.get('camera_view')['data']
            if not is_none(img):
                img = cv2.resize(img, dsize=(iw, ih))
                _, h = cv2.getTextSize('A', cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2)
                x, y = params['x'], params['y']
                img = cv2.circle(img, (x, y), color=(0, 0, 255), radius=5, thickness=-1)
                x *= rw
                y *= rh
                img = cv2.putText(img, f"Depth on selected point: {self.__get_depth([x, y, x + 2 * bw, y + 2 * bh], h_, w_)}(m)", (0, 2 * h),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)
                cv2.imshow("camera_view", img)
                cv2.setMouseCallback("camera_view", callback, params)
                cv2.waitKey(1)

    def run_auto(self):
        # 深度图
        h_, w_ = EventBus.get('image')['data']['height'], EventBus.get('image')['data']['width']
        iw, ih = 1200, 600
        rh, rw = h_ / ih, w_ / iw
        while True:
            img = EventBus.get('camera_view')['data']
            if not is_none(img):
                img = cv2.resize(img, dsize=(1200, 600))
                _, h = cv2.getTextSize('A', cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2)
                # 找标定板
                img, img_points = find_board(img)  # shape (N, 1, 2)
                p1, p2 = board2xyxy(img_points)
                if not is_none(p1) and not is_none(p2):
                    [x1, y1], [x2, y2] = p1, p2
                    x1 *= rw
                    y1 *= rh
                    x2 *= rw
                    y2 *= rh
                    img = cv2.putText(img,
                                      f"AvgDepth on detected BOARD: {self.__get_depth([x1, y1, x2, y2], h_, w_)}(m)",
                                      (0, 2 * h),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)
                cv2.imshow("camera_view", img)
                cv2.waitKey(1)

    def run_roi(self):
        def callback(event, _x, _y, _, param: dict):
            if event == cv2.EVENT_LBUTTONDOWN:
                # 鼠标左键点选
                if param['time'] == 0:
                    # 选中矩形左上角
                    param['x1'] = _x
                    param['y1'] = _y
                    params['time'] += 1
                elif param['time'] == 1:
                    # 选中矩形右下角
                    param['x2'] = _x
                    param['y2'] = _y
                    params['time'] -= 1

        # 回调参数
        params = {
            'x1': -1,
            'y1': -1,
            'x2': -1,
            'y2': -1,
            'time': 0
        }

        # 深度图
        h_, w_ = EventBus.get('image')['data']['height'], EventBus.get('image')['data']['width']
        iw, ih = 1200, 600
        rh, rw = h_ / ih, w_ / iw
        while True:
            img = EventBus.get('camera_view')['data']
            if not is_none(img):
                img = cv2.resize(img, dsize=(iw, ih))
                _, h = cv2.getTextSize('A', cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2)
                img = cv2.circle(img, (params['x1'], params['y1']), color=(0, 0, 255), radius=5, thickness=-1)
                img = cv2.circle(img, (params['x2'], params['y2']), color=(0, 0, 255), radius=5, thickness=-1)
                img = cv2.rectangle(img, (params['x1'], params['y1']), (params['x2'], params['y2']), color=(0, 0, 255))
                x1, y1, x2, y2 = params['x1'], params['y1'], params['x2'], params['y2']
                x1 *= rw
                y1 *= rh
                x2 *= rw
                y2 *= rh
                img = cv2.putText(img, f'AvgDepth on selected ROI: {self.__get_depth([x1, y1, x2, y2], h_, w_)}(m)', (0, 2 * h),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)
                cv2.imshow("camera_view", img)
                cv2.setMouseCallback("camera_view", callback, params)
                cv2.waitKey(1)

    def __get_depth(self, point: list, h_, w_):
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
        return z


if __name__ == "__main__":
    dm = DepthMeasure()
    dm.start('auto')
