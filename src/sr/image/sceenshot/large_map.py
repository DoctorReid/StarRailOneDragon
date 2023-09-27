import time

import cv2
from cv2.typing import MatLike

from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.img.os import save_debug_image
from basic.log_utils import log
from sr import constants, save_map_image
from sr.config import ConfigHolder
from sr.constants import LabelValue
from sr.image import OcrMatcher
from sr.image.cv2_matcher import CvImageMatcher
from sr.image.image_holder import ImageHolder
from sr.map_cal import MapCalculator


def convert_origin_map(planet: str, region: str, save: bool = True) -> MatLike:
    """
    将大地图转化成黑白图，黑色为可以走的部分
    再将使用黑白图从原图中扣出细化的地图，用作后续匹配
    :param planet: 星球名称
    :param region: 对应区域
    :param save: 是否保存
    :return:
    """
    ih = ImageHolder()
    im = CvImageMatcher()
    ch = ConfigHolder()
    mc = MapCalculator(im=im, config=ch)
    large_map = ih.get_large_map(planet, region, 'origin')
    cv2.waitKey(0)


def get_planet(screen: MatLike, ocr: OcrMatcher) -> LabelValue:
    """
    从屏幕左上方 获取当前星球的名字
    :param screen: 屏幕截图
    :param ocr: ocr
    :return: 星球名称
    """
    word: str
    result = ocr.run_ocr(screen[30:100, 90:250], threshold=0.4)
    log.debug('屏幕左上方获取星球结果 %s', result.keys())
    for word in result.keys():
        if word.find(gt(constants.P1_KZJ.cn)) > -1:
            return constants.P1_KZJ
        if word.find(gt(constants.P2_YYL.cn)) > -1:
            return constants.P2_YYL
        if word.find(gt(constants.P3_XZLF.cn)) > -1:
            return constants.P3_XZLF

    return None
