import math
import queue
from collections import Counter

import cv2
import numpy as np
import torch
from ultralytics.utils.plotting import Annotator, colors

from core.library.EasyImportBase import ROOT
from core.library.Utils import Singleton, draw_rec, get_bbox_from_label, get_max_conf_bbox, get_max_item_from_dict, \
    get_data_from_list
from core.utils.logger import Logger
from core.inference.yolov5.models.common import DetectMultiBackend
from core.inference.yolov5.utils.dataloaders import LoadImage
from core.inference.yolov5.utils.general import Profile, check_img_size, non_max_suppression, scale_boxes
from core.inference.yolov5.utils.torch_utils import select_device


# TODO YOLO检测器待办功能
# TODO 1.  跟丢目标预测
# TODO 2.  卡尔曼滤波跟踪预测目标
# TODO *3. 投票机制(vote)，为追求更高的精度(显然会增大运算量)，意思是加载多个模型同时预测[比如：小、中、大模型同时预测以防止模糊目标、小目标]
# TODO 长期支持
# TODO 1.  模型的轻量化与高精化
# TODO 2.  将更改模型结构永远是明智的选择
# TODO 3.  不妨优化下代码
# TODO 4.  模型精度理论(模型抗模糊[尝试利用高精原点图片进行stage2检测，将模糊图片用于stage1检测])
# TODO 5.  多路模型检测功能，取不同检测效果的若干模型同时检测将结果取平均

class YoloBox:
    """
    YOLO检测框
    """
    cls = 0  # 标签
    car_bbox = []
    armor_bbox = []
    car_copy = []


class YoloDetector(Singleton):
    """
    YOLO检测器为双层神经网络检测，多批次检测并行，结构同传统一致。 \n
    并具有检测(检测armor及car)、跟踪(防跟丢、防未检测)、预测(跟丢、未检测)、热更新(热更新检测批次、检测chunk、检测输入图片尺寸、供检测模型)、数据保存(保存场地数据)
    """
    __data_root = 'resource/assets/data/'
    __saved_root = 'resource/assets/yolo-output.mp4'
    weights_list = [ROOT('car.pt'), ROOT('armor.pt')]
    conf_thr = 0.25
    iou_thr = 0.45
    device = ''
    hide_labels = False
    hide_conf = False
    device_ = select_device(device)
    model = None
    stage = 0
    parent = None
    use_zio = False  # 是否使用Zoom In/Zoom Out操作
    is_saved = False  # 是否录制
    __out = None  # 录制视频流
    __total_ticks = 0  # 总Tick数
    __is_init = False
    __detect_cars = []
    __detect_armors = []
    __car_trail = []  # 轨迹
    __car_copy = []  # stage2阶段矩形框的坐标
    __armor_index = {}  # armor索引
    __last_img = None

    def __init__(self):
        super().__init__()

    @classmethod
    def __init(cls):
        # 加载YOLO模型
        Logger.info('Loading Yolo models...')
        Logger.info(f'Found {len(cls.weights_list)} models in {[url for url in cls.weights_list]}')
        cls.model = [DetectMultiBackend(cls.weights_list[0], device=cls.device_, dnn=False, data='', fp16=False),
                     DetectMultiBackend(cls.weights_list[1], device=cls.device_, dnn=False, data='', fp16=False)]
        Logger.info('Yolo models load finished.')
        # 分配轨迹空间
        classes = cls.parent.get('robot_classes')['data']
        for cl in classes:
            cls.__car_trail.append(
                {
                    'type': cl,
                    'trail': queue.Queue(maxsize=cls.parent.get('max_trail_queue_size')['data']),
                    'tick': 0,  # 标记帧
                    'has_predicted': False  # 是否已经预测过
                }
            )

    @classmethod
    def get_total_ticks(cls):
        return cls.__total_ticks

    @classmethod
    def run(cls, img, img_sz=(640, 640)):
        if not cls.__is_init:
            cls.__init()
            cls.__is_init = True
        model = cls.model[cls.stage]
        stride, names, pt = model.stride, model.names, model.pt
        imgsz = check_img_size(img_sz, s=stride)
        bs = 1
        b_img = img
        if cls.use_zio:
            img = cls.use_zoom_in_out_function(img)
        dataset = LoadImage(img, img_size=imgsz, stride=stride)
        model.warmup(imgsz=(1 if pt or model.triton else bs, 3, *imgsz))
        seen, windows, dt = 0, [], (Profile(), Profile(), Profile())
        coord = []
        for im, im0s in dataset:
            s = ''
            with dt[0]:
                im = torch.from_numpy(im).to(model.device)
                im = im.half() if model.fp16 else im.float()
                im /= 255
                if len(im.shape) == 3:
                    im = im[None]
            with dt[1]:
                pred = model(im, augment=False, visualize=False)
            with dt[2]:
                pred = non_max_suppression(pred, cls.conf_thr, cls.iou_thr)
            for i, det in enumerate(pred):
                seen += 1
                im0, frame = im0s.copy(), getattr(dataset, 'frame', 0)
                annotator = Annotator(im0, line_width=3, example=str(names))
                if len(det):
                    det[:, :4] = scale_boxes(im.shape[2:], det[:, :4], im0.shape).round()
                    for c in det[:, 5].unique():
                        n = (det[:, 5] == c).sum()
                        s += f"{n} {names[int(c)]}{'s' * (n > 1)} | "
                    for *xyxy, conf, cls_ in reversed(det):
                        c = int(cls_)
                        label = None if cls.hide_labels else (names[c] if cls.hide_conf else f'{names[c]} {conf:.2f}')
                        annotator.box_label(xyxy, label, color=colors(c, True))
                        coord.append([c, [int(f) for f in xyxy], float(conf)])
                im0 = annotator.result()
                cls.parent.update('annotator_result', im0)
                if cls.stage == 1:
                    cv2.imshow('res', im0)
                    cv2.waitKey(1)
            Logger.output(
                f"stage {cls.stage + 1} {s}{'' if len(det) else '(no detections) | '}Spend {dt[1].dt * 1E3:.1f}ms")
        if cls.stage == 1:
            cls.__total_ticks += 1
            cls.__detect_armors = coord
            cls.stage = 0
            res = cls.__gen_final_detect_result(chunk_size=256, chunk_per_line=5)
            # cls.__save_pre_tick_information(res)
            cls.__normalize(res)
            if len(cls.__detect_armors) != 0 and len(cls.__detect_cars) != 0:
                res = cls.__reshape()
                img = draw_rec(cls.__last_img, [p[1] for p in res])
                img = cv2.resize(img, dsize=(1000, 600))
                cv2.imshow('aaa', img)
                cv2.waitKey(0)
            cls.parent.update('armor_car_index', cls.__armor_index)
            cls.parent.update('armor_bbox', res)
            return
        cls.__last_img = img
        cls.__detect_cars = coord
        cls.stage = 1
        input_image = b_img if cls.use_zio else img
        iw, ih = img.shape[:2]
        bw, bh = b_img.shape[:2]
        input_coord = cls.gen_scale_coord(coord, (bw / iw, bh / ih)) if cls.use_zio else coord
        stage2_img = cls.__gen_clip_image(input_image=input_image, input_coord=input_coord)
        if not isinstance(stage2_img, type(None)):
            cls.run(img=stage2_img, img_sz=(640, 640))

    @classmethod
    def __gen_clip_image(cls, input_image, input_coord, n_cols=5, padding=255, has_border=True, border_color=255,
                         border_width=1, chunk_size=256):
        """
        :param input_image: 输入待剪切图像
        :param input_coord: 输入识别后的bbox
        :param n_cols: 每行融合图像数
        :param padding: 空缺图像填充值
        :param has_border: 是否与其他图像边缘融合。若边缘不融合，则会在图像外围创建边框以防止跨区块误识别
        :param border_color: 边框颜色
        :param border_width: 边框宽度
        :param chunk_size: 区块大小，为正方形
        :return: 融合的图像
        """
        if len(input_coord) == 0:
            return
        cols = min(n_cols, len(input_coord))
        rows = math.ceil(len(input_coord) / cols)
        res = np.full(fill_value=padding, shape=(rows * chunk_size, cols * chunk_size, 3))
        cls.__car_copy = []
        for index, bbox in enumerate(input_coord):
            _, coord, _ = bbox
            x1, y1, x2, y2 = coord
            img = cv2.resize(input_image[y1:y2, x1:x2, ],
                             dsize=(chunk_size - 2 * border_width, chunk_size - 2 * border_width) if has_border else (
                                 chunk_size, chunk_size))
            if has_border:
                padding_img = np.full(fill_value=border_color, shape=(chunk_size, chunk_size, 3))
                padding_img[border_width:(chunk_size - border_width), border_width:(chunk_size - border_width), ] = img
                img = padding_img
            row = math.floor(index / cols)
            col = index % cols
            if row < rows and col < cols:
                res[row * chunk_size: (row + 1) * chunk_size, col * chunk_size: (col + 1) * chunk_size, ] = img
                cls.__car_copy.append(
                    [index, coord, [col * chunk_size, row * chunk_size, (col + 1) * chunk_size, (row + 1) * chunk_size]])

        return np.array(res, dtype=np.uint8)

    @classmethod
    def __normalize(cls, index_list):
        res = []
        return res

    @classmethod
    def __reshape(cls):
        """
        :return: [[c, armor_bbox_in_origin_sample], ...]
        """
        res = []
        armors, copy = cls.__armor_index, cls.__car_copy
        for index, bbox in armors.items():
            d = get_data_from_list(0, copy, index)[0]
            c, car_bbox_ori, car_bbox_copy, armor_bbox = bbox[0][0], d[1], d[2], bbox[0][1]
            cx1o, cy1o, cx2o, cy2o = car_bbox_ori
            cx1c, cy1c, cx2c, cy2c = car_bbox_copy
            ax1, ay1, ax2, ay2 = armor_bbox
            stage2_width, stage2_height = abs(cx1c - cx2c), abs(cy1c - cy2c)
            w = abs(cx2o - cx1o)
            h = abs(cy2o - cy1o)
            rw = w / stage2_width
            rh = h / stage2_height
            delta_x1, delta_x2 = ax1 - cx1c, ax2 - cx2c
            delta_y1, delta_y2 = ay1 - cy1c, ay2 - cy2c
            res.append([c, [cx1o + delta_x1 * rw, cy1o + delta_y1 * rh, cx2o + delta_x2 * rw, cy2o + delta_y2 * rh]])
        # clear detect result list
        cls.__detect_cars = []
        cls.__detect_armors = []
        cls.__boxes = []
        return res

    @classmethod
    def __gen_final_detect_result(cls, chunk_size=64, chunk_per_line=5):
        """
        用于将检测的armor结果与检测到的car结果融合
        :return: 检测数组，包含[[类别(None为未检测到，其余和配置标签一致)， car的bbox，armor的bbox], ...]
        """

        def xyxy2c(xyxy):
            x1, y1, x2, y2 = xyxy
            return [(x1 + x2) / 2, (y1 + y2) / 2]

        # 索引armor-car关系
        res = [[None, car_p, []] for car_p in cls.__detect_cars]
        armor_index = {}
        for armor_p in cls.__detect_armors:
            cl, armor, _ = armor_p
            cx, cy = xyxy2c(armor)
            row = int(cy // chunk_size)
            col = math.floor(cx / chunk_size)
            index = row * chunk_per_line + col
            if not armor_index.get(index):
                armor_index[index] = []
            res[index][0] = cl
            res[index][2] = armor
            armor_index[index].append(armor_p)
        # 过滤标签
        """
        Step1: 若对应car中无armor则为None
        Step2: 若对应car中的armor与其color不符，则为None（或者为反色序号）
        Step3: 若对应car中的armor有多个，且都是相同的armor，则为这个armor类型
        Step4: 若对应car中的armor有多个，且有不同的armor，若armor的占比一样，取置信度最大的，反之取armor占比最大的
        Step5: 若对应car中的armor有一个，则为这个armor
        """
        for k, v in armor_index.items():
            if len(v) > 1:
                armor_label = [a[0] for a in v]
                # 计数
                counter = Counter(armor_label)
                # 排序，按计数降序排列
                counter = dict(sorted(counter.items(), reverse=True, key=lambda d: d[0]))
                # Step3
                if len(counter.keys()) == 1:
                    # 就是这个类型，且取最大置信度的类型
                    armor_index[k] = [get_max_conf_bbox(v)]
                else:
                    # Step4
                    temp = list(counter.values())[0]  # 为armor的最大数量
                    pair = {}
                    for k_, v_ in counter.items():
                        if v_ == temp:
                            bbox = get_bbox_from_label(k_, v)  # 获取对应label的bbox数组
                            avg = sum([box[-1] for box in bbox]) / len(bbox)
                            if not pair.get(avg):
                                # 以平均置信度作为key
                                pair[avg] = [get_max_conf_bbox(bbox)]
                            break
                    if len(pair.keys()) == 1:
                        # 说明，只有一个最大的armor
                        armor_index[k] = list(pair.values())[0]
                    elif len(pair.keys()) > 1:
                        # 取最大置信度的armor
                        armor_index[k] = [get_max_item_from_dict(pair)]
        cls.__armor_index = armor_index
        return armor_index

    @classmethod
    def __lost_target_action(cls, armor_car_index):
        """
        跟丢/未识别行为 \n
        跟丢：stage1/2均未识别到 \n
        未识别：stage1识别到但stage2未识别到
        """
        # 处理未识别
        for index, ac in enumerate(armor_car_index):
            cl, car_p, armor_p = ac
            if cl is None:
                _cl, _armor_p = cls.__predict_next_tick()  # 尝试补充未识别到的armor
                armor_car_index[index][0], armor_car_index[index][2] = _cl, _armor_p
        # 处理跟丢
        for index, trails in enumerate(cls.__car_trail):
            # 我们认为ticks参数不为0且同当前total_ticks不相同的对象为需要预测(即跟丢对象)，当该轮(直到再次检测到)结束后才将has_predicted参数置真
            if trails['tick'] == 0 or trails['tick'] == cls.__total_ticks or trails['has_predicted']:
                continue
            # 使用预测器去预测后{lost_target_need_predict_ticks}的坐标
            p = cls.__karman_filter()
            cls.__car_trail[index][1] = p
        return armor_car_index

    @classmethod
    def __predict_next_tick(cls):
        """
        使用先验数据预测丢失的下一帧坐标及armor类别
        """
        return None, None

    @classmethod
    def __save_pre_tick_information(cls, armor_car_index):
        """
        收集/保存先验数据
        """
        for index, ac in enumerate(armor_car_index):
            cl, car_p, _ = ac
            if cl is not None:
                q = cls.__car_trail[int(cl)]['trail']
                cls.__car_trail[int(cl)]['ticks'] = cls.__total_ticks
                if q.full():
                    q.get()
                q.put(car_p)

    @classmethod
    def __karman_filter(cls):
        """
        利用卡尔曼滤波平滑数据、预测数据
        """
        pass

    def __follow_target(self):
        """
        跟踪目标行为
        """
        pass

    @classmethod
    def save_init(cls):
        """
        保存场地数据
        """
        cls.__is_saved = True
        h, w = cls.parent.get('image')['height'], cls.parent.get('image')['width']
        cls.__out = cv2.VideoWriter(cls.__saved_root, cv2.VideoWriter.fourcc(*"mp4v"), 30, (w, h))

    def handle_break_event(self):
        if self.__is_saved:
            self.__out.release()

    def use_multi_models_detector(self):
        """
        多路模型检测器
        """
        pass

    @classmethod
    def use_zoom_in_out_function(cls, img):
        """
        使用放大/缩小方法对小目标进行检测，过程如下： \n
        Step1. 采集高分辨率图像作为基图 \n
        Step2. 将基图压缩，使其分辨率降低作为次图 \n
        Step3. 次图用来检测Car，并将检测的结果框映射到基图之上 \n
        Step4. 使用基图分割的ROI用于Armor的检测 \n
        Step5. 后续操作与前无异 \n
        :param img: 基图
        :return: 模糊图像
        """
        bh, bw = cls.parent.get('blur_image_size')
        blur_img = cv2.resize(img, dsize=(bw, bh))
        return blur_img

    @classmethod
    def gen_scale_coord(cls, coord, scale):
        x, y = scale
        for index, _ in enumerate(coord):
            coord[index][1][0] *= x
            coord[index][1][1] *= y
            coord[index][1][2] *= x
            coord[index][1][3] *= y
        return coord
