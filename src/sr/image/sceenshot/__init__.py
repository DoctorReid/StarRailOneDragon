from typing import Optional

import cv2
from cv2.typing import MatLike

from basic import Point
from sr.const.map_const import Region


def fill_uid_black(screen: MatLike):
    """
    将截图的UID部分变成灰色 （这个颜色是YOLO的填充默认颜色）
    :param screen: 屏幕截图
    """
    lt = (30, 1030)
    rb = (200, 1080)
    cv2.rectangle(screen, lt, rb, (114, 114, 114), -1)


class MiniMapInfo:

    def __init__(self):
        self.origin: MatLike = None  # 原图
        self.origin_del_radio: MatLike = None  # 原图减掉雷达
        self.center_arrow_mask: MatLike = None  # 小地图中心小箭头的掩码 用于判断方向
        self.arrow_mask: MatLike = None  # 整张小地图的小箭头掩码 用于合成道路掩码
        self.angle: Optional[float] = None  # 箭头方向
        self.circle_mask: MatLike = None  # 小地图圆形
        self.sp_mask: MatLike = None  # 特殊点的掩码
        self.sp_result: Optional[dict] = None  # 匹配到的特殊点结果
        self.road_mask: MatLike = None  # 道路掩码 不包含中间的小箭头 以及特殊点
        self.road_mask_with_edge: MatLike = None  # 有边缘道路掩码 不包含中间的小箭头 以及特殊点 适用于灰度图和原图匹配


class LargeMapInfo:

    def __init__(self):
        self.region: Optional[Region] = None  # 区域
        self.raw: MatLike = None  # 原图
        self.origin: MatLike = None  # 处理后的原图
        self.gray: MatLike = None  # 灰度图 用于特征检测
        self.mask: MatLike = None  # 主体掩码 用于特征匹配
        self.sp_result: Optional[dict] = None  # 特殊点坐标
        self.kps = None  # 特征点 用于特征匹配
        self.desc = None  # 描述子 用于特征匹配


class SimUniLevelInfo:

    def __init__(self):
        """
        模拟宇宙中每层的信息
        """

        self.initial_mm: Optional[MatLike] = None
        """刚进入这层 小地图的截图"""

        self.uni_num: Optional[int] = None
        """属于第几个宇宙的"""

        self.lm_info: Optional[LargeMapInfo] = None
        """该层对应的大地图"""

        self.start_pos: Optional[Point] = None
        """刚进入这层所在的位置"""
