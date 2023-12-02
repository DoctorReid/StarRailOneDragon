from typing import Optional

import cv2
import numpy as np
from cv2.typing import MatLike

from basic.img import MatchResultList, cv2_utils
from basic.log_utils import log
from sr.image import ImageMatcher, TemplateImage
from sr.image.image_holder import ImageHolder


class CvImageMatcher(ImageMatcher):

    def __init__(self, ih: ImageHolder = None):
        self.ih = ImageHolder() if ih is None else ih

    def get_template(self, template_id: str,
                     template_sub_dir: Optional[str] = None) -> TemplateImage:
        """
        获取对应模板图片
        :param template_id: 模板id
        :param template_sub_dir: 模板的子文件夹
        :return: 模板图片
        """
        return self.ih.get_template(template_id, sub_dir=template_sub_dir)

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
        return cv2_utils.match_template(source, template, threshold, mask=mask,
                                        only_best=only_best, ignore_inf=ignore_inf)

    def match_template(self, source: MatLike, template_id: str,
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
        :param template_type: 模板类型
        :param threshold: 匹配阈值
        :param mask: 额外使用的掩码 与原模板掩码叠加
        :param ignore_template_mask: 是否忽略模板自身的掩码
        :param only_best: 只返回最好的结果
        :param ignore_inf: 是否忽略无限大的结果
        :return: 所有匹配结果
        """
        template: TemplateImage = self.get_template(template_id, template_sub_dir)
        if template is None:
            log.error('未加载模板 %s' % template_id)
            return MatchResultList()

        mask_usage = None
        if not ignore_template_mask:
            mask_usage = cv2.bitwise_or(mask_usage, template.mask) if mask_usage is not None else template.mask
        if mask is not None:
            mask_usage = cv2.bitwise_or(mask_usage, mask) if mask_usage is not None else mask
        return self.match_image(source, template.get(template_type), threshold, mask_usage,
                                only_best=only_best, ignore_inf=ignore_inf)
