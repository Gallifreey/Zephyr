import asyncio
import time
import base64
import json
import random
import cv2
import numpy as np

from core.library.EasyImportBase import ROOT
from core.library.EventBusBase import EventBus
from core.library.RadarWebsocketBase import RadarWebsocketViewBase
from core.library.Utils import pnp, pnp2pose, numpy2list_in_dict, is_none
from core.utils.logger import Logger


class VideoStreamView(RadarWebsocketViewBase):

    def __init__(self):
        self.port = 1000
        super().__init__()

    async def enter(self, websocket):
        while True:
            result, img_encode = cv2.imencode('.jpg', EventBus.get('annotator_result')['data'])
            data = np.array(img_encode)
            img = data.tobytes()
            img = base64.b64encode(img).decode()
            ws_buffer = {
                'img': "data:image/jpeg;base64," + img
            }
            await websocket.send(json.dumps(ws_buffer))


class DataView(RadarWebsocketViewBase):
    def __init__(self):
        self.port = 1001
        super().__init__()

    async def enter(self, websocket):
        with open(ROOT('data/config.json'), 'r') as f:
            data = f.readlines()
            if websocket.ws_server.is_serving():
                await websocket.send(data)


class ReprojectView(RadarWebsocketViewBase):

    def __init__(self):
        self.port = 1002
        super().__init__()

    async def enter(self, websocket):
        pass
        while True:
            if is_none(EventBus.get('bev_points')['data']):
                continue
            ws_buffer = {
                'data': numpy2list_in_dict(EventBus.get('bev_points')['data'])
            }
            if websocket.ws_server.is_serving():
                await websocket.send(json.dumps(ws_buffer))
            time.sleep(0.2)


class LogView(RadarWebsocketViewBase):
    def __init__(self):
        self.port = 1003
        self.__index = 0
        super().__init__()

    async def enter(self, websocket):
        while True:
            if len(Logger.output_logs()) > self.__index:
                time.sleep(0.1)
                try:
                    if websocket.ws_server.is_serving():
                        await websocket.send(Logger.output_logs()[self.__index])
                except Exception as e:
                    Logger.danger(f'Websocket has been closed.ERROR: {e}')
                    break
                await asyncio.sleep(0)
                self.__index += 1
            else:
                time.sleep(0.1)


class CalibrateView(RadarWebsocketViewBase):
    def __init__(self):
        self.port = 1004
        self.__flag = 2
        self.__terminate_process = True
        super().__init__()

    async def enter(self, websocket):
        if self.__flag == 0:
            await self.calibrate_camera(websocket)
        elif self.__flag == 1:
            await self.calibrate_camera_lidar(websocket)
        elif self.__flag == 2:
            await self.calibrate_camera_env(websocket)

    async def calibrate_camera(self, ws):
        while self.__terminate_process:
            pass

    async def calibrate_camera_lidar(self, ws):
        while self.__terminate_process:
            pass

    async def calibrate_camera_env(self, ws):
        while self.__terminate_process:
            result, img_encode = cv2.imencode('.jpg', EventBus.get('camera_view')['data'])
            data = np.array(img_encode)
            img = data.tobytes()
            img = base64.b64encode(img).decode()
            ws_buffer = {
                'img': "data:image/jpeg;base64," + img
            }
            await ws.send(json.dumps(ws_buffer))


class CalibrationDataView(RadarWebsocketViewBase):

    def __init__(self):
        self.port = 1005
        self.__terminate = False
        super().__init__()

    async def enter(self, websocket):
        while not self.__terminate:
            # message = await websocket.recv()
            # # 正则化，乘宽高系数
            # message = json.loads(message)
            # print(message)
            # points, size = message['labels'], message['size']
            points, size = EventBus.get('label_points_cache')['data'], EventBus.get('frontend_label_view_size_cache')[
                'data']
            rw = EventBus.get('image')['data']['width'] / size[0]
            rh = EventBus.get('image')['data']['height'] / size[1]
            for k, v in points.items():
                x, y = points[k]
                points[k] = [x * rw, y * rh]
            EventBus.put('label_points', points)
            # 解算
            rvec, tvec = pnp(points, EventBus.get('real_world_label_points')['data'],
                             EventBus.get('camera_intrinsic_matrix')['data'],
                             EventBus.get('camera_dist')['data'])
            t, cp = pnp2pose(rvec, tvec)
            # 更新
            EventBus.put('cam2world', t)
            EventBus.put('cam_in_world', cp)
            self.__terminate = True
