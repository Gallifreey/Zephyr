"""
警报：
功能1: 观察点是否在管制区，若在管制区则预警，并发送预警信息。 Warning
功能2: 哨站、基地保护。 Protect
功能3: 全局预警。 Guard
...
"""
from core.library.Utils import Singleton
from core.utils.utils import check_in_region


class Alert(Singleton):
    def __init__(self):
        super().__init__()
        self.__region = None
        self.parent = None

    def init(self):
        self.__region = self.parent.get('alert_msg')['data']

    def warning(self):
        """
        预警
        """
        q = self.parent.get('depth_queue')['data'].queue
        print(q[len(q) - 1])
        print(self.parent.get('armor_car_index')['data'])

    def protect(self):
        pass

    def guard(self):
        pass
