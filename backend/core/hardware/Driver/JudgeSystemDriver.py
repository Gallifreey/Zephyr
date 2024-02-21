import threading

import serial

from core.library.EventBusBase import EventBus
from core.library.Utils import Singleton, get_crc16_check_sum, append_crc16_check_sum


class JudgeSystemDriver(Singleton):
    """
    裁判系统 \n
    官方通信协议：\n
    https://rm-static.djicdn.com/tem/13194/RoboMaster_%E8%A3%81%E5%88%A4%E7%B3%BB%E7%BB%9F%E4%B8%B2%E5%8F%A3%E5%8D%8F%E8%AE%AE%E9%99%84%E5%BD%95%20V1.3.pdf
    """

    serial = serial.Serial('', 115200, timeout=0.2)

    _CMD_BEV_TRANSMISSION = 0x0305

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def bev_transmission(cls, data_length, robot: dict):
        """
        小地图传输地址
        :param data_length: 数据长度
        :param robot: {id: (x, y, z)}
        """
        rid, (x, y, _) = robot.items()
        buffer = [0]
        buffer = buffer * 200

        buffer[0] = 0xA5  # 数据帧起始字节，固定值为 0xA5
        buffer[1] = data_length & 0x00ff  # 数据帧中 data 的长度,占两个字节
        buffer[2] = (data_length & 0xff00) >> 8
        buffer[3] = 0  # 包序号
        buffer[4] = get_crc16_check_sum(id(buffer), 5 - 1, 0xff)  # 帧头 CRC8 校验
        buffer[5] = cls._CMD_BEV_TRANSMISSION & 0x00ff
        buffer[6] = (cls._CMD_BEV_TRANSMISSION & 0xff00) >> 8

        buffer[7] = rid
        buffer[8] = 0
        buffer[9] = bytes(x)[0]
        buffer[10] = bytes(x)[1]
        buffer[11] = bytes(x)[2]
        buffer[12] = bytes(x)[3]
        buffer[13] = bytes(y)[0]
        buffer[14] = bytes(y)[1]
        buffer[15] = bytes(y)[2]
        buffer[16] = bytes(y)[3]
        buffer[17:20] = [0] * 4  # 朝向，直接赋0，协议bug，不加这一项无效

        append_crc16_check_sum(id(buffer), data_length + 9)

        buffer_tmp_array = [0]
        buffer_tmp_array *= 9 + data_length

        for i in range(9 + data_length):
            buffer_tmp_array[i] = buffer[i]
        cls.serial.write(bytearray(buffer_tmp_array))

    @classmethod
    def write(cls):
        """
        循环发送串口信息
        """
        while True:
            robots = EventBus.get('bev_points')['data']
            for k, _ in robots.items():
                cls.bev_transmission(14, robots[k])

    @classmethod
    def read(cls):
        """
        循环读取串口信息
        """
        while True:
            pass

    @classmethod
    def start(cls):
        thread1 = threading.Thread(target=cls.write, daemon=False)
        thread1.start()
        thread2 = threading.Thread(target=cls.read, daemon=False)
        thread2.start()
