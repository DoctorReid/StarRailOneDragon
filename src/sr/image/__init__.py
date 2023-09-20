from typing import Union

import cv2
import numpy as np

from basic.img import MatchResultList


class ImageMatcher:

    def match_template(self, source: cv2.typing.MatLike, template: Union[cv2.typing.MatLike, str],
                       threshold: float = 0.5, ignore_inf: bool = True,
                       ignore_template_alpha: bool = True,
                       mask: np.ndarray = None,
                       show: bool = False) -> MatchResultList:
        """
        在原图中 匹配模板
        :param source: 原图
        :param template: 模板图片 或 模板id
        :param threshold: 匹配阈值
        :param ignore_inf: 是否忽略无限大的结果
        :param ignore_template_alpha: 是否忽略模板中的透明通道。会与掩码合并
        :param mask: 掩码
        :param show：是否显示匹配结果
        :return: 所有匹配结果
        """
        pass

    def match_template_with_rotation(self, source: cv2.typing.MatLike, template: Union[str, cv2.typing.MatLike],
                                     threshold: float = 0.5, ignore_inf: bool = True,
                                     ignore_template_alpha: bool = True,
                                     mask: np.ndarray = None,
                                     show: bool = False) -> dict:
        """
        在原图中 对模板进行360度旋转匹配
        :param source: 原图
        :param template: 模板图片 或 模板id
        :param threshold: 匹配阈值
        :param ignore_template_alpha: 是否忽略模板中的透明通道。会与掩码合并
        :param mask: 掩码
        :param ignore_inf: 是否忽略无限大的结果
        :param show：是否在最后显示结果图片
        :return: 每个选择角度的匹配结果
        """
        pass