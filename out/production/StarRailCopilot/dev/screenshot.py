import time
from typing import List

import cv2
import numpy as np
import pyautogui

import dev
import sr
from basic import gui_utils
from basic.img import cv2_utils
from basic.img.cv2_matcher import CvImageMatcher
from sr import constants
from sr.config import ConfigHolder
from sr.map_cal import MapCalculator


def screenshot_game(no_uid: bool = True, save_result: bool = True, show_result: bool = False):
    """
    对游戏窗口进行截图
    :param no_uid: 是否屏幕uid部分
    :param save_result: 是否显示结果
    :param show_result: 是否显示截图
    :return:
    """
    win = gui_utils.get_win_by_name('崩坏：星穹铁道', active=True)
    # 移开鼠标
    pyautogui.moveTo(1, 1)
    img = gui_utils.screenshot_win(win)
    if no_uid:
        img = cv2_utils.mark_area_as_transparent(img, [0, 1080, 200, 100])
    if show_result:
        cv2_utils.show_image(img)
    if save_result:
        dev.save_debug_image(img)
    return img


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
                dev.save_debug_image(map_part)
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
        dev.save_debug_image(merge)


def cut_icon_from_black_bg(icon: cv2.typing.MatLike, special_parts: List = []):
    """
    图标二值化后扣图
    :param icon:
    :param special_parts:
    :return:
    """
    # 二值化
    mask = cv2_utils.binary_with_white_alpha(icon)
    # 变成透明
    result = cv2.bitwise_and(icon, icon, mask=mask)
    # 特殊处理
    for i in special_parts:
        result = cv2_utils.mark_area_as_transparent(result, i)
    return result


def convert_debug_transport(name: str, special_parts: List = [], save: bool = True):
    t = dev.get_debug_image(name)
    t2 = cut_icon_from_black_bg(t, special_parts=special_parts)
    if save:
        dev.save_debug_image(t2)
    cv2_utils.show_image(t2, wait=0)


def convert_origin_map(planet: str, region: str, save: bool = True) -> cv2.typing.MatLike:
    """
    将大地图转化成黑白图，黑色为可以走的部分
    再将使用黑白图从原图中扣出细化的地图，用作后续匹配
    :param planet: 星球名称
    :param region: 对应区域
    :param save: 是否保存
    :return:
    """
    im = CvImageMatcher()
    ch = ConfigHolder()
    mc = MapCalculator(im=im, config=ch)
    map = sr.read_map_image(planet, region)
    bw, usage, _ = mc.auto_cut_map(map, show=True)
    if save:
        sr.save_map_image(bw, planet, region, 'bw')
        sr.save_map_image(usage, planet, region, 'usage')
    return bw


if __name__ == '__main__':
    convert_origin_map(constants.PLANET_1_KZJ, constants.REGION_2_JZCD, save=True)
    cv2.waitKey(0)