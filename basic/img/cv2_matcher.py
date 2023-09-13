from typing import List

import cv2
import numpy as np
from PIL.Image import Image

from basic.img import ImageMatcher, ImageLike, MatchResult, MatchResultList
from basic.log_utils import log


class CvImageMatcher(ImageMatcher):

    def __init__(self):
        self.templates = {}

    def read_image_with_alpha(self, file_path: str, show_result: bool = False):
        """
        读取图片 如果没有透明图层则加入
        :param file_path: 图片路径
        :param show_result: 是否显示结果
        :return:
        """
        image = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
        channels = cv2.split(image)
        if len(channels) != 4:
            # 创建透明图层
            alpha = np.ones(image.shape[:2], dtype=np.uint8) * 255
            # 合并图像和透明图层
            image = cv2.merge((image, alpha))
        if show_result:
            cv2.imshow('Result', image)
        return image

    def load_template(self, template_id: str, template_path: str, x_scale: float = 1, y_scale: float = 1):
        """
        加载需要匹配的模板到内存中 后续使用模板id匹配即可
        :param template_id: 模板id
        :param template_path: 模板路径
        :param x_scale: 读取后缩放比例x
        :param y_scale: 读取后缩放比例y
        :return:
        """
        res = self.read_image_with_alpha(template_path)
        if x_scale != 1 or y_scale != 1:
            res = cv2.resize(res, (0, 0), fx=x_scale, fy=y_scale)

        self.templates[template_id] = res

    def match_template_by_id(self, source_image: ImageLike, template_id: str, threshold: float = 0,
                             src_x_scale: float = 1, src_y_scale: float = 1,
                             show_result: bool = False) -> MatchResultList:
        """
        在原图中 匹配模板
        :param source_image: 原图
        :param template_id: 模板id
        :param threshold: 匹配阈值
        :param src_x_scale: 原图缩放比例x
        :param src_y_scale: 原图缩放比例y
        :param show_result：是否在最后显示结果图片
        :return: 所有匹配结果
        """
        if template_id not in self.templates:
            log.error('未加载模板 %s' % template_id)
            return 0, 0, 0
        source: cv2.typing.MatLike = None
        if type(source_image) == Image:
            if source_image.mode == 'RGBA':
                source = cv2.cvtColor(np.array(source_image), cv2.COLOR_RGBA2BGRA)
            else:
                source = cv2.cvtColor(source_image.convert('RGBA'), cv2.COLOR_RGBA2BGRA)
        elif type(source_image) == str:
            source = cv2.imread(source_image)
        else:
            source = source_image
        if src_x_scale != 1 or src_y_scale != 1:
            source = cv2.resize(source, (0, 0), fx=src_x_scale, fy=src_y_scale)

        template = self.templates[template_id]
        tx, ty, _ = template.shape

        # 创建掩码图像，将透明背景像素设置为零
        mask = np.where(template[..., 3] > 0, 255, 0).astype(np.uint8)
        # 进行模板匹配，忽略透明背景
        result = cv2.matchTemplate(source, template, cv2.TM_CCOEFF_NORMED, mask=mask)

        match_result_list = MatchResultList()
        # 获取匹配结果的位置
        locations = np.where(result >= threshold)  # threshold是一个阈值，用于过滤低置信度的匹配结果

        # 遍历所有匹配结果，并输出位置和置信度
        for pt in zip(*locations[::-1]):
            confidence = result[pt[1], pt[0]]  # 获取置信度
            match_result_list.append(MatchResult(confidence, pt[0], pt[1], tx, ty))

        log.debug('模板[%s]匹配结果 %s', template_id, str(match_result_list))

        if show_result:
            for i in match_result_list:
                cv2.rectangle(source, (i.x, i.y), (i.x + i.w, i.y + i.h), (255, 0, 0), 1)
            cv2.imshow('Result', source)
        return match_result_list

