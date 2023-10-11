import os
from typing import List

import cv2
import numpy as np
from cv2.typing import MatLike

from basic import os_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr import constants
from sr.constants.map import Planet, Region
from sr.image import OcrMatcher, TemplateImage, ImageMatcher
from sr.image.sceenshot import LargeMapInfo


REGION_LIST_PART = (1480, 200, 1700, 1000)
REGION_LIST_PART_CENTER = ((REGION_LIST_PART[0] + REGION_LIST_PART[2]) // 2, (REGION_LIST_PART[1] + REGION_LIST_PART[3]) // 2)
LEVEL_LIST_PART = (30, 730, 100, 1000)


def get_planet(screen: MatLike, ocr: OcrMatcher) -> Planet:
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
        if word.find(gt(constants.map.P01_KZJ.cn)) > -1:
            return constants.map.P01_KZJ
        if word.find(gt(constants.map.P02_YYL.cn)) > -1:
            return constants.map.P02_YYL
        if word.find(gt(constants.map.P03_XZLF.cn)) > -1:
            return constants.map.P03_XZLF

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


def get_sp_mask_by_template_match(lm_info: LargeMapInfo, im: ImageMatcher,
                                  template_type: str = 'origin',
                                  template_list: List = None,
                                  show: bool = False):
    """
    在地图中 圈出传送点、商铺点等可点击交互的的特殊点
    使用模板匹配
    :param lm_info: 大地图
    :param im: 图片匹配器
    :param template_type: 模板类型
    :param template_list: 限定种类的特殊点
    :param show: 是否展示结果
    :return: 特殊点组成的掩码图 特殊点是白色255、特殊点的匹配结果
    """
    sp_match_result = {}
    source = lm_info.origin if template_type == 'origin' else lm_info.gray
    sp_mask = np.zeros(source.shape[:2], dtype=np.uint8)
    # 找出特殊点位置
    for prefix in ['mm_tp', 'mm_sp']:
        for i in range(100):
            if i == 0:
                continue
            template_id = '%s_%02d' % (prefix, i)
            if template_list is not None and template_id not in template_list:
                continue
            ti: TemplateImage = im.get_template(template_id)
            if ti is None:
                break
            template = ti.get(template_type)
            template_mask = ti.mask

            match_result = im.match_image(
                source, template, mask=template_mask,
                threshold=constants.THRESHOLD_SP_TEMPLATE_IN_LARGE_MAP,
                ignore_inf=True)

            if len(match_result) > 0:
                sp_match_result[template_id] = match_result
            for r in match_result:
                sp_mask[r.y:r.y+r.h, r.x:r.x+r.w] = cv2.bitwise_or(sp_mask[r.y:r.y+r.h, r.x:r.x+r.w], template_mask)

            if show:
                cv2_utils.show_image(source, win_name='source_%s' % template_id)
                cv2_utils.show_image(template, win_name='template_%s' % template)
                cv2_utils.show_image(source, match_result, win_name='all_match_%s' % template_id)
                cv2.waitKey(0)
                cv2.destroyAllWindows()

    return sp_mask, sp_match_result


def get_map_path(region: Region, mt: str = 'origin') -> str:
    """
    获取某张地图路径
    :param region: 对应区域
    :param mt: 地图类型
    :return: 图片路径
    """
    return os.path.join(os_utils.get_path_under_work_dir('images', 'map', region.planet.id, region.get_rl_id()), '%s.png' % mt)


def save_large_map_image(image: MatLike, region: Region, mt: str = 'origin'):
    """
    保存某张地图
    :param image: 图片
    :param region: 区域
    :param mt: 地图类型
    :return:
    """
    path = get_map_path(region, mt)
    cv2.imwrite(path, image)


def get_active_region_name(screen: MatLike, ocr: OcrMatcher) -> str:
    """
    在大地图界面 获取右边列表当前选择的区域 白色字体
    :param screen: 大地图界面截图
    :param ocr: ocr
    :return: 当前选择区域
    """
    lower = 240
    upper = 255
    part = cv2_utils.crop_image(screen, REGION_LIST_PART)
    bw = cv2.inRange(part, (lower, lower, lower), (upper, upper, upper))
    km = ocr.run_ocr(bw)
    if len(km) > 0:
        return km.popitem()[0]
    else:
        return None


def get_active_level(screen: MatLike, ocr: OcrMatcher) -> str:
    """
    在大地图界面 获取左下方当前选择的层数 黑色字体
    :param screen: 大地图界面截图
    :param ocr: ocr
    :return: 当前选择区域
    """
    lower = 40
    upper = 80
    part = cv2_utils.crop_image(screen, LEVEL_LIST_PART)
    bw = cv2.inRange(part, (lower, lower, lower), (upper, upper, upper))
    km = ocr.run_ocr(bw)
    if len(km) > 0:
        return km.popitem()[0]
    else:
        return None
