import os.path
from os import PathLike
from typing import Union

from core.library.Utils import Singleton


class EasyImport(Singleton):
    """
    本类用于处理Python导入模块问题。
    """
    __resource_root = ""
    __file_map = []

    def __init__(self):
        super().__init__()

    @classmethod
    def set_resource_root_path(cls, root):
        """
        设置资源根目录
        """
        cls.__resource_root = root
        # 建立根目录索引
        cls.__build_dir(cls.__resource_root)

    @classmethod
    def get(cls):
        return cls.__file_map

    @classmethod
    def __build_dir(cls, dir_path):
        resource_file_list = os.listdir(dir_path)
        for resource in resource_file_list:
            p = f'{dir_path}/{resource}'
            if os.path.isdir(p):
                cls.__build_dir(p)
            else:
                cls.__file_map.append(p)

    @classmethod
    def set_ignore_path(cls, path: Union[list, str]):
        pass

    @classmethod
    def get_absolute_path(cls, filename):
        """
        返回资源目录的绝对路径 \n
        :param filename: 文件名，重复会报错
        :return: 绝对路径
        """
        for p in cls.__file_map:
            if filename in p:
                return p
        return ""


EasyImport.set_resource_root_path(r"F:\Python\Zephyr\backend\resource")
ROOT = EasyImport.get_absolute_path
