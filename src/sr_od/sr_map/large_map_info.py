import cv2
from cv2.typing import MatLike
from typing import Optional, Tuple, List

from one_dragon.utils import cv2_utils
from sr_od.sr_map.sr_map_def import Region


class LargeMapInfo:

    def __init__(self):
        self.region: Optional[Region] = None  # 区域
        self.raw: MatLike = None  # 原图
        self._gray: MatLike = None  # 灰度图
        self.mask: MatLike = None  # 主体掩码 用于特征匹配
        self.sp_result: Optional[dict] = None  # 特殊点坐标
        self._kps = None  # 特征点 用于特征匹配
        self._desc = None  # 描述子 用于特征匹配

    @property
    def gray(self) -> MatLike:
        if self._gray is not None:
            return self._gray
        if self.raw is None:
            return None
        self._gray = cv2.cvtColor(self.raw, cv2.COLOR_RGB2GRAY)
        return self._gray

    @property
    def features(self) -> Tuple[List[cv2.KeyPoint], MatLike]:
        if self._kps is not None:
            return self._kps, self._desc
        if self.raw is not None:
            self._kps, self._desc = cv2_utils.feature_detect_and_compute(self.raw, self.mask)
        return self._kps, self._desc
