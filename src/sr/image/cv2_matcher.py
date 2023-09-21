from typing import Union

import cv2
import numpy as np

from basic.img import MatchResultList, cv2_utils
from basic.log_utils import log
from sr.image import ImageMatcher
from sr.image.image_holder import ImageHolder


class CvImageMatcher(ImageMatcher):

    def __init__(self, ih: ImageHolder = None):
        self.ih = ImageHolder() if ih is None else ih

    def get_template(self, template: Union[cv2.typing.MatLike, str]):
        """
        获取对应模板图片
        :param template: 模板id 或 模板图片
        :return: 模板图片
        """
        if type(template) == str:
            return self.ih.get_template(template)
        else:
            return template

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
        template: cv2.typing.MatLike = self.get_template(template)
        if template is None:
            log.error('未加载模板 %s' % template)
            return MatchResultList()

        source_usage = source
        template_usage = template
        mask_usage = mask
        if ignore_template_alpha:
            alpha_mask = np.where(template[..., 3] > 0, 255, 0).astype(np.uint8)
            if mask_usage is None:
                mask_usage = alpha_mask
            else:
                mask_usage = cv2.bitwise_or(mask, alpha_mask)

        # 原图没有透明通道的话 模板图自动转化
        if len(source_usage.shape) == 2 and len(template_usage.shape) == 3:
            template_usage = cv2.cvtColor(template_usage, cv2.COLOR_BGRA2BGR)

        match_result_list = cv2_utils.match_template(
            source_usage, template_usage, threshold,
            mask=mask_usage,
            ignore_inf=ignore_inf)

        if show:
            cv2_utils.show_image(source, match_result_list, win_name='match_template_result')
            if mask_usage is not None:
                cv2_utils.show_image(mask_usage, match_result_list, win_name='match_template_mask')
        return match_result_list

    def get_rotate_template(self, template: Union[str, cv2.typing.MatLike], angle: int):
        """
        获取旋转后的模板
        :param template: 模板图片、模板id
        :param angle: 角度
        :return:
        """
        if type(template) == str:
            return self.ih.get_template(template, angle)
        else:
            return cv2_utils.image_rotate(template, angle)

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
        angle_result = {}
        for i in range(360):
            rt = self.get_rotate_template(template, i)
            result: MatchResultList = self.match_template(
                source, rt, threshold,
                ignore_inf=ignore_inf,
                ignore_template_alpha=ignore_template_alpha,
                mask=mask)
            if len(result) > 0:
                angle_result[i] = result

        return angle_result

