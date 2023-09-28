import os

import cv2
import numpy as np
from cv2.typing import MatLike

from basic import os_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr import constants
from sr.constants import LabelValue
from sr.image import OcrMatcher


def get_map_path(planet: str, region: str, mt: str = 'origin') -> str:
    """
    获取某张地图路径
    :param planet: 星球名称
    :param region: 对应区域
    :param mt: 地图类型
    :return: 图片路径
    """
    return os.path.join(os_utils.get_path_under_work_dir('images', 'map', planet, region), '%s.png' % mt)


def save_large_map_image(image: MatLike, planet: str, region: str, mt: str = 'origin'):
    """
    保存某张地图
    :param image: 图片
    :param planet: 星球名称
    :param region: 对应区域
    :param mt: 地图类型
    :return:
    """
    path = get_map_path(planet, region, mt)
    cv2.imwrite(path, image)


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


def cut_minus_or_plus(screen: MatLike, minus: bool = True) -> MatLike:
    """
    从大地图下方把减号/加号裁剪出来
    :param screen: 大地图截图
    :param minus: 是否要减号
    :return: 减号/加号图片 掩码图
    """
    op_part = screen[960: 1010, 600: 650] if minus else screen[960: 1010, 970: 1020]
    gray = cv2.cvtColor(op_part, cv2.COLOR_BGR2GRAY)
    _, bw = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    # 做一个连通性检测 将黑色噪点消除
    bw = cv2_utils.connection_erase(bw, erase_white=False)
    cv2_utils.show_image(bw, win_name='bw')
    circles = cv2.HoughCircles(bw, cv2.HOUGH_GRADIENT, 1, 20, param1=0.7, param2=0.7, maxRadius=15)
    # 如果找到了圆
    tx, ty, tr = 0, 0, 0
    if circles is not None:
        circles = np.uint8(np.around(circles))

        # 保留半径最大的圆
        for circle in circles[0, :]:
            if circle[2] > tr:
                tx, ty, tr = circle[0], circle[1], circle[2]

    show_circle = op_part.copy()
    cv2.circle(show_circle, (tx, ty), tr, (255, 0, 0), 2)

    ml = (tr + 5) * 2
    mask = np.zeros((ml, ml), dtype=np.uint8)
    cv2.circle(mask, (ml // 2, ml // 2), tr + 1, 255, -1)

    cv2_utils.show_image(show_circle, win_name='op_part')
    cv2_utils.show_image(mask, win_name='mask')
    cut = op_part[ty-tr-5:ty+tr+5, tx-tr-5:tx+tr+5]
    cut = cv2.bitwise_and(cut, cut, mask=mask)
    cv2_utils.show_image(cut, win_name='cut')
    return cut, mask