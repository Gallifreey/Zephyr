import threading

import numpy as np

from core.library.CameraBase import Camera
import pyzed.sl as sl
import cv2
from core.utils.logger import Logger


class ZED(Camera):
    """
    此为ZED相机类，用于创建、管理ZED相机
    """
    name = 'ZED'

    def __init__(self):
        super().__init__()
        self.__zed = sl.Camera()
        self.__init_params = sl.InitParameters()
        self.grab_image = None
        self.thread = None
        self.parent = None
        self.__r_gain = 131
        self.__g_gain = 114
        self.__b_gain = 100
        self.__r_factor = self.__r_gain / 255.0
        self.__g_factor = self.__g_gain / 255.0
        self.__b_factor = self.__b_gain / 255.0

    def open(self):
        # 读取 ZED 相机参数
        if self.parent:
            self.load_config(self.parent.get('camera')['data'])
        self.__init_params.camera_resolution = sl.RESOLUTION.HD2K
        self.__init_params.camera_fps = 30
        err = self.__zed.open(self.__init_params)
        if err != sl.ERROR_CODE.SUCCESS:
            Logger.danger(f"Camera Open :{repr(err)}.")
            self.close()
        else:
            self.thread = threading.Thread(target=self.__camera_thread, daemon=False)
            self.thread.start()

    def read(self):
        pass

    def close(self):
        self.__zed.close()
        Logger.info("ZED closed.")

    def __camera_thread(self):
        image = sl.Mat()
        runtime_parameters = sl.RuntimeParameters()
        while True:
            if self.__zed.grab(runtime_parameters) == sl.ERROR_CODE.SUCCESS:
                self.__zed.retrieve_image(image, sl.VIEW.RIGHT)
                grab_image = cv2.cvtColor(src=image.get_data(), code=1)
                if grab_image is not None:
                    grab_image = cv2.resize(grab_image, dsize=(1000, 600))
                    if self.parent:
                        self.parent.update('camera_view', grab_image)
                    else:
                        grab_image = self.__img_change(grab_image)
                        cv2.imshow("zed_view", grab_image)
                        cv2.waitKey(1)

    def load_config(self, file: str):
        pass

    def __img_change(self, img):
        img = np.clip(img * [self.__r_factor, self.__g_factor, self.__b_factor], 0, 255).astype(np.uint8)
        return img
