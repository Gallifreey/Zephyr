import abc


class Lidar(metaclass=abc.ABCMeta):
    info: dict

    def __init__(self):
        pass

    @abc.abstractmethod
    def build_connection(self):
        """
        建立连接
        """
        pass

    @abc.abstractmethod
    def start(self):
        """
        开启雷达
        """
        pass

    @abc.abstractmethod
    def close(self):
        """
        关闭雷达
        """
        pass

    @abc.abstractmethod
    def load_pcd(self):
        """
        加载点云
        """
        pass
