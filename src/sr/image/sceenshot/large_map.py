import time

import cv2
import pyautogui
from cv2.typing import MatLike

from basic import gui_utils
from basic.img import cv2_utils
from basic.img.get import save_debug_image
from sr import constants, save_map_image
from sr.config import ConfigHolder
from sr.image import OcrMatcher
from sr.image.cv2_matcher import CvImageMatcher
from sr.image.image_holder import ImageHolder
from sr.map_cal import MapCalculator


def screenshot_map_vertically(save_each: bool = False, save_merge: bool = True, show_merge: bool = False):
    """
    使用垂直滚动的方式对大地图进行截图，并进行垂直方向的拼接。
    结果图使用美图秀秀自动扣图和裁剪即可。
    :param save_each: 是否保存中间截图结果
    :param save_merge: 是否保存最终拼接结果
    :param show_merge: 是否显示最终拼接结果
    :return: 完整的大地图
    """
    win = gui_utils.get_win_by_name('崩坏：星穹铁道', active=True)
    # 先拉取到最上方
    gui_utils.scroll_with_mouse_press([win.topleft.x + 1300, win.topleft.y + 500], down_distance=-1000, duration=1)
    time.sleep(1)
    img = []
    # 每秒往下滚动一次截图
    for i in range(10):
        no_uid = screenshot_game(no_uid=False, save_result=False)
        map_part = no_uid[250: 900, 200: 1400]
        if len(img) == 0 or not cv2_utils.is_same_image(img[len(img) - 1], map_part):
            img.append(map_part)
            if save_each:
                save_debug_image(map_part)
            gui_utils.scroll_with_mouse_press([win.topleft.x + 1300, win.topleft.y + 500], down_distance=300)
            time.sleep(1)
        else:
            break

    merge = img[0]
    for i in range(len(img)):
        if i == 0:
            merge = img[i]
        else:
            merge = cv2_utils.concat_vertically(merge, img[i])

    if show_merge:
        cv2_utils.show_image(merge)

    if save_merge:
        save_debug_image(merge)


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
    lm = mc.analyse_large_map(large_map)
    cv2_utils.show_image(lm.gray, win_name='gray')
    cv2_utils.show_image(lm.mask, win_name='mask')
    if save:
        save_map_image(lm.gray, planet, region, 'gray')
        save_map_image(lm.mask, planet, region, 'mask')
    cv2.waitKey(0)


def get_planet_name(screen: MatLike, ocr: OcrMatcher) -> str:
    """
    从屏幕左上方 获取当前星球的名字
    :param screen: 屏幕截图
    :param ocr: ocr
    :return: 星球名称
    """
    return constants.PLANET_1_KZJ