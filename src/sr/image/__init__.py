from typing import Optional

import numpy as np
from cv2.typing import MatLike

from basic import os_utils
from basic.img import MatchResultList
from sr.const.map_const import Region


class TemplateImage:

    def __init__(self):

        self.origin: MatLike = None  # 原图
        self.gray: MatLike = None  # 灰度图
        self.mask: MatLike = None  # 掩码
        self.kps = None  # 特征点
        self.desc = None  # 描述符

    def get(self, t: str):
        if t is None or t == 'origin':
            return self.origin
        if t == 'gray':
            return self.gray
        if t == 'mask':
            return self.mask


class ImageMatcher:

    def get_template(self, template_id: str,
                     template_sub_dir: Optional[str] = None) -> TemplateImage:
        """
        获取对应模板图片
        :param template_id: 模板id
        :param template_sub_dir: 模板的子文件夹
        :return: 模板图片
        """
        pass

    def match_image(self, source: MatLike, template: MatLike,
                    threshold: float = 0.5, mask: np.ndarray = None,
                    only_best: bool = True,
                    ignore_inf: bool = True):
        """
        在原图中 匹配模板
        :param source: 原图
        :param template: 模板图片
        :param threshold: 匹配阈值
        :param mask: 掩码
        :param only_best: 只返回最好的结果
        :param ignore_inf: 是否忽略无限大的结果
        :return: 所有匹配结果
        """
        pass

    def match_template(self, source: MatLike,
                       template_id: str,
                       template_sub_dir: Optional[str] = None,
                       template_type: str = 'origin',
                       threshold: float = 0.5,
                       mask: np.ndarray = None,
                       ignore_template_mask: bool = False,
                       only_best: bool = True,
                       ignore_inf: bool = True) -> MatchResultList:
        """
        在原图中 匹配模板 如果模板图中有掩码图 会自动使用
        :param source: 原图
        :param template_id: 模板id
        :param template_sub_dir: 模板的子文件夹
        :param template_type: 使用哪种类型模板
        :param threshold: 匹配阈值
        :param mask: 额外使用的掩码 与原模板掩码叠加
        :param ignore_template_mask: 是否忽略模板自身的掩码
        :param only_best: 只返回最好的结果
        :param ignore_inf: 是否忽略无限大的结果
        :return: 所有匹配结果
        """
        pass

    def match_template_with_rotation(self, source: MatLike, template_id: str,
                                     threshold: float = 0.5,
                                     mask: np.ndarray = None,
                                     only_best: bool = True,
                                     ignore_inf: bool = True) -> dict:
        """
        在原图中 对模板进行360度旋转匹配
        :param source: 原图
        :param template_id: 模板id
        :param threshold: 匹配阈值
        :param mask: 掩码
        :param only_best: 只返回最好的结果
        :param ignore_inf: 是否忽略无限大的结果
        :return: 每个选择角度的匹配结果
        """
        pass


def get_large_map_dir_path(region: Region):
    return os_utils.get_path_under_work_dir('images', 'map', region.planet.np_id, region.rl_id)
