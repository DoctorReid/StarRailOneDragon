import cv2
from cv2.typing import MatLike

from sr.constants.map import Region
from sr.win import Window


def fill_uid_black(screen: MatLike, win: Window = None):
    """
    将截图的UID部分变成黑色
    :param screen: 屏幕截图
    :param win: 窗口
    :return: 没有UID的新图
    """
    img = screen.copy()
    lt = (30, 1030)
    rb = (200, 1080)
    if win is None:
        cv2.rectangle(img, lt, rb, (0, 0, 0), -1)
    else:
        cv2.rectangle(img, win.game_pos(lt), win.game_pos(rb), (0, 0, 0), -1)
    return img


class MiniMapInfo:

    def __init__(self):
        self.origin: MatLike = None  # 原图
        self.center_arrow_mask: MatLike = None  # 小地图中心小箭头的掩码 用于判断方向
        self.arrow_mask: MatLike = None  # 整张小地图的小箭头掩码 用于合成道路掩码
        self.angle: float = None  # 箭头方向
        self.gray: MatLike = None  # 灰度图 用于特征检测
        self.center_mask: MatLike = None  # 中心正方形 用于模板匹配
        self.circle_mask: MatLike = None  # 小地图圆形
        self.feature_mask: MatLike = None  # 小地图圆形 用于特征匹配
        self.sp_mask: MatLike = None  # 特殊点的掩码
        self.sp_result: dict = None  # 匹配到的特殊点结果
        self.road_mask: MatLike = None  # 道路掩码
        self.edge: MatLike = None  # 道路边缘 用于模板匹配
        self.kps = None  # 特征点 用于特征匹配
        self.desc = None  # 描述子 用于特征匹配


class LargeMapInfo:

    def __init__(self):
        self.region: Region = None  # 区域
        self.raw: MatLike = None  # 原图
        self.origin: MatLike = None  # 处理后的原图
        self.gray: MatLike = None  # 灰度图 用于特征检测
        self.mask: MatLike = None  # 主体掩码 用于特征匹配
        self.edge: MatLike = None  # 道路边缘 用于模板匹配
        self.sp_result: dict = None  # 特殊点坐标
        self.kps = None  # 特征点 用于特征匹配
        self.desc = None  # 描述子 用于特征匹配
