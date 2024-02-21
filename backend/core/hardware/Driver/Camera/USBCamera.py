import queue
import threading

import cv2

from core.library.CameraBase import Camera
from core.library.EasyImportBase import ROOT


class USBCamera(Camera):
    name = 'Static Video'

    def __init__(self):
        super().__init__()
        self.cap = None
        self.thread = None
        self.is_pause = False
        self.img_queue = queue.Queue(maxsize=10)
        self.parent = None

    def open(self):
        self.cap = cv2.VideoCapture(ROOT('video2.mp4'))
        # self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if self.cap.isOpened():
            self.thread = threading.Thread(target=self.__camera_thread, daemon=False)
            self.thread.start()
        else:
            raise RuntimeError('No camera available.')

    def read(self):
        return self.img_queue.get()

    def close(self):
        self.is_pause = True
        self.cap.release()

    def __camera_thread(self):
        while self.cap.isOpened():
            if self.is_pause:
                break
            ret, img = self.cap.read()
            if ret and img is not None:
                # img = cv2.resize(img, dsize=(1000, 600))
                self.parent.update('camera_view', img)
                if self.img_queue.full():
                    self.img_queue.get()
                self.img_queue.put(img)
            else:
                break
            cv2.waitKey(100)
