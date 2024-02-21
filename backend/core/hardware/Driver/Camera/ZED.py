import threading

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

    def open(self):
        self.__init_params.camera_resolution = sl.RESOLUTION.HD1080
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
                self.__zed.retrieve_image(image, sl.VIEW.LEFT)
                grab_image = cv2.cvtColor(src=image.get_data(), code=1)
                if grab_image is not None:
                    grab_image = cv2.resize(grab_image, dsize=(1000, 600))
                    self.parent.update('camera_view', grab_image)
