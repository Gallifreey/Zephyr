import ctypes
import threading

import cv2
import numpy as np


class Singleton(object):
    """
    单例类
    """
    _lock_lock = threading.RLock()
    _lock = None
    _instance = None
    _is_shared = None

    def __new__(cls, *args, **kwargs):
        assert not kwargs.get("shared", False) or (len(args) + len(kwargs)) == 0, (
            "Cannot use constructor arguments when accessing a Singleton without "
            "specifying shared=False."
        )
        if not cls._instance:
            if cls._lock is None:
                with cls._lock_lock:
                    if cls._lock is None:
                        cls._lock = threading.RLock()
            if not cls._instance:
                with cls._lock:
                    if not cls._instance:
                        cls._instance = object.__new__(cls)
                        cls._instance.__init__()
                        cls.__init__ = lambda *args, **kwargs: None

        return cls._instance

    def __init__(self, *args, **kwargs):
        shared = kwargs.pop("shared", True)
        with self:
            if shared:
                assert (
                        type(self)._is_shared is not False
                ), "Cannot access a non-shared Singleton."
                type(self)._is_shared = True
            else:
                assert type(self)._is_shared is None, "Singleton is already created."

    def __enter__(self):
        type(self)._lock.acquire()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        type(self)._lock.release()

    def share(self):
        type(self)._is_shared = True


class ThreadSafeSingleton(Singleton):
    """
    线程安全的单例类
    """
    threadsafe_attrs = frozenset()
    readonly_attrs = frozenset()

    def __init__(self, *args, **kwargs):
        super(ThreadSafeSingleton, self).__init__(*args, **kwargs)
        type(self).readonly_attrs = set(type(self).readonly_attrs)

    @staticmethod
    def assert_locked(self):
        lock = type(self)._lock
        assert lock.acquire(blocking=False), (
            "ThreadSafeSingleton accessed without locking. Either use with-statement, "
            "or if it is a method or property, mark it as @threadsafe_method or with "
            "@auto_locked_method, as appropriate."
        )
        lock.release()

    def __getattribute__(self, name):
        value = object.__getattribute__(self, name)
        if name not in (type(self).threadsafe_attrs | type(self).readonly_attrs):
            if not getattr(value, "is_threadsafe_method", False):
                ThreadSafeSingleton.assert_locked(self)
        return value

    def __setattr__(self, name, value):
        assert name not in type(self).readonly_attrs, "This attribute is read-only."
        if name not in type(self).threadsafe_attrs:
            ThreadSafeSingleton.assert_locked(self)
        return object.__setattr__(self, name, value)


def get_from_element(e, t):
    """
    返回目标中找到含元素e的列表
    """
    for i in t:
        if e in i:
            return i
    return None


def draw_rec(img, p):
    for p_ in p:
        img = cv2.rectangle(img, (int(p_[0]), int(p_[1])), (int(p_[2]), int(p_[3])), color=(0, 0, 255), thickness=8)
    return img


def get_bbox_from_label(label: int, data: list):
    """
    从data中找到符合label的bbox数组
    :param label: 标签
    :param data: 数据
    :return: 返回符合条件的bbox数组
    """
    res = []
    for d in data:
        if d[0] == label:
            res.append(d)
    return res


def get_max_conf_bbox(bbox):
    """
    获得bbox中置信度最大的armor
    """
    conf = -1
    res = None
    for b in bbox:
        if conf < b[-1]:
            conf = b[-1]
            res = b
    return res


def get_max_item_from_dict(dic: dict):
    t = None
    v_ = -1
    for k, v in dic.items():
        if v_ < k:
            v_ = k
            t = v
    return t


def get_data_from_list(pos: int, data: list, target):
    """
    用于返回获取列表在pos位置上相同的元素
    :param pos: 位置
    :param data: 列表
    :param target: 目标元素
    :return: 结果数组
    """
    res = []
    for d in data:
        if d[pos] == target:
            res.append(d)
    return res


def is_none(target):
    return isinstance(target, type(None))


def get_values_from_two_dict(d1: dict, d2: dict):
    """
    从d2字典中获取与d1字典相同键的值，并结果返回顺序一致的列表
    :param d1: 根字典
    :param d2: 目标字典
    :return: 返回的列表
    """
    res = []
    for k in d1.keys():
        res.append(d2[k])
    return list(d1.values()), res


def pnp(points, objects, k0, c0):
    """
    PNP获取相机外参
    :param points: 相机视野标定点坐标， 格式：[{label: 'R1', point: [0, 0]}, ...]
    :param objects: 世界坐标， 格式：[{label: 'R1', point: [0, 0]}, ...]
    :param k0: 相机内参
    :param c0: 相机畸变
    :return: 旋转向量、平移向量
    """
    p, obp = get_values_from_two_dict(points, objects)
    obp = np.float64([[p] for p in obp])
    pick_point = np.float64(p).reshape(-1, 1, 2)
    _, rvec, tvec = cv2.solvePnP(obp, pick_point, np.float32(k0).reshape(3, 3), np.float32(c0), flags=cv2.SOLVEPNP_P3P)
    return rvec, tvec


def pnp2pose(rvec, tvec):
    """
    获取相机位姿
    :param rvec: PNP-旋转向量
    :param tvec: PNP-平移向量
    :return: 相机到世界的变换矩阵，相机位于世界的坐标
    """
    T = np.eye(4)
    T[:3, :3] = cv2.Rodrigues(rvec)[0]
    T[:3, 3] = tvec.reshape(-1)
    T = np.linalg.inv(T)
    return T, (T @ (np.array([0, 0, 0, 1])))[:3]


def numpy2list_in_dict(d: dict):
    for k, v in d.items():
        d[k] = list(v)
    return d


def normalize_dict(d: dict, ratio):
    for k, v in d.items():
        d[k][0] = v[0] * ratio[0]
        d[k][1] = v[1] * ratio[1]
    return d


def regen_list_from_keys(target: dict, keys: list):
    """
    从字典中抽取目标键值成数组
    :param target: 目标字典
    :param keys: 键值
    :return: 数组
    """
    t = []
    for k in keys:
        t.append(target[k])
    return t


class DepthQueue(object):
    def __init__(self, maxsize=1):
        """
        :param maxsize: 队列最大容量
        """
        self.__maxsize = maxsize
        self.__size = None
        self.__k0 = None
        self.__c0 = None
        self.__e0 = None
        self.__current = 0
        self.__queue = []
        self.__depth = None

    def set(self, k0, c0, e0, size):
        self.__size = size
        self.__k0 = k0
        self.__c0 = c0
        self.__e0 = e0
        self.__depth = np.ones((size[0], size[1]), np.float64) * np.nan

    def get(self):
        return self.__queue[self.__current]

    def pop(self):
        top = self.get()
        self.__current -= 1
        del self.__queue[0]
        return top

    def empty(self):
        return self.__current == 0

    def full(self):
        return self.__current == (self.__maxsize - 1)

    def push(self, a):
        """
        向深度队列入队
        :param a: [depth, point_2d]
        """
        if self.full():
            ip_d, _ = self.pop()
            self.__depth[ip_d[:, 1], ip_d[:, 0]] = np.nan
        self.__queue.append(a)
        self.__current += 1
        dpt, ip = a
        s = np.stack([self.__depth[ip[:, 1], ip[:, 0]], dpt], axis=1)
        s = np.nanmin(s, axis=1)
        self.__depth[ip[:, 1], ip[:, 0]] = s

    def get_from_index(self, index):
        assert 0 <= index <= self.__maxsize - 1
        return self.__queue[index]

    def get_full_queue(self):
        return self.__queue

    def get_depth(self):
        return self.__depth

    def get_armor_depth(self, armors):
        """
        根据armors确定到armor的距离
        :param armors: armor列表，[[cls, bbox, (conf)], ...]
        :return: [[cls, depth], ...]
        """
        res = []
        if len(armors) == 0:
            return

        def xyxy2c(p):
            return np.float32([p[0] + (p[2] / 2), p[1] + (p[3] / 2)])

        def xyxy2xywh(p):
            return [p[0], p[1], abs(p[2] - p[0]), abs(p[3] - p[1])]

        for armor in armors:
            cls, bbox = armor[0], xyxy2xywh(armor[1])
            c = xyxy2c(bbox)
            area = self.__depth[int(max(0, c[1] - bbox[3])):int(min(c[1] + bbox[3], self.__size[0] - 1)),
                   int(max(c[0] - bbox[2], 0)):int(min(c[0] + bbox[2], self.__size[1] - 1))]
            z = np.nanmean(area) if not np.isnan(area).all() else np.nan
            res.append([cls, np.concatenate([cv2.undistortPoints(c, self.__k0, self.__c0).reshape(-1), np.array([z])],
                                            axis=0)])
        return np.stack(res, axis=0)


# 绘制
RED = (0, 0, 255)
BLUE = (255, 0, 0)

# 裁判系统校验
CRC8_INIT = 0xff
CRC8_TABLE = [0x00, 0x5e, 0xbc, 0xe2, 0x61, 0x3f, 0xdd, 0x83, 0xc2, 0x9c, 0x7e, 0x20, 0xa3, 0xfd, 0x1f, 0x41,
              0x9d, 0xc3, 0x21, 0x7f, 0xfc, 0xa2, 0x40, 0x1e, 0x5f, 0x01, 0xe3, 0xbd, 0x3e, 0x60, 0x82, 0xdc,
              0x23, 0x7d, 0x9f, 0xc1, 0x42, 0x1c, 0xfe, 0xa0, 0xe1, 0xbf, 0x5d, 0x03, 0x80, 0xde, 0x3c, 0x62,
              0xbe, 0xe0, 0x02, 0x5c, 0xdf, 0x81, 0x63, 0x3d, 0x7c, 0x22, 0xc0, 0x9e, 0x1d, 0x43, 0xa1, 0xff,
              0x46, 0x18, 0xfa, 0xa4, 0x27, 0x79, 0x9b, 0xc5, 0x84, 0xda, 0x38, 0x66, 0xe5, 0xbb, 0x59, 0x07,
              0xdb, 0x85, 0x67, 0x39, 0xba, 0xe4, 0x06, 0x58, 0x19, 0x47, 0xa5, 0xfb, 0x78, 0x26, 0xc4, 0x9a,
              0x65, 0x3b, 0xd9, 0x87, 0x04, 0x5a, 0xb8, 0xe6, 0xa7, 0xf9, 0x1b, 0x45, 0xc6, 0x98, 0x7a, 0x24,
              0xf8, 0xa6, 0x44, 0x1a, 0x99, 0xc7, 0x25, 0x7b, 0x3a, 0x64, 0x86, 0xd8, 0x5b, 0x05, 0xe7, 0xb9,
              0x8c, 0xd2, 0x30, 0x6e, 0xed, 0xb3, 0x51, 0x0f, 0x4e, 0x10, 0xf2, 0xac, 0x2f, 0x71, 0x93, 0xcd,
              0x11, 0x4f, 0xad, 0xf3, 0x70, 0x2e, 0xcc, 0x92, 0xd3, 0x8d, 0x6f, 0x31, 0xb2, 0xec, 0x0e, 0x50,
              0xaf, 0xf1, 0x13, 0x4d, 0xce, 0x90, 0x72, 0x2c, 0x6d, 0x33, 0xd1, 0x8f, 0x0c, 0x52, 0xb0, 0xee,
              0x32, 0x6c, 0x8e, 0xd0, 0x53, 0x0d, 0xef, 0xb1, 0xf0, 0xae, 0x4c, 0x12, 0x91, 0xcf, 0x2d, 0x73,
              0xca, 0x94, 0x76, 0x28, 0xab, 0xf5, 0x17, 0x49, 0x08, 0x56, 0xb4, 0xea, 0x69, 0x37, 0xd5, 0x8b,
              0x57, 0x09, 0xeb, 0xb5, 0x36, 0x68, 0x8a, 0xd4, 0x95, 0xcb, 0x29, 0x77, 0xf4, 0xaa, 0x48, 0x16,
              0xe9, 0xb7, 0x55, 0x0b, 0x88, 0xd6, 0x34, 0x6a, 0x2b, 0x75, 0x97, 0xc9, 0x4a, 0x14, 0xf6, 0xa8,
              0x74, 0x2a, 0xc8, 0x96, 0x15, 0x4b, 0xa9, 0xf7, 0xb6, 0xe8, 0x0a, 0x54, 0xd7, 0x89, 0x6b, 0x35]

CRC16_INIT = 0xffff
CRC16_TABLE = [0x0000, 0x1189, 0x2312, 0x329b, 0x4624, 0x57ad, 0x6536, 0x74bf,
               0x8c48, 0x9dc1, 0xaf5a, 0xbed3, 0xca6c, 0xdbe5, 0xe97e, 0xf8f7,
               0x1081, 0x0108, 0x3393, 0x221a, 0x56a5, 0x472c, 0x75b7, 0x643e,
               0x9cc9, 0x8d40, 0xbfdb, 0xae52, 0xdaed, 0xcb64, 0xf9ff, 0xe876,
               0x2102, 0x308b, 0x0210, 0x1399, 0x6726, 0x76af, 0x4434, 0x55bd,
               0xad4a, 0xbcc3, 0x8e58, 0x9fd1, 0xeb6e, 0xfae7, 0xc87c, 0xd9f5,
               0x3183, 0x200a, 0x1291, 0x0318, 0x77a7, 0x662e, 0x54b5, 0x453c,
               0xbdcb, 0xac42, 0x9ed9, 0x8f50, 0xfbef, 0xea66, 0xd8fd, 0xc974,
               0x4204, 0x538d, 0x6116, 0x709f, 0x0420, 0x15a9, 0x2732, 0x36bb,
               0xce4c, 0xdfc5, 0xed5e, 0xfcd7, 0x8868, 0x99e1, 0xab7a, 0xbaf3,
               0x5285, 0x430c, 0x7197, 0x601e, 0x14a1, 0x0528, 0x37b3, 0x263a,
               0xdecd, 0xcf44, 0xfddf, 0xec56, 0x98e9, 0x8960, 0xbbfb, 0xaa72,
               0x6306, 0x728f, 0x4014, 0x519d, 0x2522, 0x34ab, 0x0630, 0x17b9,
               0xef4e, 0xfec7, 0xcc5c, 0xddd5, 0xa96a, 0xb8e3, 0x8a78, 0x9bf1,
               0x7387, 0x620e, 0x5095, 0x411c, 0x35a3, 0x242a, 0x16b1, 0x0738,
               0xffcf, 0xee46, 0xdcdd, 0xcd54, 0xb9eb, 0xa862, 0x9af9, 0x8b70,
               0x8408, 0x9581, 0xa71a, 0xb693, 0xc22c, 0xd3a5, 0xe13e, 0xf0b7,
               0x0840, 0x19c9, 0x2b52, 0x3adb, 0x4e64, 0x5fed, 0x6d76, 0x7cff,
               0x9489, 0x8500, 0xb79b, 0xa612, 0xd2ad, 0xc324, 0xf1bf, 0xe036,
               0x18c1, 0x0948, 0x3bd3, 0x2a5a, 0x5ee5, 0x4f6c, 0x7df7, 0x6c7e,
               0xa50a, 0xb483, 0x8618, 0x9791, 0xe32e, 0xf2a7, 0xc03c, 0xd1b5,
               0x2942, 0x38cb, 0x0a50, 0x1bd9, 0x6f66, 0x7eef, 0x4c74, 0x5dfd,
               0xb58b, 0xa402, 0x9699, 0x8710, 0xf3af, 0xe226, 0xd0bd, 0xc134,
               0x39c3, 0x284a, 0x1ad1, 0x0b58, 0x7fe7, 0x6e6e, 0x5cf5, 0x4d7c,
               0xc60c, 0xd785, 0xe51e, 0xf497, 0x8028, 0x91a1, 0xa33a, 0xb2b3,
               0x4a44, 0x5bcd, 0x6956, 0x78df, 0x0c60, 0x1de9, 0x2f72, 0x3efb,
               0xd68d, 0xc704, 0xf59f, 0xe416, 0x90a9, 0x8120, 0xb3bb, 0xa232,
               0x5ac5, 0x4b4c, 0x79d7, 0x685e, 0x1ce1, 0x0d68, 0x3ff3, 0x2e7a,
               0xe70e, 0xf687, 0xc41c, 0xd595, 0xa12a, 0xb0a3, 0x8238, 0x93b1,
               0x6b46, 0x7acf, 0x4854, 0x59dd, 0x2d62, 0x3ceb, 0x0e70, 0x1ff9,
               0xf78f, 0xe606, 0xd49d, 0xc514, 0xb1ab, 0xa022, 0x92b9, 0x8330,
               0x7bc7, 0x6a4e, 0x58d5, 0x495c, 0x3de3, 0x2c6a, 0x1ef1, 0x0f78]


def get_crc8_check_sum(message, length, crc8):
    message = ctypes.cast(message, ctypes.py_object).value
    tmp = 0
    while length > 0:
        length = length - 1
        ucIndex = crc8 ^ message[tmp]
        tmp += 1
        crc8 = CRC8_TABLE[ucIndex]
    return crc8


def get_crc16_check_sum(message, length, crc16):
    message = ctypes.cast(message, ctypes.py_object).value
    if message == 0:
        return 0xFFFF
    tmp = 0
    while length:
        length -= 1
        chData = message[tmp]
        tmp += 1
        crc16 = (crc16 >> 8) ^ CRC16_TABLE[(crc16 ^ chData) & 0x00ff]
    return crc16


def append_crc16_check_sum(message, length):
    message = ctypes.cast(message, ctypes.py_object).value
    if message == 0 or length <= 2:
        return
    CRC = get_crc16_check_sum(message, length - 2, CRC16_INIT)
    message[length - 2] = (CRC & 0x00ff)
    message[length - 1] = ((CRC > 8) & 0x00ff)


# 标定
def find_board(img, board_w=9, board_h=6, board_eps=18.1, max_it=30, max_err=0.001):
    """
    找标定板函数
    """
    # 找棋盘格角点
    # 设置寻找亚像素角点的参数，采用的停止准则是最大循环次数30和最大误差容限0.001
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, max_it, max_err)  # 阈值
    # 棋盘格模板规格
    w = board_w
    h = board_h
    objp = np.zeros((w * h, 3), np.float32)
    objp[:, :2] = np.mgrid[0:w, 0:h].T.reshape(-1, 2)
    objp = objp * board_eps
    # 储存棋盘格角点的世界坐标和图像坐标对
    obj_points = []  # 在世界坐标系中的三维点
    img_points = []  # 在图像平面的二维点
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 找到棋盘格角点
    ret, corners = cv2.findChessboardCorners(gray, (w, h), None)
    # 如果找到足够点对，将其存储起来
    if ret:
        # 在原角点的基础上寻找亚像素角点
        cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        # 追加进入世界三维点和平面二维点中
        obj_points.append(objp)
        img_points.append(corners)
        # 将角点在图像上显示
        cv2.drawChessboardCorners(img, (w, h), corners, ret)
    return img, img_points


def board2xyxy(img_points):
    """
    从标定板检测角点中提取标定板左上角和右下角坐标
    :param img_points: 检测角点
    :return: 标定板左上角和右下角坐标
    """
    if len(img_points) == 0:
        return None, None
    # 正常应该是第一个和最后一个点
    return img_points[0][0], img_points[0][-1]
