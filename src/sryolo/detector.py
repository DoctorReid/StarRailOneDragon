import os
import time
import urllib.request
import zipfile
from typing import Optional, List, Tuple

import cv2
import numpy as np
import onnxruntime as ort
import pandas as pd
from cv2.typing import MatLike
from basic.log_utils import log


class DetectContext:

    def __init__(self):
        """
        推理过程的上下文
        用于保存临时变量
        """
        self.conf: float = 0.7
        """检测时用的置信度阈值"""

        self.iou: float = 0.5
        """检测时用的IOU阈值"""

        self.img: MatLike = None
        """预测用的图片"""

        self.img_height: int = 0
        """原图的高度"""

        self.img_width: int = 0
        """原图的宽度"""

        self.scale_height: int = 0
        """缩放后的高度"""

        self.scale_width: int = 0
        """缩放后的宽度"""


class DetectClass:

    def __init__(self, class_id: int, class_name: str, class_cate: str):
        """
        检测类别
        """
        self.class_id: int = class_id
        self.class_name: str = class_name
        self.class_cate: str = class_cate


class DetectResult:

    def __init__(self, rect: List,
                 score: float,
                 detect_class: DetectClass):
        """
        图片检测的结果
        :param rect: 目标的位置 xyxy
        :param score: 得分（置信度）
        :param detect_class: 检测到的类别
        """
        self.x1: int = int(rect[0])
        """目标框的左上角x"""
        self.y1: int = int(rect[1])
        """目标框的左上角y"""
        self.x2: int = int(rect[2])
        """目标框的右下角x"""
        self.y2: int = int(rect[3])
        """目标框的右下角y"""

        self.score: float = score
        """得分（置信度）"""

        self.detect_class: DetectClass = detect_class
        """检测到的类别"""

    @property
    def center(self) -> Tuple[int, int]:
        """
        中心点的位置
        :return:
        """
        return (self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2


class StarRailYOLO:

    def __init__(self,
                 model_name: str = 'yolov8n-1088-full-v1',
                 model_parent_dir_path: Optional[str] = None,
                 cuda: bool = False):
        """
        崩铁用的YOLO模型 参考自 https://github.com/ibaiGorordo/ONNX-YOLOv8-Object-Detection
        :param model_name: 模型名称 在根目录下会有一个以模型名称创建的子文件夹
        :param model_parent_dir_path: 放置所有模型的根目录
        :param cuda: 是否启用CUDA
        """
        self.session: Optional[ort.InferenceSession] = None

        # 从模型中读取到的输入输出信息
        self.input_names: List[str] = []
        self.onnx_input_width: int = 0
        self.onnx_input_height: int = 0
        self.output_names: List[str] = []

        # 分类
        self.idx_2_class: dict[int, DetectClass] = {}

        # 检测并下载模型
        model_dir_path = get_model_dir_path(model_parent_dir_path, model_name)
        # 加载模型
        self.load_model(model_dir_path, cuda)
        self.load_detect_classes(model_dir_path)

    def load_model(self, model_dir_path: str, cuda: bool):
        """
        加载模型
        :param model_dir_path: 存放模型的子目录
        :param cuda: 是否启用CUDA
        :return:
        """
        availables = ort.get_available_providers()
        providers = ['CUDAExecutionProvider' if cuda else 'CPUExecutionProvider']
        if cuda and 'CUDAExecutionProvider' not in availables:
            log.error('机器未支持CUDA 使用CPU')
            providers = ['CPUExecutionProvider']

        onnx_path = os.path.join(model_dir_path, 'model.onnx')
        log.info('加载模型 %s', onnx_path)
        self.session = ort.InferenceSession(
            onnx_path,
            providers=providers
        )
        self.get_input_details()
        self.get_output_details()

    def load_detect_classes(self, model_dir_path: str):
        """
        加载分类
        :param model_dir_path: model_dir_path: str
        :return:
        """
        csv_path = os.path.join(model_dir_path, 'labels.csv')
        labels_df = pd.read_csv(csv_path, encoding='utf-8')
        self.idx_2_class = {}
        for _, row in labels_df.iterrows():
            self.idx_2_class[row['idx']] = DetectClass(row['idx'], row['label'], row['cate'])

    def detect(self, image: MatLike,
               conf: float = 0.5,
               iou: float = 0.5) -> List[DetectResult]:
        """

        :param image: 使用 opencv 读取的图片 BGR通道
        :param conf: 置信度阈值
        :param iou: IOU阈值
        :return: 检测得到的目标
        """
        t1 = time.time()
        context = DetectContext()
        context.conf = conf
        context.iou = iou

        input_tensor = self.prepare_input(image, context)
        t2 = time.time()

        outputs = self.inference(input_tensor)
        t3 = time.time()

        results = self.process_output(outputs, context)
        t4 = time.time()

        log.info(f'检测完毕 得到结果 {len(results)}个。预处理耗时 {t2 - t1:.3f}s, 推理耗时 {t3 - t2:.3f}s, 后处理耗时 {t4 - t3:.3f}s')
        return results

    def prepare_input(self, image: MatLike, context: DetectContext) -> np.ndarray:
        """
        对检测图片进行处理 处理结果再用于输入模型
        参考 https://github.com/orgs/ultralytics/discussions/6994?sort=new#discussioncomment-8382661
        :param image: 原图 BGR通道
        :param context: 上下文
        :return: 输入模型的图片 RGB通道
        """
        context.img = image
        context.img_height, context.img_width = image.shape[:2]

        rgb_img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # 将图像缩放到模型的输入尺寸中较短的一边
        min_scale = min(self.onnx_input_height / context.img_height, self.onnx_input_width / context.img_width)

        # 未进行padding之前的尺寸
        context.scale_height = int(round(context.img_height * min_scale))
        context.scale_width = int(round(context.img_width * min_scale))

        # 缩放到目标尺寸
        if self.onnx_input_height != context.img_height or self.onnx_input_width != context.img_width:  # 需要缩放
            input_img = np.full(shape=(self.onnx_input_height, self.onnx_input_width, 3),
                                fill_value=114, dtype=np.uint8)
            scale_img = cv2.resize(rgb_img, (context.scale_width, context.scale_height), interpolation=cv2.INTER_LINEAR)
            input_img[0:context.scale_height, 0:context.scale_width, :] = scale_img
        else:
            input_img = rgb_img

        # 缩放后最后的处理
        input_img = input_img / 255.0
        input_img = input_img.transpose(2, 0, 1)
        input_tensor = input_img[np.newaxis, :, :, :].astype(np.float32)

        return input_tensor

    def inference(self, input_tensor: np.ndarray):
        """
        图片输入到模型中进行推理
        :param input_tensor: 输入模型的图片 RGB通道
        :return: onnx模型推理得到的结果
        """
        outputs = self.session.run(self.output_names, {self.input_names[0]: input_tensor})
        return outputs

    def process_output(self, output, context: DetectContext) -> List[DetectResult]:
        """
        :param output: 推理结果
        :param context: 上下文
        :return: 最终得到的识别结果
        """
        predictions = np.squeeze(output[0]).T

        # 按置信度阈值进行基本的过滤
        scores = np.max(predictions[:, 4:], axis=1)
        predictions = predictions[scores > context.conf, :]
        scores = scores[scores > context.conf]

        results: List[DetectResult] = []
        if len(scores) == 0:
            return results

        # 选择置信度最高的类别
        class_ids = np.argmax(predictions[:, 4:], axis=1)

        # 提取Bounding box
        boxes = predictions[:, :4]  # 原始推理结果 xywh
        scale_shape = np.array([context.scale_width, context.scale_height, context.scale_width, context.scale_height])  # 缩放后图片的大小
        boxes = np.divide(boxes, scale_shape, dtype=np.float32)  # 转化到 0~1
        boxes *= np.array([context.img_width, context.img_height, context.img_width, context.img_height])  # 恢复到原图的坐标
        boxes = xywh2xyxy(boxes)  # 转化成 xyxy

        # 进行NMS 获取最后的结果
        indices = multiclass_nms(boxes, scores, class_ids, context.iou)

        for idx in indices:
            result = DetectResult(rect=boxes[idx].tolist(),
                                  score=float(scores[idx]),
                                  detect_class=self.idx_2_class[int(class_ids[idx])]
                                  )
            results.append(result)

        return results

    def get_input_details(self):
        model_inputs = self.session.get_inputs()
        self.input_names = [model_inputs[i].name for i in range(len(model_inputs))]

        shape = model_inputs[0].shape
        self.onnx_input_height = shape[2]
        self.onnx_input_width = shape[3]

    def get_output_details(self):
        model_outputs = self.session.get_outputs()
        self.output_names = [model_outputs[i].name for i in range(len(model_outputs))]


_GH_PROXY_URL = 'https://mirror.ghproxy.com'
_MODEL_DOWNLOAD_PATH = 'https://github.com/DoctorReid/StarRail-YOLO/releases/download/model_download_test'

_COLORS = np.random.default_rng(3).uniform(0, 255, size=(100, 3))


def check_model_exists(model_parent_dir_path: str, model_name: str) -> bool:
    """
    检查模型是否已经下载好了
    :param model_parent_dir_path: 存放所有模型的根目录
    :param model_name: 使用的模型名称
    :return:
    """
    model_dir_path = os.path.join(model_parent_dir_path, model_name)
    onnx_path = os.path.join(model_dir_path, 'model.onnx')
    labels_path = os.path.join(model_dir_path, 'labels.csv')

    return (os.path.exists(model_dir_path)
            and os.path.exists(onnx_path)
            and os.path.exists(labels_path)
            )


def get_model_dir_path(model_parent_dir_path: str, model_name: str) -> str:
    """
    获取模型所在的目录 如果目录不存在 或者缺少文件 则进行下载
    :param model_parent_dir_path: 存放所有模型的根目录
    :param model_name: 使用的模型名称
    :return: 返回模型的目录
    """
    if model_parent_dir_path is None:  # 默认使用本文件的目录
        model_parent_dir_path = os.path.abspath(__file__)

    if not check_model_exists(model_parent_dir_path, model_name):
        download = download_model(model_parent_dir_path, model_name)
        if not download:
            raise Exception('模型下载失败 可手动下载模型')

    return os.path.join(model_parent_dir_path, model_name)


def download_model(model_dir_path: str, model_name: str) -> bool:
    """
    下载模型
    :param model_dir_path: 模型子目录
    :param model_name: 模型名称
    :return: 是否成功下载模型
    """
    if not os.path.exists(model_dir_path):
        os.mkdir(model_dir_path)
    url = f'{_GH_PROXY_URL}/{_MODEL_DOWNLOAD_PATH}/{model_name}.zip'
    log.info('开始下载 %s %s', model_name, url)
    zip_file_path = os.path.join(model_dir_path, f'{model_name}.zip')
    last_log_time = time.time()

    def log_download_progress(block_num, block_size, total_size):
        nonlocal last_log_time
        if time.time() - last_log_time < 1:
            return
        last_log_time = time.time()
        downloaded = block_num * block_size / 1024.0 / 1024.0
        total_size_mb = total_size / 1024.0 / 1024.0
        progress = downloaded / total_size_mb * 100
        log.info(f"正在下载 {model_name}: {downloaded:.2f}/{total_size_mb:.2f} MB ({progress:.2f}%)")

    try:
        _, _ = urllib.request.urlretrieve(url, zip_file_path, log_download_progress)
        log.info('下载完成 %s', model_name)
        unzip_model(zip_file_path, os.path.join(model_dir_path, model_name))
        return True
    except Exception:
        log.error('下载失败模型失败', exc_info=True)
        return False


def unzip_model(zip_file_path: str, extract_dir: str):
    """
    解压文件
    :param zip_file_path: 压缩文件路径
    :param extract_dir: 提取的路径
    :return:
    """
    log.info('开始解压文件 %s', zip_file_path)

    if not os.path.exists(extract_dir):
        os.mkdir(extract_dir)

    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

    log.info('解压完成 %s', zip_file_path)


def nms(boxes, scores, iou_threshold):
    # Sort by score
    sorted_indices = np.argsort(scores)[::-1]

    keep_boxes = []
    while sorted_indices.size > 0:
        # Pick the last box
        box_id = sorted_indices[0]
        keep_boxes.append(box_id)

        # Compute IoU of the picked box with the rest
        ious = compute_iou(boxes[box_id, :], boxes[sorted_indices[1:], :])

        # Remove boxes with IoU over the threshold
        keep_indices = np.where(ious < iou_threshold)[0]

        # print(keep_indices.shape, sorted_indices.shape)
        sorted_indices = sorted_indices[keep_indices + 1]

    return keep_boxes


def multiclass_nms(boxes, scores, class_ids, iou_threshold):

    unique_class_ids = np.unique(class_ids)

    keep_boxes = []
    for class_id in unique_class_ids:
        class_indices = np.where(class_ids == class_id)[0]
        class_boxes = boxes[class_indices,:]
        class_scores = scores[class_indices]

        class_keep_boxes = nms(class_boxes, class_scores, iou_threshold)
        keep_boxes.extend(class_indices[class_keep_boxes])

    return keep_boxes


def compute_iou(box, boxes):
    # Compute xmin, ymin, xmax, ymax for both boxes
    xmin = np.maximum(box[0], boxes[:, 0])
    ymin = np.maximum(box[1], boxes[:, 1])
    xmax = np.minimum(box[2], boxes[:, 2])
    ymax = np.minimum(box[3], boxes[:, 3])

    # Compute intersection area
    intersection_area = np.maximum(0, xmax - xmin) * np.maximum(0, ymax - ymin)

    # Compute union area
    box_area = (box[2] - box[0]) * (box[3] - box[1])
    boxes_area = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    union_area = box_area + boxes_area - intersection_area

    # Compute IoU
    iou = intersection_area / union_area

    return iou


def xywh2xyxy(x):
    # Convert bounding box (x, y, w, h) to bounding box (x1, y1, x2, y2)
    y = np.copy(x)
    y[..., 0] = x[..., 0] - x[..., 2] / 2
    y[..., 1] = x[..., 1] - x[..., 3] / 2
    y[..., 2] = x[..., 0] + x[..., 2] / 2
    y[..., 3] = x[..., 1] + x[..., 3] / 2
    return y


def draw_detections(image: MatLike, results: List[DetectResult], mask_alpha=0.3):
    det_img = image.copy()

    img_height, img_width = image.shape[:2]
    font_size = min([img_height, img_width]) * 0.0006
    text_thickness = int(min([img_height, img_width]) * 0.001)

    det_img = draw_masks(det_img, results, mask_alpha)

    # Draw bounding boxes and labels of detections
    for result in results:
        color = _COLORS[result.detect_class.class_id]

        cv2.rectangle(det_img, (result.x1, result.y1), (result.x2, result.y2), color, 2)

        label = result.detect_class
        caption = f'{label.class_name} {int(result.score * 100)}%'
        draw_text(det_img, caption, result, font_size, text_thickness)

    return det_img


def draw_text(image: np.ndarray, text: str, result: DetectResult,
              font_size: float = 0.001, text_thickness: int = 2) -> np.ndarray:
    x1, y1, x2, y2 = result.x1, result.y1, result.x2, result.y2
    color = _COLORS[result.detect_class.class_id]
    (tw, th), _ = cv2.getTextSize(text=text, fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                                  fontScale=font_size, thickness=text_thickness)
    th = int(th * 1.2)

    cv2.rectangle(image, (x1, y1),
                  (x1 + tw, y1 - th), color, -1)

    return cv2.putText(image, text, (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, font_size, (255, 255, 255), text_thickness, cv2.LINE_AA)


def draw_masks(image: np.ndarray, results: List[DetectResult], mask_alpha: float = 0.3) -> np.ndarray:
    mask_img = image.copy()

    # Draw bounding boxes and labels of detections
    for result in results:
        color = _COLORS[result.detect_class.class_id]

        # Draw fill rectangle in mask image
        cv2.rectangle(mask_img, (result.x1, result.y1), (result.x2, result.y2), color, -1)

    return cv2.addWeighted(mask_img, mask_alpha, image, 1 - mask_alpha, 0)
