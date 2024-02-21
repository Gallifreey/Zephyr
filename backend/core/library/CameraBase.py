import abc
import cv2


class Camera(metaclass=abc.ABCMeta):
    name = 'UNKNOWN'

    def __init__(self):
        super().__init__()

    @abc.abstractmethod
    def open(self):
        """
        相机入口函数
        """
        pass

    @abc.abstractmethod
    def read(self):
        """
        获取相机图像数据
        """
        pass

    @abc.abstractmethod
    def close(self):
        """
        相机关闭函数
        """
        pass

    @staticmethod
    def encode_to_byte(frame):
        """
        向HTML解码成byte
        """
        if frame is None:
            return None
        else:
            ret, frame = cv2.imencode('.jpeg', frame)
            if ret:
                return frame.tobytes()
            else:
                return None
