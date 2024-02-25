"""
相机，环境标定精度测试，通过规整目标的尺寸，确定标定的精度
"""
import cv2
import numpy as np

from core.hardware.Camera.CameraPlugin import CameraPlugin
from core.library.Enums import EventBusItemType
from core.library.EventBusBase import EventBus
from core.library.Utils import is_none, find_board, regen_list_from_keys


class CalibrationMeasure(object):
    def __init__(self):
        self.init()

    def init(self):
        """
        程序引导
        """
        EventBus.read_config_file()
        EventBus.install_plugin(CameraPlugin)
        CameraPlugin.register(CameraPlugin.camera_view, 'camera_view', EventBusItemType.DATA)
        EventBus.start()

    def start(self, params):
        if params == 'cam':
            self.run_cam()
        elif params == 'env':
            self.run_env()

    def run_cam(self):
        while True:
            img = EventBus.get('camera_view')['data']
            if not is_none(img):
                img = cv2.resize(img, dsize=(1200, 600))
                _, h = cv2.getTextSize('AvgDepth on selected ROI: (m)', cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2)
                img = cv2.putText(img, 'AvgDepth on selected ROI: ', (0, 2 * h),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)
                # 找标定板
                img, img_points = find_board(img)
                cv2.imshow("camera_view", img)
                cv2.waitKey(1)

    def run_env(self):
        self.pnp4p()  # 先进行标定
        while True:
            img = EventBus.get('camera_view')['data']
            if not is_none(img):
                img = cv2.resize(img, dsize=(1200, 600))
                _, h = cv2.getTextSize('AvgDepth on selected ROI: (m)', cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2)
                img = cv2.putText(img, 'AvgDepth on selected ROI: ', (0, 2 * h),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)
                # 找标定板
                img, img_points = find_board(img)
                cv2.imshow("camera_view", img)
                cv2.waitKey(1)

    def pnp4p(self):
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
                    # 标志进行PNP解算

                    pass
                elif keyboard == ord('c'):
                    # 清空，重新进行选点
                    for i in range(4):
                        params[f'p{i + 1}'] = [0, 0]
                elif keyboard == ord('f'):
                    # 退回前一个点
                    if params['time'] != 0:
                        params[f"p{params['time']}"] = [0, 0]
                        params['time'] -= 1


if __name__ == "__main__":
    cm = CalibrationMeasure()
    cm.start('cam')
