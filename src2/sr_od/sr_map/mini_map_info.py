from cv2.typing import MatLike
from typing import Optional


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
