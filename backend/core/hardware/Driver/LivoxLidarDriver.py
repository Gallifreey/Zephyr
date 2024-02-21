import binascii
import select
import socket
import struct
import threading
import time

import crcmod
import cv2
import numpy as np

from core.library.EasyImportBase import ROOT
from core.library.EventBusBase import EventBus
from core.utils.logger import Logger


class _LivoxLidarPointCloudObject(object):
    """
    Livox雷达点云格式基类
    """
    timestamps = []
    timestamp_types = []
    slot_ids = []
    lidar_ids = []
    returnNums = []


class _LivoxMid70PointCloudType(_LivoxLidarPointCloudObject):
    """
    LivoxMid70雷达点云格式
    """
    x = []
    y = []
    z = []
    intensities = []
    tags = []


class _LivoxLidarHeartbeatThread(object):
    """
    Livox雷达心跳维持线程
    """

    def __init__(self, interval, transmit_socket, send_to_ip, send_to_port, send_command, show_log):
        self.interval = interval
        self.transmit_socket = transmit_socket
        self.ip = send_to_ip
        self.port = send_to_port
        self.cmd = send_command
        self.show_log = show_log
        self.started = True
        self.work_state = -1
        self.idle_state = 0

        self.thread = threading.Thread(target=self.run, args=())
        self.thread.daemon = True
        self.thread.start()

    def run(self):
        while True:
            if self.started:
                self.transmit_socket.sendto(self.cmd, (self.ip, self.port))
                if select.select([self.transmit_socket], [], [], 0.1)[0]:
                    binData, addr = self.transmit_socket.recvfrom(22)
                    tempObj = LivoxLidarDriver()
                    _, ack, cmd_set, cmd_id, ret_code_bin = tempObj.parse_resp(binData)
                    if ack == "ACK (response)" and cmd_set == "General" and cmd_id == "3":
                        ret_code = int.from_bytes(ret_code_bin[0], byteorder='little')
                        if ret_code != 0:
                            if self.show_log:
                                Logger.danger(f"{self.ip} is incorrect heartbeat response")
                        else:
                            self.work_state = int.from_bytes(ret_code_bin[1], byteorder='little')
                            if self.work_state == 4:
                                Logger.danger(f"{self.ip} is HEARTBEAT ERROR MESSAGE RECEIVED")
                                break
                    elif ack == "MSG (message)" and cmd_set == "General" and cmd_id == "7":
                        Logger.danger(f"{self.ip} is ABNORMAL STATUS MESSAGE RECEIVED")
                        break
                    else:
                        if self.show_log:
                            Logger.danger(f"{self.ip} is incorrect heartbeat response")
                for i in range(9, -1, -1):
                    self.idle_state = i
                    time.sleep(self.interval / 10.0)
            else:
                break

    def stop(self):
        self.started = False
        self.thread.join()
        self.idle_state = 9


class _LivoxPointCloudRecordThread(object):
    """
    Livox雷达点云录制线程
    """

    def __init__(self, lidar_ip=None, receive_socket=None, wait_seconds=0., duration=0., firmware_type=None,
                 show_log=True, without_lidar=False):
        self.lidar_ip = lidar_ip
        self.receive_socket = receive_socket
        self.wait_seconds = wait_seconds
        self.duration = duration
        self.firmware_type = firmware_type
        self.show_log = show_log
        self.without_lidar = without_lidar
        self.started = True
        self.is_recording = False
        self.is_saved = False
        self.dataType = -1
        self.version = -1
        self.system_status = -1
        self.temp_status = -1
        self.volt_status = -1
        self.motor_status = -1
        self.dirty_status = -1
        self.firmware_status = -1
        self.pps_status = -1
        self.device_status = -1
        self.start_time = None
        self.livox_mid70_point_cloud_array_object = None
        self.depth_image = []  # 深度图，尺寸：w*h(单位：m)
        self.support_pcd_type = ['txt', 'pcd', 'pkl']
        self._width = 0  # 分辨率宽度
        self._height = 0  # 分辨率高度
        self._rVec = None  # 雷达外参，相对左相机的旋转向量
        self._tVec = None  # 雷达外参，相对左相机的平移向量
        self._cMat = None  # 相机内参
        self._cDif = None  # 相机畸变系数
        self._extrinsic = None  # 雷达外参
        self._device_extrinsic = None  # 设备外参
        self._saved_path = ""  # PCD存储路径

        self._init()

        if not self.without_lidar:
            self.thread = threading.Thread(target=self.run, args=())
            self.thread.daemon = True
            self.thread.start()

    def _init(self):
        self._width = EventBus.get('image')['data']['width']
        self._height = EventBus.get('image')['data']['height']
        self._extrinsic = np.array(EventBus.get('lidar_extrinsic')['data'], dtype=np.float64)
        self._rVec = cv2.Rodrigues(self._extrinsic[:3, :3])[0]
        self._tVec = self._extrinsic[:3, 3]
        self._cMat = np.array(EventBus.get('camera_intrinsic_matrix')['data'], dtype=np.float64)
        self._cDif = np.array(EventBus.get('camera_dist')['data'], dtype=np.float64)
        self._saved_path = EventBus.get('saved_point_cloud_path')['data']
        self._device_extrinsic = EventBus.get('device_extrinsic')['data']

    def run(self):
        # 无雷达情况，读点云文件
        if self.without_lidar:
            self.read_pcd(EventBus.get('read_pcd_path')['data'])
            return
        breakByRecord = False
        while True:
            if self.started:
                if select.select([self.receive_socket], [], [], 0)[0]:
                    data_pc, addr = self.receive_socket.recvfrom(1500)
                    self.version = int.from_bytes(data_pc[0:1], byteorder='little')
                    self.dataType = int.from_bytes(data_pc[9:10], byteorder='little')
                    timestamp_type = int.from_bytes(data_pc[8:9], byteorder='little')
                    timestamp1 = self.get_time_stamp(data_pc[10:18], timestamp_type)
                    self.update_status(data_pc[4:8])
                    if self.is_recording:
                        self.start_time = timestamp1
                        breakByRecord = True
                        break
            else:
                break
        if breakByRecord:
            if self.version == 5:
                self.livox_mid70_point_cloud_array_object = _LivoxMid70PointCloudType()
                timestamp2 = self.start_time
                while True:
                    if self.started:
                        timeSinceStart = timestamp2 - self.start_time
                        if timeSinceStart <= self.wait_seconds:
                            if select.select([self.receive_socket], [], [], 0)[0]:
                                data_pc, addr = self.receive_socket.recvfrom(1500)
                                timestamp_type = int.from_bytes(data_pc[8:9], byteorder='little')
                                timestamp2 = self.get_time_stamp(data_pc[10:18], timestamp_type)
                                self.update_status(data_pc[4:8])
                        else:
                            self.start_time = timestamp2
                            break
                    else:
                        break
                if self.show_log:
                    Logger.info(f"{self.lidar_ip} CAPTURING DATA")
                # 126230400 一年的秒数
                if self.duration != 126230400:
                    if self.firmware_type == 1:
                        self.duration += (0.001 * (self.duration / 2.0))
                    elif self.firmware_type == 2:
                        self.duration += (0.0005 * (self.duration / 2.0))
                    elif self.firmware_type == 3:
                        self.duration += (0.00055 * (self.duration / 2.0))
                    elif self.firmware_type == 4:
                        self.duration += (0.0005 * (self.duration / 2.0))
                timestamp_sec = self.start_time

                while True:
                    if self.started:
                        timeSinceStart = timestamp_sec - self.start_time
                        if timeSinceStart <= self.duration:
                            if select.select([self.receive_socket], [], [], 0)[0]:
                                data_pc, addr = self.receive_socket.recvfrom(1500)
                                """
                                # version = int.from_bytes(data_pc[0:1], byteorder='little')
                                # slot_id = int.from_bytes(data_pc[1:2], byteorder='little')
                                # lidar_id = int.from_bytes(data_pc[2:3], byteorder='little')
                                """
                                self.update_status(data_pc[4:8])
                                timestamp_type = int.from_bytes(data_pc[8:9], byteorder='little')
                                timestamp_sec = self.get_time_stamp(data_pc[10:18], timestamp_type)
                                bytePos = 18
                                # Mid70 Device
                                if self.firmware_type == 4:
                                    if self.dataType == 2:
                                        buffer = []
                                        for i in range(0, 96):
                                            returnNum = 1
                                            # X coordinate
                                            x = data_pc[bytePos:bytePos + 4]
                                            bytePos += 4
                                            # Y coordinate
                                            y = data_pc[bytePos:bytePos + 4]
                                            bytePos += 4
                                            # Z coordinate
                                            z = data_pc[bytePos:bytePos + 4]
                                            bytePos += 4
                                            # intensity
                                            intensity = data_pc[bytePos:bytePos + 1]
                                            bytePos += 1
                                            # tags is no need for now
                                            # tag = data_pc[bytePos:bytePos + 1]
                                            bytePos += 1
                                            zeroORtwo = i % 2
                                            # timestamp
                                            timestamp_sec += float(not zeroORtwo) * 0.00001
                                            # return number
                                            returnNum += zeroORtwo * 1
                                            # 数据正则化
                                            x = round(float(struct.unpack('<i', x)[0]) / 1000.0, 3)
                                            y = round(float(struct.unpack('<i', y)[0]) / 1000.0, 3)
                                            z = round(float(struct.unpack('<i', z)[0]) / 1000.0, 3)
                                            intensity = str(float(int.from_bytes(intensity, byteorder='little')))
                                            self.livox_mid70_point_cloud_array_object.x.append(x)
                                            self.livox_mid70_point_cloud_array_object.y.append(y)
                                            self.livox_mid70_point_cloud_array_object.z.append(z)
                                            self.livox_mid70_point_cloud_array_object.intensities.append(intensity)
                                            buffer.append([x, y, z, 1])
                                        self.depth_image.append(self.xyz2uvd(buffer))
                        else:
                            self.started = False
                            self.is_recording = False
                            break
                    else:
                        break

    def stop(self):
        self.started = False
        self.thread.join()

    def save_to_pcd(self):
        # 写文件句柄
        handle = open(f"{self._saved_path}/{time.strftime('%Y-%m-%d %H%M%S', time.localtime())}.pcd", 'a')
        # 得到点云点数
        point_num = len(self.livox_mid70_point_cloud_array_object.x)
        # pcd头部
        handle.write(
            '# .PCD v0.7 - Point Cloud Data file format\n'
            'VERSION 0.7\n'
            'FIELDS x y z intensity\n'
            'SIZE 4 4 4 4\n'
            'TYPE F F F F\n'
            'COUNT 1 1 1 1\n'
            f'WIDTH {point_num}\n'
            'HEIGHT 1\n'
            'VIEWPOINT 0 0 0 1 0 0 0\n'
            f'POINTS {point_num}\n'
            'DATA ascii\n'
        )
        # 写入所有点
        x = self.livox_mid70_point_cloud_array_object.x
        y = self.livox_mid70_point_cloud_array_object.y
        z = self.livox_mid70_point_cloud_array_object.z
        intensities = self.livox_mid70_point_cloud_array_object.intensities
        for i in range(point_num):
            handle.write(
                f'{str(x[i])} {str(y[i])} {str(z[i])} {intensities[i]}\n'
            )
        handle.close()

    @staticmethod
    def get_time_stamp(data_pc, timestamp_type):
        timestamp_sec = 0
        if timestamp_type == 0 or timestamp_type == 1 or timestamp_type == 4:
            timestamp_sec = round(float(struct.unpack('<Q', data_pc[0:8])[0]) / 1000000000.0, 6)
        elif timestamp_type == 3:
            """
            timestamp_year = int.from_bytes(data_pc[0:1], byteorder='little')
            timestamp_month = int.from_bytes(data_pc[1:2], byteorder='little')
            timestamp_day = int.from_bytes(data_pc[2:3], byteorder='little')
            """
            timestamp_hour = int.from_bytes(data_pc[3:4], byteorder='little')
            timestamp_sec = round(float(struct.unpack('<L', data_pc[4:8])[0]) / 1000000.0, 6)
            timestamp_sec += timestamp_hour * 3600.
        return timestamp_sec

    def update_status(self, data_pc):
        status_bits = str(bin(int.from_bytes(data_pc[0:1], byteorder='little')))[2:].zfill(8)
        status_bits += str(bin(int.from_bytes(data_pc[1:2], byteorder='little')))[2:].zfill(8)
        status_bits += str(bin(int.from_bytes(data_pc[2:3], byteorder='little')))[2:].zfill(8)
        status_bits += str(bin(int.from_bytes(data_pc[3:4], byteorder='little')))[2:].zfill(8)

        self.temp_status = int(status_bits[0:2], 2)
        self.volt_status = int(status_bits[2:4], 2)
        self.motor_status = int(status_bits[4:6], 2)
        self.dirty_status = int(status_bits[6:8], 2)
        self.firmware_status = int(status_bits[8:9], 2)
        self.pps_status = int(status_bits[9:10], 2)
        self.device_status = int(status_bits[10:11], 2)
        self.system_status = int(status_bits[30:], 2)

        if self.system_status:
            if self.show_log:
                if self.system_status == 1:
                    if self.temp_status == 1:
                        Logger.warn(f"{self.lidar_ip} WARNING: temperature")
                    if self.volt_status == 1:
                        Logger.warn(f"{self.lidar_ip} WARNING: voltage")
                    if self.motor_status == 1:
                        Logger.warn(f"{self.lidar_ip} WARNING: motor")
                    if self.dirty_status == 1:
                        Logger.warn(f"{self.lidar_ip} WARNING: dirty or blocked")
                    if self.device_status == 1:
                        Logger.warn(f"{self.lidar_ip} WARNING: approaching end of service life")
                elif self.system_status == 2:
                    if self.temp_status == 1:
                        Logger.danger(f"{self.lidar_ip} ERROR: TEMPERATURE")
                    if self.volt_status == 1:
                        Logger.danger(f"{self.lidar_ip} ERROR: VOLTAGE")
                    if self.motor_status == 1:
                        Logger.danger(f"{self.lidar_ip} ERROR: MOTOR")
                    if self.firmware_status == 1:
                        Logger.danger(f"{self.lidar_ip} ERROR: ABNORMAL FIRMWARE")

    def xyz2uvd(self, xyz):
        """
        功能函数，把雷达的直角坐标转换成像素深度图 \n
        :param xyz: 输入的雷达直角坐标，为每一帧(定义为经过wait_seconds的所有点云的[x, y, z])， 输入的类型为numpy.array
        """
        depth = (self._extrinsic @ (np.concatenate([xyz, np.ones((xyz.shape[0], 1))], axis=1).transpose())).transpose()[:,
              2]
        point_2d = cv2.projectPoints(xyz, self._rVec, self._tVec, self._cMat, self._cDif)[0].reshape(-1, 2).astype(np.int)
        # 判断投影点是否在图像内部
        inside = np.logical_and(np.logical_and(point_2d[:, 0] >= 0, point_2d[:, 0] < self._width),
                                np.logical_and(point_2d[:, 1] >= 0, point_2d[:, 1] < self._height))
        point_2d = point_2d[inside]
        depth = depth[inside]
        EventBus.get('depth_queue')['data'].push([depth, point_2d])

    def read_pcd(self, file: str):
        """
        从文件中加载PCD，支持*.pkl、*.txt、*.pcd类型文件
        """
        if '.' in file:
            _, suffix = file.split('.')
            if suffix in self.support_pcd_type:
                b = None
                if suffix == 'txt':
                    pass
                elif suffix == 'pcd':
                    pass
                elif suffix == 'pkl':
                    b = np.load(ROOT(file), allow_pickle=True)
                frame = 0
                total = len(b)
                while frame < total:
                    pcd = b[frame]
                    self.xyz2uvd(np.array(pcd))
                    frame += 1
                    time.sleep(self.wait_seconds)
            else:
                Logger.danger(f'Only support file type in {self.support_pcd_type}, but found {suffix}.')
        else:
            Logger.danger(f'Wrong PCD file format. {file}')


class LivoxLidarDriver(object):
    """
    Livox雷达驱动类 \n
    Livox Lidar Python SDK 改于： \n
    https://github.com/Livox-SDK/openpylivox \n
    Livox Lidar 系列通信协议： \n
    https://github.com/Livox-SDK/Livox-SDK/wiki/Livox-SDK-Communication-Protocol-Cn
    """
    _CMD_QUERY = bytes.fromhex(b'AA010F0000000004D70002AE8A8A7B'.decode('ascii'))
    _CMD_HEARTBEAT = bytes.fromhex(b'AA010F0000000004D7000338BA8D0C'.decode('ascii'))
    _CMD_DATA_START = bytes.fromhex(b'AA011000000000B809000401228D5307'.decode('ascii'))
    _CMD_DATA_STOP = bytes.fromhex(b'AA011000000000B809000400B4BD5470'.decode('ascii'))
    _CMD_DISCONNECT = bytes.fromhex(b'AA010F0000000004D70006B74EE77C'.decode('ascii'))
    _SPECIAL_FIRMWARE_TYPE_DICT = {"03.03.0001": 2,
                                   "03.03.0002": 3,
                                   "10.10.0001": 4}

    def __init__(self, show_log=True, duration=20, wait_seconds=0.1, without_lidar=False):
        # 积分时间
        self._duration = duration
        # 采集间隔
        self._wait_seconds = wait_seconds
        # 是否使用点云文件
        self._without_lidar = without_lidar
        # 雷达端口
        self._lidar_port = 55000
        # 主机映射端口
        self._host_port = 65000
        # 是否显示调试信息
        self.show_log = show_log
        # 点云录制标志
        self._is_recorded = False
        # 主机IP
        self._ip = ""
        # 雷达IP
        self._lidar_ip = ""
        # 雷达数据端口
        self._data_port = ""
        # 雷达控制指令端口
        self._cmd_port = ""
        # 雷达固件信息
        self._lidar_firmware = "UNKNOWN"
        # 是否连接
        self._is_connected = False
        # cmd socket
        self._cmd_socket = None
        # data socket
        self._data_socket = None
        # 心跳信号
        self._heartbeat = None
        # 点云录制流
        self._record_stream = None

    def _init_sockets(self):
        self._data_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._cmd_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._data_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._cmd_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        foundIPs, foundSerials, ipRangeCodes = self._search_livox_lidar()
        foundMatchIP = False
        for i in range(0, len(foundIPs)):
            if foundIPs[i] == self._lidar_ip:
                foundMatchIP = True
                self._serial = foundSerials[i]
                self._ipRangeCode = ipRangeCodes[i]
                break

        if not foundMatchIP:
            Logger.danger("* ERROR: specified sensor IP:Command Port cannot connect to a Livox sensor *")
            Logger.danger("* common causes are a wrong IP or the command port is being used already   *")

        return len(foundIPs)

    @staticmethod
    def _crc16(data):
        crc16 = crcmod.mkCrcFun(0x11021, rev=True, initCrc=0x4C49)
        checkSum = crc16(data)
        return checkSum

    def _crc16_from_str(self, string):
        crcDataA = bytes.fromhex(string.decode('ascii'))
        checkSum = self._crc16(crcDataA)
        strHexCheckSum = str(hex(checkSum))[2:]
        strLen = len(strHexCheckSum)
        for i in range(strLen, 4):
            strHexCheckSum = "0" + strHexCheckSum
        byte1 = strHexCheckSum[2:4]
        byte2 = strHexCheckSum[0:2]
        checkSumB = (byte1 + byte2)
        return checkSumB

    def _crc32_from_str(self, string):
        crcDataA = bytes.fromhex(string.decode('ascii'))
        checkSum = self._crc32(crcDataA)
        strHexCheckSum = str(hex(checkSum))[2:]
        strLen = len(strHexCheckSum)
        for i in range(strLen, 8):
            strHexCheckSum = "0" + strHexCheckSum
        byte1 = strHexCheckSum[6:8]
        byte2 = strHexCheckSum[4:6]
        byte3 = strHexCheckSum[2:4]
        byte4 = strHexCheckSum[0:2]
        checkSumB = (byte1 + byte2 + byte3 + byte4)
        return checkSumB

    @staticmethod
    def _crc32(data):
        crc32 = crcmod.mkCrcFun(0x104C11DB7, rev=True, initCrc=0x564F580A, xorOut=0xFFFFFFFF)
        checkSum = crc32(data)
        return checkSum

    def parse_resp(self, data):

        dataBytes = []
        dataString = ""
        dataLength = len(data)
        for i in range(0, dataLength):
            dataBytes.append(data[i:i + 1])
            dataString += (binascii.hexlify(data[i:i + 1])).decode("utf-8")

        crc16Data = b''
        for i in range(0, 7):
            crc16Data += binascii.hexlify(dataBytes[i])

        crc16DataA = bytes.fromhex(crc16Data.decode('ascii'))
        checkSum16I = self._crc16(crc16DataA)

        frame_header_checksum_crc16 = int.from_bytes((dataBytes[7] + dataBytes[8]), byteorder='little')

        cmdMessage, dataMessage, dataID, = "", "", ""
        data = []

        goodData = True

        if frame_header_checksum_crc16 == checkSum16I:

            crc32Data = b''
            for i in range(0, dataLength - 4):
                crc32Data += binascii.hexlify(dataBytes[i])

            crc32DataA = bytes.fromhex(crc32Data.decode('ascii'))
            checkSum32I = self._crc32(crc32DataA)

            frame_header_checksum_crc32 = int.from_bytes((dataBytes[dataLength - 4] + dataBytes[dataLength - 3] +
                                                          dataBytes[dataLength - 2] + dataBytes[dataLength - 1]),
                                                         byteorder='little')

            if frame_header_checksum_crc32 == checkSum32I:

                frame_sof = int.from_bytes(dataBytes[0], byteorder='little')
                frame_version = int.from_bytes(dataBytes[1], byteorder='little')
                frame_length = int.from_bytes((dataBytes[2] + dataBytes[3]), byteorder='little')

                if frame_sof == 170:
                    if frame_version == 1:
                        if frame_length <= 1400:
                            frame_cmd_type = int.from_bytes(dataBytes[4], byteorder='little')

                            cmdMessage = ""
                            if frame_cmd_type == 0:
                                cmdMessage = "CMD (request)"
                            elif frame_cmd_type == 1:
                                cmdMessage = "ACK (response)"
                            elif frame_cmd_type == 2:
                                cmdMessage = "MSG (message)"
                            else:
                                goodData = False

                            frame_data_cmd_set = int.from_bytes(dataBytes[9], byteorder='little')

                            dataMessage = ""
                            if frame_data_cmd_set == 0:
                                dataMessage = "General"
                            elif frame_data_cmd_set == 1:
                                dataMessage = "Lidar"
                            elif frame_data_cmd_set == 2:
                                dataMessage = "Hub"
                            else:
                                goodData = False

                            dataID = str(int.from_bytes(dataBytes[10], byteorder='little'))
                            data = dataBytes[11:]

                        else:
                            goodData = False
                    else:
                        goodData = False
                else:
                    goodData = False
            else:
                goodData = False
                if self.show_log:
                    Logger.danger("CRC32 Checksum Error")
        else:
            goodData = False
            if self.show_log:
                Logger.danger("CRC16 Checksum Error")

        return goodData, cmdMessage, dataMessage, dataID, data

    def _info(self, data):

        goodData, cmdMessage, dataMessage, dataID, dataBytes = self.parse_resp(data)
        device_serial, typeMessage = "", ""
        ipRangeCode = 0
        if goodData:
            if cmdMessage == "MSG (message)" and dataMessage == "General" and dataID == "0":
                device_broadcast_code = ""
                for i in range(0, 16):
                    device_broadcast_code += dataBytes[i].decode('ascii')
                ipRangeCode = int(device_broadcast_code[14:15])
                device_serial = device_broadcast_code[:-2]
                device_type = int.from_bytes(dataBytes[16], byteorder='little')
                typeMessage = ""
                if device_type == 0:
                    typeMessage = "Hub"
                elif device_type == 1:
                    typeMessage = "Mid-40"
                elif device_type == 2:
                    typeMessage = "Tele-15"
                elif device_type == 3:
                    typeMessage = "Horizon"
                elif device_type == 6:
                    typeMessage = "Mid-70"

        return goodData, cmdMessage, dataMessage, device_serial, typeMessage, ipRangeCode

    @staticmethod
    def _check_ip(ip):
        IPclean = ""
        if ip:
            parts = ip.split(".")
            if len(parts) == 4:
                for i in range(0, 4):
                    try:
                        IPint = int(parts[i])
                        if 0 <= IPint <= 254:
                            IPclean += str(IPint)
                            if i < 3:
                                IPclean += "."
                        else:
                            IPclean = ""
                            break
                    except RuntimeError:
                        IPclean = ""
                        break
        return IPclean

    @staticmethod
    def _check_port(port):
        try:
            portNum = int(port)
            if 0 <= portNum <= 65535:
                pass
            else:
                portNum = -1
        except RuntimeError:
            portNum = -1
        return portNum

    def _bind_ports(self):
        try:
            self._data_socket.bind((self._ip, self._data_port))
            self._cmd_socket.bind((self._ip, self._cmd_port))
            assignedDataPort = self._data_socket.getsockname()[1]
            assignedCmdPort = self._cmd_socket.getsockname()[1]
            time.sleep(0.1)
            return assignedDataPort, assignedCmdPort
        except socket.error as err:
            Logger.danger("Cannot bind to specified IP:Port(s), " + err)

    def _wait_idle(self):
        while self._heartbeat.idle_state != 9:
            time.sleep(0.1)

    def _query(self):
        self._wait_idle()
        self._cmd_socket.sendto(self._CMD_QUERY, (self._lidar_ip, self._host_port))
        if select.select([self._cmd_socket], [], [], 0.1)[0]:
            binData, addr = self._cmd_socket.recvfrom(20)
            _, ack, cmd_set, cmd_id, ret_code_bin = self.parse_resp(binData)
            if ack == "ACK (response)" and cmd_set == "General" and cmd_id == "2":
                ret_code = int.from_bytes(ret_code_bin[0], byteorder='little')
                if ret_code == 1:
                    if self.show_log:
                        Logger.danger(f"{self._lidar_ip} is FAILED to receive query results")
                elif ret_code == 0:
                    AA = str(int.from_bytes(ret_code_bin[1], byteorder='little')).zfill(2)
                    BB = str(int.from_bytes(ret_code_bin[2], byteorder='little')).zfill(2)
                    CC = str(int.from_bytes(ret_code_bin[3], byteorder='little')).zfill(2)
                    DD = str(int.from_bytes(ret_code_bin[4], byteorder='little')).zfill(2)
                    self._lidar_firmware = AA + "." + BB + "." + CC + DD
            else:
                if self.show_log:
                    Logger.danger(f"{self._lidar_ip} is incorrect query response")

    def _auto_get_host(self):
        try:
            hostname = socket.gethostname()
            self._ip = socket.gethostbyname(hostname)
        except RuntimeError:
            self._ip = ""

    def _search_livox_lidar(self):
        serverSock_INIT = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serverSock_INIT.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serverSock_INIT.bind(("0.0.0.0", self._lidar_port))
        foundDevice = select.select([serverSock_INIT], [], [], 1)[0]
        IPs = []
        Serials = []
        ipRangeCodes = []
        if foundDevice:
            while True:
                data, addr = serverSock_INIT.recvfrom(34)
                if len(addr) == 2:
                    if addr[1] == self._host_port:
                        if len(IPs) == 0:
                            goodData, cmdMessage, dataMessage, device_serial, typeMessage, ipRangeCode = self._info(
                                data)
                            if typeMessage == "Mid-70":
                                IPs.append(self._check_ip(addr[0]))
                                Serials.append(device_serial)
                                ipRangeCodes.append(ipRangeCode)
                        else:
                            existsAlready = False
                            for i in range(0, len(IPs)):
                                if addr[0] == IPs[i]:
                                    existsAlready = True
                            if existsAlready:
                                break
                            else:
                                goodData, cmdMessage, dataMessage, device_serial, typeMessage, ipRangeCode = self._info(
                                    data)
                                if typeMessage == "Mid-70":
                                    IPs.append(self._check_ip(addr[0]))
                                    Serials.append(device_serial)
                                    ipRangeCodes.append(ipRangeCode)
                else:
                    if self.show_log:
                        Logger.danger(f"Unknown address found in {addr}")
                break
        serverSock_INIT.close()
        time.sleep(0.2)
        if self.show_log:
            for i in range(0, len(IPs)):
                Logger.info(f"Found Mid-70 w. serial #{Serials[i]} at IP: {IPs[i]}")
        return IPs, Serials, ipRangeCodes

    def _connect(self, ip, lidar_ip, data_port, cmd_port):
        lidar_num = 0
        if not self._is_connected:
            self._ip = self._check_ip(ip)
            self._lidar_ip = self._check_ip(lidar_ip)
            self._data_port = self._check_port(data_port)
            self._cmd_port = self._check_port(cmd_port)
            if self._ip and self._lidar_ip and self._data_port != -1 and self._cmd_port != -1:
                lidar_num = self._init_sockets()
                time.sleep(0.1)
                self._data_port, self._cmd_port = self._bind_ports()
                IP_parts = self._ip.split(".")
                IP_hex = str(hex(int(IP_parts[0]))).replace('0x', '').zfill(2)
                IP_hex += str(hex(int(IP_parts[1]))).replace('0x', '').zfill(2)
                IP_hex += str(hex(int(IP_parts[2]))).replace('0x', '').zfill(2)
                IP_hex += str(hex(int(IP_parts[3]))).replace('0x', '').zfill(2)
                dataHexAll = str(hex(int(self._data_port))).replace('0x', '').zfill(4)
                dataHex = dataHexAll[2:] + dataHexAll[:-2]
                cmdHexAll = str(hex(int(self._cmd_port))).replace('0x', '').zfill(4)
                cmdHex = cmdHexAll[2:] + cmdHexAll[:-2]
                cmdString = "aa01170000000064390001" + IP_hex + dataHex + cmdHex
                binString = bytes(cmdString, encoding='utf-8')
                crc32checksum = self._crc32_from_str(binString)
                cmdString += crc32checksum
                binString = bytes(cmdString, encoding='utf-8')
                connect_request = bytes.fromhex(binString.decode('ascii'))
                self._cmd_socket.sendto(connect_request, (self._lidar_ip, self._host_port))
                if select.select([self._cmd_socket], [], [], 0.1)[0]:
                    binData, addr = self._cmd_socket.recvfrom(16)
                    _, ack, cmd_set, cmd_id, ret_code_bin = self.parse_resp(binData)
                    if ack == "ACK (response)" and cmd_set == "General" and cmd_id == "1":
                        ret_code = int.from_bytes(ret_code_bin[0], byteorder='little')
                        if ret_code == 0:
                            self._is_connected = True
                            self._heartbeat = _LivoxLidarHeartbeatThread(1, self._cmd_socket, self._lidar_ip,
                                                                         self._host_port,
                                                                         self._CMD_HEARTBEAT, self.show_log)
                            time.sleep(0.15)
                            self._query()
                            if self.show_log:
                                Logger.info(f"Connected to Mid-70 at IP: {self._lidar_ip}, F/W: {self._lidar_firmware}")
                        else:
                            if self.show_log:
                                Logger.danger(f"FAILED to connect to Mid-70 at IP: {self._lidar_ip}")
                    else:
                        if self.show_log:
                            Logger.danger(f"FAILED to connect to Mid-70 at IP: {self._lidar_ip}")
            else:
                if self.show_log:
                    Logger.danger("Invalid connection parameter(s)")
        else:
            if self.show_log:
                Logger.danger(f"FAILED to connect to Mid-70 at IP: {self._lidar_ip}")
        return lidar_num

    def connect(self, ip=""):
        """
        :param ip: 主机端口，若不填则认为采取自动获取
        """
        lidar_num = 0
        if not ip:
            self._auto_get_host()
        else:
            self._ip = ip
        if self._ip:
            if self.show_log:
                Logger.info(f"Using IP address:{self._ip}.")
            lidar_ips, _, _ = self._search_livox_lidar()
            if len(lidar_ips) > 0:
                if self.show_log:
                    Logger.info(f'Attempting to connect lidar at IP: {lidar_ips[0]}')
                lidar_num = self._connect(self._ip, lidar_ips[0], 0, 0)
                if lidar_num > 0 and self.show_log:
                    Logger.info(f"Connected to lidar at IP: {self._lidar_ip}, F/W: {self._lidar_firmware}")
                else:
                    if self.show_log:
                        Logger.danger(f"No lidar device connected")
            else:
                if self.show_log:
                    Logger.danger(f"No lidar ip(s) available")
        else:
            if self.show_log:
                Logger.danger(f"No lidar device available")
        return lidar_num

    def start_record(self):
        """
        开启点云录制
        """
        if self._is_connected:
            if not self._is_recorded:
                firmwareType = 0
                if self._lidar_firmware != "UNKNOWN":
                    firmwareType = self._SPECIAL_FIRMWARE_TYPE_DICT[self._lidar_firmware]
                self._record_stream = _LivoxPointCloudRecordThread(self._lidar_ip, self._data_socket,
                                                                   self._wait_seconds, self._duration,
                                                                   firmwareType, self.show_log, self._without_lidar)
                time.sleep(0.15)
                self._record_stream.is_recording = True
                self._wait_idle()
                self._cmd_socket.sendto(self._CMD_DATA_START, (self._lidar_ip, self._host_port))
                if self.show_log:
                    Logger.info(f"{self._lidar_ip} sent start data stream request")
                if select.select([self._cmd_socket], [], [], 0.1)[0]:
                    binData, addr = self._cmd_socket.recvfrom(16)
                    _, ack, cmd_set, cmd_id, ret_code_bin = self.parse_resp(binData)
                    if ack == "ACK (response)" and cmd_set == "General" and cmd_id == "4":
                        ret_code = int.from_bytes(ret_code_bin[0], byteorder='little')
                        if ret_code == 1:
                            if self.show_log:
                                Logger.danger(f"{self._lidar_ip} FAILED to start data stream")
                            if self._record_stream is not None:
                                self._record_stream.stop()
                            time.sleep(0.1)
                            self._is_recorded = False
                        else:
                            self._is_recorded = True
                    else:
                        if self.show_log:
                            Logger.danger(f"{self._lidar_ip} incorrect start data stream response")
            else:
                if self.show_log:
                    Logger.danger(f"{self._lidar_ip} data stream already started")
        else:
            if self.show_log:
                Logger.danger(f"Not connected to Mid-70 sensor at IP: {self._lidar_ip}")

    def stop_record(self):
        """
        关闭点云录制
        """
        if self._is_connected:
            self._wait_idle()
            self._cmd_socket.sendto(self._CMD_DATA_STOP, (self._lidar_ip, self._host_port))
            if self.show_log:
                Logger.info(f"{self._lidar_ip} sent stop data stream request")
            if select.select([self._cmd_socket], [], [], 0.1)[0]:
                binData, addr = self._cmd_socket.recvfrom(16)
                _, ack, cmd_set, cmd_id, ret_code_bin = self.parse_resp(binData)
                if ack == "ACK (response)" and cmd_set == "General" and cmd_id == "4":
                    ret_code = int.from_bytes(ret_code_bin[0], byteorder='little')
                    if ret_code == 1:
                        if self.show_log:
                            Logger.danger(f"{self._lidar_ip} FAILED to stop data stream")
                    else:
                        if self._record_stream is not None:
                            self._record_stream.stop()
                            Logger.info('Start to save to PCD')
                            self._record_stream.save_to_pcd()
                            Logger.info('Stop to save to PCD')
                            self._record_stream = None
                else:
                    if self.show_log:
                        Logger.danger(f"{self._lidar_ip} incorrect stop data stream response")
            else:
                if self.show_log:
                    Logger.danger(f"{self._lidar_ip} data stream already stopped")
        else:
            Logger.danger(f"Not connected to Mid-70 sensor at IP: {self._lidar_ip}")

    def disconnect(self):
        """
        关闭设备
        """
        if self._is_connected:
            self._is_connected = False
            if self._record_stream is not None:
                self._record_stream.stop()
                self._record_stream = None
            try:
                self._disconnect_device()
                self._heartbeat.stop()
                time.sleep(0.2)
                self._heartbeat = None
                self._data_socket.close()
                self._cmd_socket.close()
                if self.show_log:
                    Logger.info(f"Disconnected from Mid-70 sensor at IP: {self._lidar_ip}")
            except RuntimeError:
                if self.show_log:
                    Logger.danger(f"Error trying to disconnect from Mid-70 sensor at IP: {self._lidar_ip}")
        else:
            if self.show_log:
                Logger.danger(f"Not connected to Mid-70 sensor at IP: {self._lidar_ip}")

    def _disconnect_device(self):
        self._wait_idle()
        self._cmd_socket.sendto(self._CMD_DISCONNECT, (self._lidar_ip, self._host_port))
        if select.select([self._cmd_socket], [], [], 0.1)[0]:
            binData, addr = self._cmd_socket.recvfrom(16)
            _, ack, cmd_set, cmd_id, ret_code_bin = self.parse_resp(binData)
            if ack == "ACK (response)" and cmd_set == "General" and cmd_id == "6":
                ret_code = int.from_bytes(ret_code_bin[0], byteorder='little')
                if ret_code == 1:
                    if self.show_log:
                        Logger.danger(f"{self._lidar_ip} FAILED to disconnect")
            else:
                if self.show_log:
                    Logger.danger(f"{self._lidar_ip} incorrect disconnect response")

    def save_point_cloud_to_pcd(self, path):
        """
        保留录制的点云到PCD文件
        :param path: PCD文件路径
        """
        if self._record_stream:
            Logger.info(f"{self._lidar_ip} start to saved to path {path}")
            self._record_stream.saved_path = path
            self._record_stream.is_saved = True
        else:
            Logger.danger(f"{self._lidar_ip} is not start to record")

    def stop_point_cloud_to_pcd(self):
        """
        停止保存点云
        """
        if self._record_stream and self._record_stream.is_saved:
            Logger.info(f"{self._lidar_ip} finish to save")
            self._record_stream.is_saved = False
        else:
            Logger.danger(f"{self._lidar_ip} is not start to record")

    def _xyz2uv(self):
        pass

    def load_pcd_file(self):
        thread = _LivoxPointCloudRecordThread(without_lidar=self._without_lidar, wait_seconds=0.1)
        thread.run()

# EventBus.start()
# EventBus.read_config_file()
# driver = LivoxLidarDriver()
# connect = driver.connect()
# if connect != 0:
#     driver.start_record()
#     time.sleep(20)
#     driver.stop_record()
#     driver.disconnect()
